"""
Production ML Training on Real Lending Club Data

Uses 1.17M+ real loans from Lending Club dataset to train
a LightGBM model for breach/default prediction with SHAP explainability.

Based on Kaggle best practices:
- Gold notebook: Feature selection and preprocessing
- SHAP notebook: TreeExplainer, handle binary classification

Usage:
    python scripts/train_lending_club_model.py
"""

import os
import sys
import json
import pickle
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
DATA_PATH = Path(__file__).parent.parent / "data" / "accepted_2007_to_2018Q4.csv"
MODEL_DIR = Path(__file__).parent.parent / "models"

# Features based on Kaggle top notebooks
NUMERIC_FEATURES = [
    'loan_amnt',           # Loan amount
    'int_rate',            # Interest rate
    'installment',         # Monthly payment
    'annual_inc',          # Annual income
    'dti',                 # Debt-to-income ratio
    'fico_range_low',      # FICO score (lower bound)
    'open_acc',            # Number of open accounts
    'revol_bal',           # Revolving balance
    'revol_util',          # Revolving utilization
    'total_acc',           # Total accounts
    'delinq_2yrs',         # Delinquencies in past 2 years
    'inq_last_6mths',      # Inquiries in last 6 months
    'pub_rec',             # Public records
    'mort_acc',            # Mortgage accounts
]

CATEGORICAL_FEATURES = [
    'grade',               # Loan grade (A-G)
    'home_ownership',      # Home ownership status
    'verification_status', # Income verification
    'purpose',             # Loan purpose
    'term',                # Loan term
]

# Target: Charged Off = Default (breach in our context)
DEFAULT_STATUSES = ['Charged Off', 'Default']
GOOD_STATUSES = ['Fully Paid']


def load_and_preprocess_data(sample_size: Optional[int] = None) -> pd.DataFrame:
    """
    Load and preprocess Lending Club data.
    
    Args:
        sample_size: Optional sample size for faster testing
        
    Returns:
        Preprocessed DataFrame
    """
    logger.info(f"Loading data from {DATA_PATH}")
    
    # Columns to load
    use_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES + ['loan_status']
    
    df = pd.read_csv(
        DATA_PATH,
        usecols=use_cols,
        low_memory=False,
        nrows=sample_size,
    )
    
    logger.info(f"Loaded {len(df):,} loans")
    
    # Filter to completed loans only (Charged Off or Fully Paid)
    completed_status = DEFAULT_STATUSES + GOOD_STATUSES
    df = df[df['loan_status'].isin(completed_status)]
    logger.info(f"Filtered to completed loans: {len(df):,}")
    
    # Clean interest rate (remove %)
    if df['int_rate'].dtype == object:
        df['int_rate'] = df['int_rate'].str.replace('%', '').str.strip().astype(float)
    
    # Clean revol_util (remove %)
    if 'revol_util' in df.columns and df['revol_util'].dtype == object:
        df['revol_util'] = pd.to_numeric(
            df['revol_util'].str.replace('%', '').str.strip(), 
            errors='coerce'
        )
    
    # Clean term (extract number)
    if 'term' in df.columns and df['term'].dtype == object:
        df['term'] = df['term'].str.extract(r'(\d+)').astype(float)
    
    # Create target variable
    df['is_default'] = df['loan_status'].isin(DEFAULT_STATUSES).astype(int)
    
    default_rate = df['is_default'].mean()
    logger.info(f"Default rate: {default_rate:.2%} ({df['is_default'].sum():,} defaults)")
    
    # Handle missing values for numeric features
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
    
    # Handle missing values for categorical features
    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna('Unknown').astype(str)
    
    # Remove rows with any remaining nulls in target
    df = df.dropna(subset=['is_default'])
    
    logger.info(f"Final dataset: {len(df):,} loans")
    
    return df


def encode_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Dict]]:
    """
    Encode categorical features using label encoding.
    
    Returns:
        Tuple of (encoded DataFrame, encoding mappings)
    """
    encodings = {}
    df = df.copy()
    
    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            # Convert to category and get codes
            df[col] = df[col].astype('category')
            encodings[col] = {v: i for i, v in enumerate(df[col].cat.categories)}
            df[col] = df[col].cat.codes
    
    return df, encodings


