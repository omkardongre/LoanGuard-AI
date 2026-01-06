"""
Two-Stage LGD (Loss Given Default) Model Training Script.

Best practice approach for recovery rate prediction:
- Stage 1: LightGBM Classifier - predicts P(has_recovery)
- Stage 2: LightGBM Regressor - predicts recovery_rate given recovery exists
- Final: recovery_rate = P(has_recovery) × predicted_recovery_rate

Based on research:
- Academic papers on two-stage LGD modeling
- Kaggle best practices for Lending Club data
- Feature engineering from Gold notebook (1674 votes)
"""

import logging
import json
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score
)
import lightgbm as lgb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
MODEL_DIR = Path(__file__).parent
DATA_PATH = MODEL_DIR.parent / "data" / "accepted_2007_to_2018Q4.csv"

# Output paths
STAGE1_MODEL_PATH = MODEL_DIR / "lgd_stage1_classifier.pkl"
STAGE2_MODEL_PATH = MODEL_DIR / "lgd_stage2_regressor.pkl"
STAGE1_EXPLAINER_PATH = MODEL_DIR / "lgd_stage1_explainer.pkl"
STAGE2_EXPLAINER_PATH = MODEL_DIR / "lgd_stage2_explainer.pkl"
CONFIG_PATH = MODEL_DIR / "lgd_two_stage_config.json"
METRICS_PATH = MODEL_DIR / "lgd_two_stage_metrics.json"

# Features based on Gold notebook research + recovery-relevant additions
NUMERIC_FEATURES = [
    "loan_amnt",
    "funded_amnt", 
    "int_rate",
    "installment",
    "annual_inc",
    "dti",
    "fico_range_low",
    "fico_range_high",
    "open_acc",
    "revol_bal",
    "revol_util",
    "total_acc",
    "delinq_2yrs",
    "inq_last_6mths",
    "pub_rec",
    "mort_acc",
    "pub_rec_bankruptcies",
    "total_rec_prncp",  # Principal recovered (important for recovery!)
    "total_rec_int",    # Interest recovered
]

CATEGORICAL_FEATURES = [
    "grade",
    "home_ownership",
    "verification_status",
    "purpose",
    "term",
    "application_type",
]

