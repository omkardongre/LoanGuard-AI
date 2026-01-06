"""
IMPROVED Two-Stage LGD Model - V2 Training Script.

Improvements based on research:
1. More features: mths_since_last_delinq, last_fico, chargeoff_within_12m
2. Strict outlier removal (from Gold Kaggle notebook)
3. XGBoost + LightGBM ensemble for Stage 1
4. MinMaxScaler normalization  
5. Better hyperparameter tuning
6. Feature importance analysis
"""

import logging
import json
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score
)
import lightgbm as lgb
from xgboost import XGBClassifier, XGBRegressor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent
DATA_PATH = MODEL_DIR.parent / "data" / "accepted_2007_to_2018Q4.csv"

# Output paths - V2
STAGE1_MODEL_PATH = MODEL_DIR / "lgd_stage1_classifier_v2.pkl"
STAGE2_MODEL_PATH = MODEL_DIR / "lgd_stage2_regressor_v2.pkl"
STAGE1_EXPLAINER_PATH = MODEL_DIR / "lgd_stage1_explainer_v2.pkl"
STAGE2_EXPLAINER_PATH = MODEL_DIR / "lgd_stage2_explainer_v2.pkl"
SCALER_PATH = MODEL_DIR / "lgd_scaler_v2.pkl"
CONFIG_PATH = MODEL_DIR / "lgd_two_stage_config_v2.json"
METRICS_PATH = MODEL_DIR / "lgd_two_stage_metrics_v2.json"

# EXPANDED FEATURES based on research
NUMERIC_FEATURES = [
    # Original core features
    "loan_amnt", "funded_amnt", "int_rate", "installment", "annual_inc", "dti",
    "fico_range_low", "fico_range_high", "open_acc", "revol_bal", "revol_util", "total_acc",
    "delinq_2yrs", "inq_last_6mths", "pub_rec", "mort_acc", "pub_rec_bankruptcies",
    
    # NEW: Time-based features (key for recovery prediction per research)
    "mths_since_last_delinq",
    "mths_since_last_record", 
    "mths_since_last_major_derog",
    
    # NEW: Updated FICO (important - shows trajectory)
    "last_fico_range_high",
    "last_fico_range_low",
    
    # NEW: Recent credit behavior
    "acc_open_past_24mths",
    "chargeoff_within_12_mths",
    "collections_12_mths_ex_med",
    
    # NEW: Recent inquiry activity
    "inq_last_12m",
    "mths_since_recent_inq",
]

CATEGORICAL_FEATURES = [
    "grade", "home_ownership", "verification_status", "purpose", "term", "application_type",
]

ENCODINGS = {
    "grade": {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6},
    "home_ownership": {"ANY": 0, "MORTGAGE": 1, "NONE": 2, "OTHER": 3, "OWN": 4, "RENT": 5},
    "verification_status": {"Not Verified": 0, "Source Verified": 1, "Verified": 2},
    "purpose": {
        "car": 0, "credit_card": 1, "debt_consolidation": 2, "educational": 3,
        "home_improvement": 4, "house": 5, "major_purchase": 6, "medical": 7,
        "moving": 8, "other": 9, "renewable_energy": 10, "small_business": 11,
        "vacation": 12, "wedding": 13
    },
    "term": {" 36 months": 0, " 60 months": 1, "36 months": 0, "60 months": 1},
    "application_type": {"Individual": 0, "Joint App": 1, "INDIVIDUAL": 0, "JOINT": 1},
}


def load_data() -> pd.DataFrame:
    """Load Lending Club data."""
    logger.info(f"Loading data from {DATA_PATH}")
    
    use_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [
        "loan_status", "recoveries", "collection_recovery_fee"
    ]
    
    df = pd.read_csv(DATA_PATH, usecols=use_cols, low_memory=False)
    logger.info(f"Loaded {len(df):,} total loans")
    
    df = df[df["loan_status"] == "Charged Off"].copy()
    logger.info(f"Charged-off loans: {len(df):,}")
    
    return df