def train_model(df: pd.DataFrame) -> Tuple[Any, Any, Dict[str, Any], pd.DataFrame, List[str]]:
    """
    Train LightGBM model with SHAP explainability.
    
    Based on Kaggle SHAP notebook patterns:
    - Uses TreeExplainer for efficient SHAP computation
    - Handles binary classification output (list of arrays)
    
    Returns:
        Tuple of (model, explainer, metrics, feature_importance, feature_cols)
    """
    try:
        import lightgbm as lgb
        import shap
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import (
            roc_auc_score, precision_score, recall_score, f1_score,
            average_precision_score, confusion_matrix
        )
    except ImportError as e:
        logger.error(f"Required packages not installed: {e}")
        raise
    
    # Feature columns
    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    feature_cols = [c for c in feature_cols if c in df.columns]
    
    X = df[feature_cols]
    y = df['is_default']
    
    # Train/test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=0.2, 
        random_state=42, 
        stratify=y
    )
    
    logger.info(f"Training set: {len(X_train):,} samples ({y_train.mean():.2%} default rate)")
    logger.info(f"Test set: {len(X_test):,} samples ({y_test.mean():.2%} default rate)")
    
    # Calculate class weight for imbalanced data
    pos_weight = (len(y_train) - y_train.sum()) / max(1, y_train.sum())
    logger.info(f"Class imbalance ratio: {pos_weight:.2f}:1")
    
    # LightGBM parameters (optimized for credit risk)
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'min_child_samples': 100,
        'scale_pos_weight': pos_weight,
        'verbose': -1,
        'seed': 42,
        'n_jobs': -1,
    }
    
    # Identify categorical feature indices
    cat_feature_indices = [feature_cols.index(c) for c in CATEGORICAL_FEATURES if c in feature_cols]
    
    # Create datasets
    train_data = lgb.Dataset(
        X_train, 
        label=y_train,
        categorical_feature=cat_feature_indices if cat_feature_indices else 'auto',
        free_raw_data=False,
    )
    test_data = lgb.Dataset(
        X_test, 
        label=y_test, 
        reference=train_data,
        categorical_feature=cat_feature_indices if cat_feature_indices else 'auto',
        free_raw_data=False,
    )
    
    logger.info("Training LightGBM model...")
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=500,
        valid_sets=[train_data, test_data],
        valid_names=['train', 'valid'],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50),
            lgb.log_evaluation(period=100),
        ],
    )
    
    # Predictions
    y_pred_proba = model.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    # Calculate metrics
    cm = confusion_matrix(y_test, y_pred)
    metrics = {
        'roc_auc': roc_auc_score(y_test, y_pred_proba),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'average_precision': average_precision_score(y_test, y_pred_proba),
        'confusion_matrix': cm.tolist(),
        'train_size': len(X_train),
        'test_size': len(X_test),
        'default_rate': float(y.mean()),
        'feature_count': len(feature_cols),
        'features': feature_cols,
    }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"MODEL PERFORMANCE (REAL LENDING CLUB DATA)")
    logger.info(f"{'='*60}")
    logger.info(f"ROC AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"Average Precision: {metrics['average_precision']:.4f}")
    logger.info(f"Precision: {metrics['precision']:.4f}")
    logger.info(f"Recall: {metrics['recall']:.4f}")
    logger.info(f"F1 Score: {metrics['f1']:.4f}")
    logger.info(f"Confusion Matrix:\n{cm}")
    
    # Create SHAP explainer (following Kaggle SHAP notebook pattern)
    logger.info("\nCreating SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    
    # Calculate SHAP values on sample for feature importance
    sample_size = min(10000, len(X_test))
    sample_indices = np.random.choice(len(X_test), sample_size, replace=False)
    X_sample = X_test.iloc[sample_indices]
    
    logger.info(f"Computing SHAP values on {sample_size:,} samples...")
    shap_values = explainer.shap_values(X_sample)
    
    # Handle binary classification output (Kaggle SHAP notebook pattern)
    if isinstance(shap_values, list):
        logger.info("Binary classification detected, using positive class SHAP values")
        shap_values = shap_values[1]  # Take positive class
    
    # Calculate global feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': np.abs(shap_values).mean(axis=0),
    }).sort_values('importance', ascending=False)
    
    logger.info("\nFeature Importance (SHAP - mean |SHAP value|):")
    for _, row in feature_importance.head(10).iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.4f}")
    
    return model, explainer, metrics, feature_importance, feature_cols


