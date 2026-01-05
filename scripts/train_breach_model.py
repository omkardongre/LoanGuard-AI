"""
ML Model Training Pipeline for Covenant Breach Prediction

Creates a LightGBM model with SHAP explanations for predicting
covenant breaches. This is a production-level implementation.

Usage:
    python scripts/train_breach_model.py --generate-sample-data
    python scripts/train_breach_model.py --train
"""

import os
import sys
import json
import pickle
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Feature definitions for breach prediction
FEATURE_COLUMNS = [
    "debt_to_ebitda_ratio",
    "interest_coverage_ratio",
    "current_ratio",
    "quick_ratio",
    "revenue_growth_yoy",
    "ebitda_margin",
    "debt_growth_yoy",
    "days_to_maturity",
    "previous_breaches",
    "industry_risk_score",
]

CATEGORICAL_FEATURES = []  # All numeric for this model

TARGET_COLUMN = "breach_90d"


def generate_synthetic_training_data(n_samples: int = 5000) -> pd.DataFrame:
    """
    Generate synthetic training data for breach prediction.
    
    Uses domain knowledge to create realistic covenant breach scenarios.
    """
    logger.info(f"Generating {n_samples} synthetic training samples...")
    
    np.random.seed(42)
    
    data = {
        # Debt/EBITDA ratio (typically 2-8x for leveraged loans)
        "debt_to_ebitda_ratio": np.clip(
            np.random.lognormal(mean=1.2, sigma=0.5, size=n_samples),
            1, 10
        ),
        
        # Interest coverage ratio (typically 1.5-5x)
        "interest_coverage_ratio": np.clip(
            np.random.lognormal(mean=1.0, sigma=0.6, size=n_samples),
            0.5, 10
        ),
        
        # Current ratio (typically 1-3x)
        "current_ratio": np.clip(
            np.random.normal(1.5, 0.5, size=n_samples),
            0.5, 4
        ),
        
        # Quick ratio (typically 0.5-2x)
        "quick_ratio": np.clip(
            np.random.normal(1.0, 0.4, size=n_samples),
            0.2, 3
        ),
        
        # Revenue growth YoY (-20% to +40%)
        "revenue_growth_yoy": np.clip(
            np.random.normal(0.05, 0.15, size=n_samples),
            -0.3, 0.5
        ),
        
        # EBITDA margin (5% to 30%)
        "ebitda_margin": np.clip(
            np.random.normal(0.15, 0.07, size=n_samples),
            0.02, 0.4
        ),
        
        # Debt growth YoY (-10% to +30%)
        "debt_growth_yoy": np.clip(
            np.random.normal(0.05, 0.12, size=n_samples),
            -0.2, 0.5
        ),
        
        # Days to maturity (30 to 1800)
        "days_to_maturity": np.random.randint(30, 1800, size=n_samples),
        
        # Previous breaches (0-5)
        "previous_breaches": np.random.choice(
            [0, 0, 0, 0, 1, 1, 2, 3], size=n_samples
        ),
        
        # Industry risk score (1-10, higher = riskier)
        "industry_risk_score": np.random.choice(
            range(1, 11), size=n_samples
        ),
    }
    
    df = pd.DataFrame(data)
    
    # Generate target based on realistic breach criteria
    breach_probability = (
        # High debt/EBITDA strongly predicts breach
        (df["debt_to_ebitda_ratio"] > 4).astype(float) * 0.25 +
        (df["debt_to_ebitda_ratio"] > 5).astype(float) * 0.15 +
        
        # Low interest coverage is critical
        (df["interest_coverage_ratio"] < 1.5).astype(float) * 0.20 +
        (df["interest_coverage_ratio"] < 2.0).astype(float) * 0.08 +
        
        # Poor EBITDA margin
        (df["ebitda_margin"] < 0.08).astype(float) * 0.10 +
        
        # Negative revenue growth
        (df["revenue_growth_yoy"] < 0).astype(float) * 0.08 +
        (df["revenue_growth_yoy"] < -0.1).astype(float) * 0.07 +
        
        # Previous breaches
        (df["previous_breaches"] > 0).astype(float) * 0.1 +
        (df["previous_breaches"] > 1).astype(float) * 0.05 +
        
        # High industry risk
        (df["industry_risk_score"] > 7).astype(float) * 0.05 +
        
        # Base probability
        0.05
    )
    
    # Add noise and convert to binary
    breach_probability = np.clip(breach_probability + np.random.normal(0, 0.1, n_samples), 0.01, 0.99)
    df[TARGET_COLUMN] = (np.random.random(n_samples) < breach_probability).astype(int)
    
    logger.info(f"Generated data with {df[TARGET_COLUMN].sum()} breaches ({df[TARGET_COLUMN].mean():.1%})")
    
    return df