# Encodings for categorical features
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
    """Load and filter Lending Club data for charged-off loans."""
    logger.info(f"Loading data from {DATA_PATH}")
    
    use_cols = (
        NUMERIC_FEATURES + 
        CATEGORICAL_FEATURES + 
        ["loan_status", "recoveries", "collection_recovery_fee"]
    )
    
    df = pd.read_csv(DATA_PATH, usecols=use_cols, low_memory=False)
    logger.info(f"Loaded {len(df):,} total loans")
    
    # Filter to charged-off loans only
    df = df[df["loan_status"] == "Charged Off"].copy()
    logger.info(f"Charged-off loans: {len(df):,}")
    
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply feature engineering based on Gold notebook best practices."""
    
    # Create target variables
    df["has_recovery"] = (df["recoveries"] > 0).astype(int)
    
    # Calculate recovery rate for loans with recovery
    exposure = df["funded_amnt"] - df["total_rec_prncp"].fillna(0)
    exposure = exposure.replace(0, 1)  # Avoid division by zero
    df["recovery_rate"] = (df["recoveries"] / exposure).clip(0, 1)
    
    # Feature engineering from Gold notebook
    # 1. FICO average
    df["fico_avg"] = (df["fico_range_low"] + df["fico_range_high"]) / 2
    
    # 2. Income-to-loan ratio
    df["income_to_loan"] = df["annual_inc"] / (df["loan_amnt"] + 1)
    
    # 3. Installment-to-income ratio
    df["inst_to_inc"] = df["installment"] / (df["annual_inc"] / 12 + 1)
    
    # 4. Credit utilization category
    df["high_revol_util"] = (df["revol_util"] > 80).astype(int)
    
    # 5. Delinquency flag
    df["has_delinq"] = (df["delinq_2yrs"] > 0).astype(int)
    
    # 6. Bankruptcy flag
    df["has_bankruptcy"] = (df["pub_rec_bankruptcies"] > 0).astype(int)
    
    logger.info(f"Recovery rate distribution:")
    logger.info(f"  Loans with recovery: {df['has_recovery'].sum():,} ({df['has_recovery'].mean():.1%})")
    logger.info(f"  Mean recovery rate (all): {df['recovery_rate'].mean():.4f}")
    logger.info(f"  Mean recovery rate (>0): {df[df['has_recovery']==1]['recovery_rate'].mean():.4f}")
    
    return df


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """Prepare feature matrix with encoding and cleaning."""
    
    # Add engineered features to feature list
    all_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [
        "fico_avg", "income_to_loan", "inst_to_inc", 
        "high_revol_util", "has_delinq", "has_bankruptcy"
    ]
    
    # Remove features not available at prediction time
    all_features = [f for f in all_features if f not in ["total_rec_prncp", "total_rec_int"]]
    
    X = df[all_features].copy()
    
    # Handle numeric features
    for col in X.columns:
        if col not in CATEGORICAL_FEATURES:
            X[col] = pd.to_numeric(X[col], errors="coerce")
            X[col] = X[col].fillna(X[col].median())
    
    # Encode categoricals
    for col in CATEGORICAL_FEATURES:
        if col in X.columns:
            X[col] = X[col].fillna("Unknown")
            X[col] = X[col].astype(str).str.strip()
            if col in ENCODINGS:
                X[col] = X[col].map(lambda x: ENCODINGS[col].get(x, 0))
    
    # Remove outliers (from Gold notebook)
    # Keep values within reasonable ranges
    if "annual_inc" in X.columns:
        X.loc[X["annual_inc"] > 250000, "annual_inc"] = 250000
    if "dti" in X.columns:
        X.loc[X["dti"] > 50, "dti"] = 50
    if "revol_bal" in X.columns:
        X.loc[X["revol_bal"] > 250000, "revol_bal"] = 250000
    
    # Clean inf/nan
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(0)
    
    return X, list(X.columns)


def train_stage1_classifier(
    X_train: pd.DataFrame, 
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Tuple[lgb.LGBMClassifier, Dict]:
    """Train Stage 1: Classification (has_recovery or not)."""
    
    logger.info("=" * 60)
    logger.info("STAGE 1: Training Recovery Classification Model")
    logger.info("=" * 60)
    
    # Handle class imbalance
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    model = lgb.LGBMClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=8,
        num_leaves=31,
        min_child_samples=100,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )
    
    # Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    y_prob_test = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        "train_accuracy": float(accuracy_score(y_train, y_pred_train)),
        "test_accuracy": float(accuracy_score(y_test, y_pred_test)),
        "test_auc": float(roc_auc_score(y_test, y_prob_test)),
        "test_precision": float(precision_score(y_test, y_pred_test)),
        "test_recall": float(recall_score(y_test, y_pred_test)),
        "test_f1": float(f1_score(y_test, y_pred_test)),
        "positive_class_rate": float(y_test.mean()),
    }
    
    logger.info(f"Stage 1 Performance:")
    logger.info(f"  Test Accuracy: {metrics['test_accuracy']:.4f}")
    logger.info(f"  Test AUC: {metrics['test_auc']:.4f}")
    logger.info(f"  Test F1: {metrics['test_f1']:.4f}")
    
    return model, metrics


def train_stage2_regressor(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Tuple[lgb.LGBMRegressor, Dict]:
    """Train Stage 2: Regression (recovery rate for loans with recovery)."""
    
    logger.info("=" * 60)
    logger.info("STAGE 2: Training Recovery Rate Regression Model")
    logger.info("=" * 60)
    
    model = lgb.LGBMRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=8,
        num_leaves=31,
        min_child_samples=50,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )
    
    # Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    metrics = {
        "train_r2": float(r2_score(y_train, y_pred_train)),
        "test_r2": float(r2_score(y_test, y_pred_test)),
        "train_mae": float(mean_absolute_error(y_train, y_pred_train)),
        "test_mae": float(mean_absolute_error(y_test, y_pred_test)),
        "train_rmse": float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
        "test_rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
        "mean_actual": float(y_test.mean()),
        "n_samples": len(y_train),
    }
    
    logger.info(f"Stage 2 Performance:")
    logger.info(f"  Test R²: {metrics['test_r2']:.4f}")
    logger.info(f"  Test MAE: {metrics['test_mae']:.4f}")
    logger.info(f"  Test RMSE: {metrics['test_rmse']:.4f}")
    
    return model, metrics


def create_shap_explainers(stage1_model, stage2_model, X_sample: pd.DataFrame):
    """Create SHAP explainers for both stages."""
    try:
        import shap
        
        sample_size = min(1000, len(X_sample))
        X_shap = X_sample.sample(n=sample_size, random_state=42)
        
        stage1_explainer = shap.TreeExplainer(stage1_model)
        stage2_explainer = shap.TreeExplainer(stage2_model)
        
        logger.info("Created SHAP explainers for both stages")
        
        return stage1_explainer, stage2_explainer
        
    except ImportError:
        logger.warning("SHAP not installed, skipping explainer creation")
        return None, None


def save_artifacts(
    stage1_model,
    stage2_model,
    stage1_explainer,
    stage2_explainer,
    stage1_metrics: Dict,
    stage2_metrics: Dict,
    feature_order: list,
):
    """Save all model artifacts."""
    
    # Save Stage 1 model
    with open(STAGE1_MODEL_PATH, "wb") as f:
        pickle.dump(stage1_model, f)
    logger.info(f"Saved Stage 1 model to {STAGE1_MODEL_PATH}")
    
    # Save Stage 2 model
    with open(STAGE2_MODEL_PATH, "wb") as f:
        pickle.dump(stage2_model, f)
    logger.info(f"Saved Stage 2 model to {STAGE2_MODEL_PATH}")
    
    # Save explainers
    if stage1_explainer:
        with open(STAGE1_EXPLAINER_PATH, "wb") as f:
            pickle.dump(stage1_explainer, f)
    if stage2_explainer:
        with open(STAGE2_EXPLAINER_PATH, "wb") as f:
            pickle.dump(stage2_explainer, f)
    
    # Get feature importance from both models
    stage1_importance = sorted(
        zip(feature_order, stage1_model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )
    stage2_importance = sorted(
        zip(feature_order, stage2_model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )
    
    # Save config
    config = {
        "model_type": "Two-Stage LGD",
        "stage1": {
            "type": "LightGBM Classifier",
            "target": "has_recovery",
            "description": "Predicts P(recovery > 0)",
        },
        "stage2": {
            "type": "LightGBM Regressor", 
            "target": "recovery_rate",
            "description": "Predicts recovery_rate given recovery exists",
        },
        "formula": "Final LGD = 1 - (P(has_recovery) × predicted_recovery_rate)",
        "feature_order": feature_order,
        "encodings": ENCODINGS,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "stage1_feature_importance": [
            {"feature": f, "importance": int(i)} for f, i in stage1_importance[:15]
        ],
        "stage2_feature_importance": [
            {"feature": f, "importance": int(i)} for f, i in stage2_importance[:15]
        ],
    }
    
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    logger.info(f"Saved config to {CONFIG_PATH}")
    
    # Save metrics
    metrics = {
        "stage1_classifier": stage1_metrics,
        "stage2_regressor": stage2_metrics,
        "model_architecture": "Two-Stage LGD",
        "data_source": "Lending Club 2007-2018 Charged Off Loans",
    }
    
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {METRICS_PATH}")


def main():
    """Main training pipeline for Two-Stage LGD model."""
    logger.info("=" * 60)
    logger.info("Two-Stage LGD Model Training")
    logger.info("=" * 60)
    
    # Load and prepare data
    df = load_data()
    df = engineer_features(df)
    X, feature_order = prepare_features(df)
    
    # Target variables
    y_has_recovery = df["has_recovery"]
    y_recovery_rate = df["recovery_rate"]
    
    # Split data
    X_train, X_test, y1_train, y1_test, y2_train, y2_test = train_test_split(
        X, y_has_recovery, y_recovery_rate, 
        test_size=0.2, random_state=42
    )
    
    logger.info(f"Data split: Train={len(X_train):,}, Test={len(X_test):,}")
    
    # ==========================================
    # STAGE 1: Classification
    # ==========================================
    stage1_model, stage1_metrics = train_stage1_classifier(
        X_train, y1_train, X_test, y1_test
    )
    
    # ==========================================
    # STAGE 2: Regression (only on loans with recovery)
    # ==========================================
    # Filter to loans with recovery for Stage 2
    train_mask = y1_train == 1
    test_mask = y1_test == 1
    
    X_train_s2 = X_train[train_mask]
    y2_train_s2 = y2_train[train_mask]
    X_test_s2 = X_test[test_mask]
    y2_test_s2 = y2_test[test_mask]
    
    logger.info(f"Stage 2 data: Train={len(X_train_s2):,}, Test={len(X_test_s2):,}")
    
    stage2_model, stage2_metrics = train_stage2_regressor(
        X_train_s2, y2_train_s2, X_test_s2, y2_test_s2
    )
    
    # ==========================================
    # Combined Evaluation
    # ==========================================
    logger.info("=" * 60)
    logger.info("COMBINED MODEL EVALUATION")
    logger.info("=" * 60)
    
    # Predict on full test set
    p_has_recovery = stage1_model.predict_proba(X_test)[:, 1]
    pred_recovery = stage2_model.predict(X_test)
    pred_recovery = np.clip(pred_recovery, 0, 1)
    
    # Final prediction: P(has_recovery) × recovery_rate
    final_pred = p_has_recovery * pred_recovery
    actual_recovery = y2_test.values
    
    combined_mae = mean_absolute_error(actual_recovery, final_pred)
    combined_rmse = np.sqrt(mean_squared_error(actual_recovery, final_pred))
    
    logger.info(f"Combined Model Performance:")
    logger.info(f"  MAE: {combined_mae:.4f}")
    logger.info(f"  RMSE: {combined_rmse:.4f}")
    
    # Add combined metrics
    stage2_metrics["combined_mae"] = float(combined_mae)
    stage2_metrics["combined_rmse"] = float(combined_rmse)
    
    # Create SHAP explainers
    stage1_explainer, stage2_explainer = create_shap_explainers(
        stage1_model, stage2_model, X_test
    )
    
    # Save all artifacts
    save_artifacts(
        stage1_model, stage2_model,
        stage1_explainer, stage2_explainer,
        stage1_metrics, stage2_metrics,
        feature_order,
    )
    
    logger.info("=" * 60)
    logger.info("Training Complete!")
    logger.info(f"Stage 1 AUC: {stage1_metrics['test_auc']:.4f}")
    logger.info(f"Stage 2 MAE: {stage2_metrics['test_mae']:.4f}")
    logger.info(f"Combined MAE: {combined_mae:.4f}")
    logger.info("=" * 60)
    
    return {
        "stage1": stage1_metrics,
        "stage2": stage2_metrics,
    }


if __name__ == "__main__":
    main()
