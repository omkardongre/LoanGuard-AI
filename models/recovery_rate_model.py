"""
Recovery Rate / LGD Model Training Script.

Trains a LightGBM regressor to predict loan recovery rates for Basel III compliance.
Uses Lending Club charged-off loan data to learn patterns of post-default recoveries.

LGD (Loss Given Default) = 1 - Recovery Rate
"""

import logging
import json
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import lightgbm as lgb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
MODEL_DIR = Path(__file__).parent
DATA_PATH = MODEL_DIR.parent / "data" / "accepted_2007_to_2018Q4.csv"

# Output paths
MODEL_PATH = MODEL_DIR / "recovery_rate_predictor.pkl"
EXPLAINER_PATH = MODEL_DIR / "recovery_rate_explainer.pkl"
CONFIG_PATH = MODEL_DIR / "recovery_rate_config.json"
METRICS_PATH = MODEL_DIR / "recovery_rate_metrics.json"
IMPORTANCE_PATH = MODEL_DIR / "recovery_rate_feature_importance.json"

# Features for recovery rate prediction
NUMERIC_FEATURES = [
    "loan_amnt",
    "funded_amnt",
    "int_rate",
    "installment",
    "annual_inc",
    "dti",
    "fico_range_low",
    "open_acc",
    "revol_bal",
    "revol_util",
    "total_acc",
    "delinq_2yrs",
    "inq_last_6mths",
    "pub_rec",
    "mort_acc",
]

CATEGORICAL_FEATURES = [
    "grade",
    "home_ownership",
    "verification_status",
    "purpose",
    "term",
]

# Encoding maps (same as breach predictor for consistency)
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
    "term": {" 36 months": 0, " 60 months": 1, "36 months": 0, "60 months": 1}
}


def load_and_prepare_data() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load Lending Club data and prepare for recovery rate modeling.
    
    Returns:
        Tuple of (features DataFrame, target Series)
    """
    logger.info(f"Loading data from {DATA_PATH}")
    
    # Load only needed columns to save memory
    use_cols = (
        NUMERIC_FEATURES + 
        CATEGORICAL_FEATURES + 
        ["loan_status", "recoveries", "total_rec_prncp"]
    )
    
    df = pd.read_csv(DATA_PATH, usecols=use_cols, low_memory=False)
    logger.info(f"Loaded {len(df):,} total loans")
    
    # Filter to charged-off loans only
    df = df[df["loan_status"] == "Charged Off"].copy()
    logger.info(f"Charged-off loans: {len(df):,}")
    
    # Filter to loans with some recovery (non-zero)
    # This gives us meaningful recovery patterns to learn
    df = df[df["recoveries"] > 0].copy()
    logger.info(f"Loans with recoveries: {len(df):,}")
    
    # Calculate recovery rate (target variable)
    # Recovery rate = recoveries / (funded_amnt - recovered_principal)
    # Clamped to [0, 1] range
    exposure = df["funded_amnt"] - df["total_rec_prncp"].fillna(0)
    exposure = exposure.replace(0, 1)  # Avoid division by zero
    
    df["recovery_rate"] = (df["recoveries"] / exposure).clip(0, 1)
    
    logger.info(f"Recovery rate stats:")
    logger.info(f"  Mean: {df['recovery_rate'].mean():.4f}")
    logger.info(f"  Median: {df['recovery_rate'].median():.4f}")
    logger.info(f"  Std: {df['recovery_rate'].std():.4f}")
    
    # Prepare features
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X = df[features].copy()
    y = df["recovery_rate"]
    
    # Handle missing values
    for col in NUMERIC_FEATURES:
        X[col] = pd.to_numeric(X[col], errors="coerce")
        X[col] = X[col].fillna(X[col].median())
    
    # Encode categoricals
    for col in CATEGORICAL_FEATURES:
        X[col] = X[col].fillna("Unknown")
        if col in ENCODINGS:
            X[col] = X[col].map(lambda x: ENCODINGS[col].get(str(x).strip(), 0))
        else:
            X[col] = 0
    
    # Remove any remaining NaN/inf
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(0)
    
    logger.info(f"Prepared {len(X):,} samples with {len(features)} features")
    
    return X, y


def train_model(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Train LightGBM regressor for recovery rate prediction.
    
    Args:
        X: Feature DataFrame
        y: Target Series (recovery_rate)
        
    Returns:
        Dict with model, metrics, and feature importance
    """
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info(f"Train: {len(X_train):,}, Test: {len(X_test):,}")
    
    # Train LightGBM
    model = lgb.LGBMRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=8,
        num_leaves=31,
        min_child_samples=100,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    
    # Fit with early stopping
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
        "n_train_samples": len(X_train),
        "n_test_samples": len(X_test),
        "n_features": len(X.columns),
        "best_iteration": model.best_iteration_,
    }
    
    logger.info(f"Model Performance:")
    logger.info(f"  Train R²: {metrics['train_r2']:.4f}")
    logger.info(f"  Test R²: {metrics['test_r2']:.4f}")
    logger.info(f"  Test MAE: {metrics['test_mae']:.4f}")
    logger.info(f"  Test RMSE: {metrics['test_rmse']:.4f}")
    
    # Feature importance
    importance = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)
    
    logger.info(f"\nTop 10 Features:")
    for _, row in importance.head(10).iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.0f}")
    
    return {
        "model": model,
        "metrics": metrics,
        "importance": importance.to_dict("records"),
        "X_test": X_test,
        "y_test": y_test,
    }