def train_model(
    df: pd.DataFrame,
    model_dir: str = "models",
    model_name: str = "breach_predictor",
) -> Tuple[Any, Any, Dict[str, Any]]:
    """
    Train a LightGBM model with SHAP explainability.
    
    Returns:
        Tuple of (model, explainer, metrics)
    """
    try:
        import lightgbm as lgb
        import shap
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import (
            roc_auc_score, precision_score, recall_score, f1_score,
            confusion_matrix, classification_report
        )
    except ImportError as e:
        logger.error(f"Required packages not installed: {e}")
        logger.error("Run: pip install lightgbm shap scikit-learn")
        raise
    
    logger.info("Preparing training data...")
    
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"Training set: {len(X_train)} samples")
    logger.info(f"Test set: {len(X_test)} samples")
    
    # LightGBM parameters optimized for breach prediction
    params = {
        "objective": "binary",
        "metric": "auc",
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "min_child_samples": 20,
        "verbose": -1,
        "seed": 42,
    }
    
    # Create datasets
    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
    
    logger.info("Training LightGBM model...")
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=200,
        valid_sets=[test_data],
        callbacks=[
            lgb.early_stopping(stopping_rounds=20),
            lgb.log_evaluation(period=50),
        ],
    )
    
    # Predictions
    y_pred_proba = model.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    # Calculate metrics
    metrics = {
        "roc_auc": roc_auc_score(y_test, y_pred_proba),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "breach_rate_train": y_train.mean(),
        "breach_rate_test": y_test.mean(),
    }
    
    logger.info(f"Model AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"Precision: {metrics['precision']:.4f}")
    logger.info(f"Recall: {metrics['recall']:.4f}")
    
    # Generate SHAP explainer
    logger.info("Creating SHAP explainer...")
    explainer = shap.TreeExplainer(model)
    
    # Calculate feature importance from SHAP
    shap_values = explainer.shap_values(X_test)
    feature_importance = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "importance": np.abs(shap_values).mean(axis=0),
    }).sort_values("importance", ascending=False)
    
    logger.info("\nFeature Importance (SHAP):")
    for _, row in feature_importance.iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.4f}")
    
    # Save model
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, f"{model_name}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved: {model_path}")
    
    # Save explainer
    explainer_path = os.path.join(model_dir, f"{model_name}_explainer.pkl")
    with open(explainer_path, "wb") as f:
        pickle.dump(explainer, f)
    logger.info(f"Explainer saved: {explainer_path}")
    
    # Save base value (expected value)
    base_value = float(explainer.expected_value)
    base_path = os.path.join(model_dir, f"{model_name}_base_value.json")
    with open(base_path, "w") as f:
        json.dump({"base_value": base_value, "base_probability": 1 / (1 + np.exp(-base_value))}, f)
    logger.info(f"Base value saved: {base_path}")
    
    # Save feature importance
    importance_path = os.path.join(model_dir, f"{model_name}_feature_importance.json")
    with open(importance_path, "w") as f:
        json.dump(feature_importance.to_dict(orient="records"), f, indent=2)
    logger.info(f"Feature importance saved: {importance_path}")
    
    # Save metrics
    metrics["trained_at"] = datetime.utcnow().isoformat()
    metrics["model_version"] = "1.0.0"
    metrics_path = os.path.join(model_dir, f"{model_name}_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved: {metrics_path}")
    
    return model, explainer, metrics


def main():
    parser = argparse.ArgumentParser(description="Train breach prediction model")
    parser.add_argument(
        "--generate-sample-data",
        action="store_true",
        help="Generate synthetic training data",
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Train the model",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="models/training_data.csv",
        help="Path to training data CSV",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="models",
        help="Directory to save model files",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=5000,
        help="Number of samples for synthetic data",
    )
    
    args = parser.parse_args()
    
    if args.generate_sample_data:
        logger.info("Generating synthetic training data...")
        df = generate_synthetic_training_data(args.n_samples)
        
        os.makedirs(os.path.dirname(args.data_path) or ".", exist_ok=True)
        df.to_csv(args.data_path, index=False)
        logger.info(f"Training data saved: {args.data_path}")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"Shape: {df.shape}")
    
    if args.train:
        if os.path.exists(args.data_path):
            logger.info(f"Loading training data from {args.data_path}")
            df = pd.read_csv(args.data_path)
        else:
            logger.info("No training data found, generating synthetic data...")
            df = generate_synthetic_training_data(args.n_samples)
        
        model, explainer, metrics = train_model(df, args.model_dir)
        
        logger.info("\n" + "=" * 50)
        logger.info("TRAINING COMPLETE")
        logger.info("=" * 50)
        logger.info(f"ROC AUC: {metrics['roc_auc']:.4f}")
        logger.info(f"F1 Score: {metrics['f1']:.4f}")
        logger.info("=" * 50)


if __name__ == "__main__":
    main()