def save_artifacts(
    model: Any,
    explainer: Any,
    metrics: Dict[str, Any],
    feature_importance: pd.DataFrame,
    feature_cols: List[str],
    encodings: Dict[str, Dict],
) -> None:
    """Save all model artifacts."""
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = MODEL_DIR / "breach_predictor.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved: {model_path}")
    
    # Save explainer
    explainer_path = MODEL_DIR / "breach_predictor_explainer.pkl"
    with open(explainer_path, 'wb') as f:
        pickle.dump(explainer, f)
    logger.info(f"Explainer saved: {explainer_path}")
    
    # Save base value for SHAP
    expected_value = explainer.expected_value
    if isinstance(expected_value, (list, np.ndarray)):
        base_value = float(expected_value[1]) if len(expected_value) > 1 else float(expected_value[0])
    else:
        base_value = float(expected_value)
    
    base_data = {
        'base_value': base_value,
        'base_probability': 1 / (1 + np.exp(-base_value)),
    }
    base_path = MODEL_DIR / "breach_predictor_base_value.json"
    with open(base_path, 'w') as f:
        json.dump(base_data, f, indent=2)
    logger.info(f"Base value saved: {base_path}")
    
    # Save feature importance
    importance_list = feature_importance.to_dict(orient='records')
    importance_path = MODEL_DIR / "breach_predictor_feature_importance.json"
    with open(importance_path, 'w') as f:
        json.dump(importance_list, f, indent=2)
    logger.info(f"Feature importance saved: {importance_path}")
    
    # Save training metrics
    metrics['trained_at'] = datetime.utcnow().isoformat()
    metrics['model_version'] = '2.0.0'  # V2 = Real Lending Club Data
    metrics['data_source'] = 'Lending Club (2007-2018) - 1.17M+ real loans'
    metrics['training_type'] = 'PRODUCTION'
    metrics_path = MODEL_DIR / "breach_predictor_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"Metrics saved: {metrics_path}")
    
    # Save feature config
    config = {
        'numeric_features': NUMERIC_FEATURES,
        'categorical_features': CATEGORICAL_FEATURES,
        'feature_order': feature_cols,
        'encodings': encodings,
    }
    config_path = MODEL_DIR / "breach_predictor_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Config saved: {config_path}")


def main():
    """Main training pipeline."""
    logger.info("="*70)
    logger.info("PRODUCTION ML TRAINING - REAL LENDING CLUB DATA")
    logger.info("="*70)
    
    # Check data exists
    if not DATA_PATH.exists():
        logger.error(f"Data not found: {DATA_PATH}")
        logger.error("Please download Lending Club data first:")
        logger.error("  kaggle datasets download -d wordsforthewise/lending-club -p data/")
        logger.error("  cd data && unzip lending-club.zip && gunzip *.gz")
        return False
    
    # Load and preprocess
    df = load_and_preprocess_data()
    
    # Encode features
    df, encodings = encode_features(df)
    
    # Train model
    model, explainer, metrics, feature_importance, feature_cols = train_model(df)
    
    # Save all artifacts
    save_artifacts(model, explainer, metrics, feature_importance, feature_cols, encodings)
    
    logger.info("\n" + "="*70)
    logger.info("TRAINING COMPLETE - PRODUCTION MODEL READY")
    logger.info("="*70)
    logger.info(f"Data: {metrics.get('train_size', 0) + metrics.get('test_size', 0):,} real loans")
    logger.info(f"Default Rate: {metrics.get('default_rate', 0):.2%}")
    logger.info(f"ROC AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"Model: LightGBM v2.0.0 (Real Lending Club Data)")
    logger.info("="*70)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