def apply_outlier_removal(df: pd.DataFrame) -> pd.DataFrame:
    """Apply strict outlier removal from Gold Kaggle notebook."""
    original_len = len(df)
    
    # From Gold notebook - proven thresholds
    df = df[df["annual_inc"] <= 250000]
    df = df[df["dti"] <= 50]
    df = df[df["open_acc"] <= 40]
    df = df[df["total_acc"] <= 80]
    df = df[df["revol_util"] <= 120]
    df = df[df["revol_bal"] <= 250000]
    
    logger.info(f"Outlier removal: {original_len:,} -> {len(df):,} ({len(df)/original_len:.1%} kept)")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Enhanced feature engineering."""
    
    # Target variables
    df["has_recovery"] = (df["recoveries"] > 0).astype(int)
    exposure = df["funded_amnt"].clip(lower=1)
    df["recovery_rate"] = (df["recoveries"] / exposure).clip(0, 1)
    
    # Engineered features
    df["fico_avg"] = (df["fico_range_low"] + df["fico_range_high"]) / 2
    df["last_fico_avg"] = (df["last_fico_range_low"].fillna(df["fico_range_low"]) + 
                           df["last_fico_range_high"].fillna(df["fico_range_high"])) / 2
    
    # FICO trajectory (key insight - improving vs declining credit)
    df["fico_change"] = df["last_fico_avg"] - df["fico_avg"]
    
    # Income ratios
    df["income_to_loan"] = df["annual_inc"] / (df["loan_amnt"] + 1)
    df["inst_to_inc"] = df["installment"] / (df["annual_inc"] / 12 + 1)
    
    # Risk flags
    df["high_dti"] = (df["dti"] > 30).astype(int)
    df["high_revol_util"] = (df["revol_util"] > 80).astype(int)
    df["has_delinq"] = (df["delinq_2yrs"] > 0).astype(int)
    df["has_bankruptcy"] = (df["pub_rec_bankruptcies"] > 0).astype(int)
    df["recent_chargeoff"] = (df["chargeoff_within_12_mths"] > 0).astype(int)
    df["recent_collections"] = (df["collections_12_mths_ex_med"] > 0).astype(int)
    
    # Credit age proxy
    df["mths_since_delinq_filled"] = df["mths_since_last_delinq"].fillna(999)
    df["mths_since_record_filled"] = df["mths_since_last_record"].fillna(999)
    
    logger.info(f"Recovery distribution: {df['has_recovery'].mean():.1%} have recovery")
    logger.info(f"Mean recovery (>0): {df[df['has_recovery']==1]['recovery_rate'].mean():.4f}")
    
    return df


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """Prepare feature matrix."""
    
    engineered_features = [
        "fico_avg", "last_fico_avg", "fico_change", "income_to_loan", "inst_to_inc",
        "high_dti", "high_revol_util", "has_delinq", "has_bankruptcy",
        "recent_chargeoff", "recent_collections",
        "mths_since_delinq_filled", "mths_since_record_filled",
    ]
    
    all_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES + engineered_features
    
    # Remove features that might leak target info
    exclude = ["last_fico_range_high", "last_fico_range_low", 
               "mths_since_last_delinq", "mths_since_last_record"]
    all_features = [f for f in all_features if f in df.columns and f not in exclude]
    
    X = df[all_features].copy()
    
    # Handle numerics
    for col in X.columns:
        if col not in CATEGORICAL_FEATURES:
            X[col] = pd.to_numeric(X[col], errors="coerce")
            X[col] = X[col].fillna(X[col].median())
    
    # Encode categoricals
    for col in CATEGORICAL_FEATURES:
        if col in X.columns:
            X[col] = X[col].fillna("Unknown").astype(str).str.strip()
            if col in ENCODINGS:
                X[col] = X[col].map(lambda x: ENCODINGS[col].get(x, 0))
    
    # Clean
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
    
    return X, list(X.columns)


def train_stage1_ensemble(
    X_train: np.ndarray,
    y_train: pd.Series,
    X_test: np.ndarray,
    y_test: pd.Series,
    feature_names: list,
) -> Tuple[Any, Dict]:
    """Train Stage 1: XGBoost + LightGBM ensemble classifier."""
    
    logger.info("=" * 60)
    logger.info("STAGE 1: Training Ensemble Classifier (XGBoost + LightGBM)")
    logger.info("=" * 60)
    
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    # XGBoost
    xgb_model = XGBClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )
    xgb_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    
    # LightGBM
    lgb_model = lgb.LGBMClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=31,
        min_child_samples=50,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    lgb_model.fit(X_train, y_train, eval_set=[(X_test, y_test)],
                  callbacks=[lgb.early_stopping(50, verbose=False)])
    
    # Ensemble predictions (average)
    xgb_prob = xgb_model.predict_proba(X_test)[:, 1]
    lgb_prob = lgb_model.predict_proba(X_test)[:, 1]
    ensemble_prob = (xgb_prob + lgb_prob) / 2
    ensemble_pred = (ensemble_prob >= 0.5).astype(int)
    
    # Evaluate
    metrics = {
        "xgb_auc": float(roc_auc_score(y_test, xgb_prob)),
        "lgb_auc": float(roc_auc_score(y_test, lgb_prob)),
        "ensemble_auc": float(roc_auc_score(y_test, ensemble_prob)),
        "ensemble_accuracy": float(accuracy_score(y_test, ensemble_pred)),
        "ensemble_f1": float(f1_score(y_test, ensemble_pred)),
        "positive_rate": float(y_test.mean()),
    }
    
    logger.info(f"XGBoost AUC: {metrics['xgb_auc']:.4f}")
    logger.info(f"LightGBM AUC: {metrics['lgb_auc']:.4f}")
    logger.info(f"ENSEMBLE AUC: {metrics['ensemble_auc']:.4f}")
    
    # Store both models
    ensemble = {"xgb": xgb_model, "lgb": lgb_model}
    
    return ensemble, metrics


def train_stage2_regressor(
    X_train: np.ndarray,
    y_train: pd.Series,
    X_test: np.ndarray,
    y_test: pd.Series,
) -> Tuple[lgb.LGBMRegressor, Dict]:
    """Train Stage 2: Enhanced regression."""
    
    logger.info("=" * 60)
    logger.info("STAGE 2: Training Recovery Rate Regressor")
    logger.info("=" * 60)
    
    model = lgb.LGBMRegressor(
        n_estimators=300,
        learning_rate=0.03,
        max_depth=8,
        num_leaves=63,
        min_child_samples=30,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)],
              callbacks=[lgb.early_stopping(50, verbose=False)])
    
    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0, 1)
    
    metrics = {
        "test_r2": float(r2_score(y_test, y_pred)),
        "test_mae": float(mean_absolute_error(y_test, y_pred)),
        "test_rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "mean_actual": float(y_test.mean()),
        "mean_predicted": float(y_pred.mean()),
    }
    
    logger.info(f"R²: {metrics['test_r2']:.4f}")
    logger.info(f"MAE: {metrics['test_mae']:.4f}")
    logger.info(f"RMSE: {metrics['test_rmse']:.4f}")
    
    return model, metrics


def save_artifacts(
    stage1_ensemble, stage2_model, scaler, 
    stage1_metrics, stage2_metrics,
    feature_order, combined_mae,
):
    """Save all artifacts."""
    
    with open(STAGE1_MODEL_PATH, "wb") as f:
        pickle.dump(stage1_ensemble, f)
    
    with open(STAGE2_MODEL_PATH, "wb") as f:
        pickle.dump(stage2_model, f)
    
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)
    
    # Create SHAP explainers
    try:
        import shap
        stage1_explainer = shap.TreeExplainer(stage1_ensemble["lgb"])
        stage2_explainer = shap.TreeExplainer(stage2_model)
        
        with open(STAGE1_EXPLAINER_PATH, "wb") as f:
            pickle.dump(stage1_explainer, f)
        with open(STAGE2_EXPLAINER_PATH, "wb") as f:
            pickle.dump(stage2_explainer, f)
    except Exception as e:
        logger.warning(f"SHAP error: {e}")
    
    # Feature importance
    lgb_importance = sorted(
        zip(feature_order, stage1_ensemble["lgb"].feature_importances_),
        key=lambda x: x[1], reverse=True
    )
    
    config = {
        "model_type": "Two-Stage LGD V2 (Ensemble)",
        "version": "2.1.0",
        "stage1": {"type": "XGBoost + LightGBM Ensemble", "target": "has_recovery"},
        "stage2": {"type": "LightGBM Regressor", "target": "recovery_rate"},
        "formula": "recovery_rate = P(has_recovery) × predicted_recovery_rate",
        "feature_order": feature_order,
        "encodings": ENCODINGS,
        "feature_importance": [{"feature": f, "importance": int(i)} for f, i in lgb_importance[:20]],
    }
    
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    
    metrics = {
        "stage1": stage1_metrics,
        "stage2": stage2_metrics,
        "combined_mae": combined_mae,
    }
    
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved all V2 artifacts")


def main():
    """Main training pipeline."""
    logger.info("=" * 60)
    logger.info("IMPROVED Two-Stage LGD Model V2 Training")
    logger.info("=" * 60)
    
    # Load and prepare data
    df = load_data()
    df = apply_outlier_removal(df)
    df = engineer_features(df)
    X, feature_order = prepare_features(df)
    
    logger.info(f"Features: {len(feature_order)}")
    
    # Targets
    y_has_recovery = df["has_recovery"]
    y_recovery_rate = df["recovery_rate"]
    
    # Split
    X_train, X_test, y1_train, y1_test, y2_train, y2_test = train_test_split(
        X, y_has_recovery, y_recovery_rate,
        test_size=0.2, random_state=42
    )
    
    # Scale features (from Gold notebook)
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    logger.info(f"Train: {len(X_train):,}, Test: {len(X_test):,}")
    
    # Stage 1: Ensemble Classifier
    stage1_ensemble, stage1_metrics = train_stage1_ensemble(
        X_train_scaled, y1_train, X_test_scaled, y1_test, feature_order
    )
    
    # Stage 2: Regressor (on loans with recovery)
    train_mask = y1_train == 1
    test_mask = y1_test == 1
    
    X_train_s2 = X_train_scaled[train_mask]
    y2_train_s2 = y2_train[train_mask]
    X_test_s2 = X_test_scaled[test_mask]
    y2_test_s2 = y2_test[test_mask]
    
    stage2_model, stage2_metrics = train_stage2_regressor(
        X_train_s2, y2_train_s2, X_test_s2, y2_test_s2
    )
    
    # Combined evaluation
    logger.info("=" * 60)
    logger.info("COMBINED EVALUATION")
    logger.info("=" * 60)
    
    xgb_prob = stage1_ensemble["xgb"].predict_proba(X_test_scaled)[:, 1]
    lgb_prob = stage1_ensemble["lgb"].predict_proba(X_test_scaled)[:, 1]
    p_recovery = (xgb_prob + lgb_prob) / 2
    
    pred_rate = stage2_model.predict(X_test_scaled)
    pred_rate = np.clip(pred_rate, 0, 1)
    
    final_pred = p_recovery * pred_rate
    actual = y2_test.values
    
    combined_mae = mean_absolute_error(actual, final_pred)
    combined_rmse = np.sqrt(mean_squared_error(actual, final_pred))
    
    logger.info(f"Combined MAE: {combined_mae:.4f}")
    logger.info(f"Combined RMSE: {combined_rmse:.4f}")
    
    # Save
    save_artifacts(
        stage1_ensemble, stage2_model, scaler,
        stage1_metrics, stage2_metrics, feature_order, float(combined_mae)
    )
    
    # Summary
    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE - V2")
    logger.info(f"Stage 1 Ensemble AUC: {stage1_metrics['ensemble_auc']:.4f}")
    logger.info(f"Stage 2 MAE: {stage2_metrics['test_mae']:.4f}")
    logger.info(f"Combined MAE: {combined_mae:.4f}")
    logger.info("=" * 60)
    
    return metrics


if __name__ == "__main__":
    main()