def create_shap_explainer(model, X_sample: pd.DataFrame):
    """Create SHAP explainer for model interpretability."""
    try:
        import shap
        
        # Use smaller sample for explainer
        sample_size = min(1000, len(X_sample))
        X_shap = X_sample.sample(n=sample_size, random_state=42)
        
        explainer = shap.TreeExplainer(model)
        logger.info("Created SHAP TreeExplainer")
        
        # Get base value
        base_value = float(explainer.expected_value)
        
        return explainer, base_value
        
    except ImportError:
        logger.warning("SHAP not installed, skipping explainer")
        return None, None


def save_artifacts(
    model,
    explainer,
    base_value: float,
    metrics: Dict,
    importance: list,
    features: list,
):
    """Save all model artifacts."""
    
    # Save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Saved model to {MODEL_PATH}")
    
    # Save explainer
    if explainer:
        with open(EXPLAINER_PATH, "wb") as f:
            pickle.dump(explainer, f)
        logger.info(f"Saved explainer to {EXPLAINER_PATH}")
    
    # Save config
    config = {
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "feature_order": features,
        "encodings": ENCODINGS,
        "base_value": base_value,
        "model_type": "LightGBM Regressor",
        "target": "recovery_rate",
        "lgd_formula": "LGD = 1 - recovery_rate",
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    logger.info(f"Saved config to {CONFIG_PATH}")
    
    # Save metrics
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {METRICS_PATH}")
    
    # Save feature importance
    with open(IMPORTANCE_PATH, "w") as f:
        json.dump(importance, f, indent=2)
    logger.info(f"Saved feature importance to {IMPORTANCE_PATH}")


def main():
    """Main training pipeline."""
    logger.info("=" * 60)
    logger.info("Recovery Rate / LGD Model Training")
    logger.info("=" * 60)
    
    # Load data
    X, y = load_and_prepare_data()
    
    # Train model
    results = train_model(X, y)
    
    # Create SHAP explainer
    explainer, base_value = create_shap_explainer(
        results["model"], 
        results["X_test"]
    )
    
    # Save artifacts
    save_artifacts(
        model=results["model"],
        explainer=explainer,
        base_value=base_value or results["metrics"]["test_r2"],
        metrics=results["metrics"],
        importance=results["importance"],
        features=list(X.columns),
    )
    
    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info(f"Test R²: {results['metrics']['test_r2']:.4f}")
    logger.info(f"Test MAE: {results['metrics']['test_mae']:.4f}")
    logger.info("=" * 60)
    
    return results["metrics"]


if __name__ == "__main__":
    main()
