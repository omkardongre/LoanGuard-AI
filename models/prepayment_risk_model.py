"""
Prepayment Risk Model - Production Training Script
V9 NEW - XGBoost classifier for early loan payoff prediction

This model predicts the probability that a loan will be paid off early
(before 90% of the term is completed). Used for portfolio yield management.

Target: prepaid_early = 1 if tenure_months < term * 0.9 else 0

Algorithm: XGBoost Classifier with SHAP explainability
Training Data: Lending Club 2007-2018 (Fully Paid loans only)
Performance Target: AUC > 0.70
"""

import os
import json
import pickle
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURATION
# ============================================

DATA_PATH = Path("self-docs/data/accepted_2007_to_2018Q4.csv")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

# Prepayment threshold: paid off before X% of term
PREPAYMENT_THRESHOLD = 0.90  # 90% of term

# Feature columns (based on research best practices)
NUMERIC_FEATURES = [
    'loan_amnt',
    'int_rate',
    'installment',
    'annual_inc',
    'dti',
    'fico_range_low',
    'fico_range_high',
    'open_acc',
    'revol_bal',
    'revol_util',
    'total_acc',
    'delinq_2yrs',
    'inq_last_6mths',
    'pub_rec',
    'mort_acc',
    'tot_cur_bal',
    'total_rev_hi_lim',
    'acc_open_past_24mths',
    'bc_util',
    'num_actv_bc_tl',
    'num_actv_rev_tl',
    'pct_tl_nvr_dlq',
]

CATEGORICAL_FEATURES = [
    'term',
    'grade',
    'sub_grade',
    'emp_length',
    'home_ownership',
    'verification_status',
    'purpose',
    'application_type',
]

# Derived features
DERIVED_FEATURES = [
    'fico_avg',
    'loan_to_income',
    'installment_to_income',
    'credit_age_months',
]


def load_and_prepare_data(sample_size: int = None) -> pd.DataFrame:
    """Load Lending Club data and prepare for training."""
    print(f"Loading data from {DATA_PATH}...")
    
    if sample_size:
        df = pd.read_csv(DATA_PATH, low_memory=False, nrows=sample_size * 3)
    else:
        df = pd.read_csv(DATA_PATH, low_memory=False)
    
    print(f"Loaded {len(df)} rows")
    
    # Filter to Fully Paid loans only (these are the ones we can calculate prepayment for)
    df = df[df['loan_status'] == 'Fully Paid'].copy()
    print(f"Fully Paid loans: {len(df)}")
    
    # Parse dates
    df['issue_d'] = pd.to_datetime(df['issue_d'], format='%b-%Y', errors='coerce')
    df['last_pymnt_d'] = pd.to_datetime(df['last_pymnt_d'], format='%b-%Y', errors='coerce')
    df['earliest_cr_line'] = pd.to_datetime(df['earliest_cr_line'], format='%b-%Y', errors='coerce')
    
    # Calculate tenure in months
    df['tenure_months'] = ((df['last_pymnt_d'] - df['issue_d']).dt.days / 30.44).fillna(0)
    
    # Parse term (e.g., " 36 months" -> 36)
    df['term_months'] = df['term'].str.extract(r'(\d+)').astype(float)
    
    # Create target variable
    df['prepaid_early'] = (df['tenure_months'] < df['term_months'] * PREPAYMENT_THRESHOLD).astype(int)
    
    # Remove loans with invalid dates or extreme tenures
    df = df[df['tenure_months'] > 0]
    df = df[df['tenure_months'] <= df['term_months'] * 1.5]  # Allow some grace
    
    print(f"Valid loans: {len(df)}")
    print(f"Prepayment rate: {df['prepaid_early'].mean()*100:.1f}%")
    
    if sample_size and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
        print(f"Sampled to: {len(df)} rows")
    
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived features for prepayment prediction."""
    df = df.copy()
    
    # FICO average
    df['fico_avg'] = (df['fico_range_low'] + df['fico_range_high']) / 2
    
    # Loan-to-income ratio
    df['loan_to_income'] = df['loan_amnt'] / (df['annual_inc'] + 1)
    
    # Installment-to-income ratio (monthly burden)
    df['installment_to_income'] = (df['installment'] * 12) / (df['annual_inc'] + 1)
    
    # Credit age in months
    if 'earliest_cr_line' in df.columns and 'issue_d' in df.columns:
        df['credit_age_months'] = ((df['issue_d'] - df['earliest_cr_line']).dt.days / 30.44).fillna(0)
        df['credit_age_months'] = df['credit_age_months'].clip(lower=0)
    else:
        df['credit_age_months'] = 0
    
    # Clean emp_length
    if 'emp_length' in df.columns:
        emp_map = {
            '< 1 year': 0, '1 year': 1, '2 years': 2, '3 years': 3,
            '4 years': 4, '5 years': 5, '6 years': 6, '7 years': 7,
            '8 years': 8, '9 years': 9, '10+ years': 10
        }
        df['emp_length_num'] = df['emp_length'].map(emp_map).fillna(0)
    
    return df


def prepare_features(df: pd.DataFrame) -> tuple:
    """Prepare feature matrix and encode categoricals."""
    
    all_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES + DERIVED_FEATURES
    
    # Select available columns
    available_numeric = [c for c in NUMERIC_FEATURES + DERIVED_FEATURES if c in df.columns]
    available_categorical = [c for c in CATEGORICAL_FEATURES if c in df.columns]
    
    print(f"Numeric features: {len(available_numeric)}")
    print(f"Categorical features: {len(available_categorical)}")
    
    # Start with numeric features
    X = df[available_numeric].copy()
    
    # Fill missing values for numeric
    for col in available_numeric:
        if X[col].dtype in ['float64', 'int64']:
            X[col] = X[col].fillna(X[col].median())
    
    # Encode categorical features
    label_encoders = {}
    for col in available_categorical:
        le = LabelEncoder()
        df[col] = df[col].fillna('Unknown').astype(str)
        X[col] = le.fit_transform(df[col])
        label_encoders[col] = le
    
    # Target
    y = df['prepaid_early'].values
    
    feature_names = list(X.columns)
    
    return X, y, feature_names, label_encoders


def train_model(X_train, y_train, X_val, y_val):
    """Train XGBoost classifier for prepayment prediction."""
    
    # Calculate scale_pos_weight for imbalanced classes
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
    
    print(f"\nClass distribution - Negative: {neg_count}, Positive: {pos_count}")
    print(f"Scale pos weight: {scale_pos_weight:.3f}")
    
    # XGBoost parameters (tuned for prepayment prediction)
    params = {
        'n_estimators': 200,
        'max_depth': 6,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 3,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'scale_pos_weight': scale_pos_weight,
        'random_state': 42,
        'n_jobs': -1,
        'eval_metric': 'auc',
        'early_stopping_rounds': 20,
    }
    
    model = xgb.XGBClassifier(**params)
    
    print("\nTraining XGBoost classifier...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    return model


def evaluate_model(model, X_test, y_test, feature_names):
    """Evaluate model and print metrics."""
    
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    auc = roc_auc_score(y_test, y_pred_proba)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print("\n" + "="*50)
    print("MODEL EVALUATION")
    print("="*50)
    print(f"ROC AUC:   {auc:.4f}")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['No Prepay', 'Prepay']))
    
    # Feature importance
    importance = model.feature_importances_
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Features:")
    print(importance_df.head(10).to_string(index=False))
    
    metrics = {
        'roc_auc': float(auc),
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'confusion_matrix': cm.tolist(),
    }
    
    return metrics, importance_df


def create_shap_explainer(model, X_train):
    """Create SHAP explainer for model interpretation."""
    import shap
    
    print("\nCreating SHAP Explainer...")
    
    # Use a small sample for background data
    background_size = min(100, len(X_train))
    if hasattr(X_train, 'sample'):
        background = X_train.sample(n=background_size, random_state=42)
    else:
        indices = np.random.choice(len(X_train), background_size, replace=False)
        background = X_train.iloc[indices] if hasattr(X_train, 'iloc') else X_train[indices]
    
    try:
        # Try KernelExplainer with predict_proba (more compatible)
        def model_predict(x):
            return model.predict_proba(x)[:, 1]
        
        explainer = shap.KernelExplainer(model_predict, background)
        base_value = explainer.expected_value
        print(f"Using KernelExplainer - base value: {base_value:.4f}")
        
    except Exception as e:
        print(f"KernelExplainer failed: {e}")
        print("Using feature importance as explanation fallback")
        
        # Create a dummy explainer-like object using feature importance
        class FeatureImportanceExplainer:
            def __init__(self, model, feature_names):
                self.expected_value = 0.5  # Default for binary classification
                self.feature_importance = dict(zip(feature_names, model.feature_importances_))
            
            def shap_values(self, X):
                # Return feature importance scaled by feature values
                if hasattr(X, 'values'):
                    X = X.values
                # Just return zeros - will use feature importance instead
                return np.zeros_like(X)
        
        explainer = FeatureImportanceExplainer(model, list(X_train.columns))
        base_value = 0.5
        print("Using FeatureImportanceExplainer fallback")
    
    return explainer, float(base_value)

def save_artifacts(
    model, 
    explainer, 
    feature_names, 
    label_encoders,
    metrics, 
    importance_df,
    base_value
):
    """Save all model artifacts."""
    
    print("\n" + "="*50)
    print("SAVING ARTIFACTS")
    print("="*50)
    
    # Save model
    model_path = MODELS_DIR / "prepayment_risk_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"✓ Model saved: {model_path}")
    
    # Save SHAP explainer (if picklable)
    try:
        explainer_path = MODELS_DIR / "prepayment_explainer.pkl"
        with open(explainer_path, 'wb') as f:
            pickle.dump(explainer, f)
        print(f"✓ Explainer saved: {explainer_path}")
    except Exception as e:
        print(f"⚠ Explainer not saved (using feature importance instead): {e}")
        # Save base value separately
        explainer_info = {
            'type': 'FeatureImportance',
            'base_value': base_value,
            'note': 'KernelExplainer not picklable, use feature importance'
        }
        explainer_info_path = MODELS_DIR / "prepayment_explainer_info.json"
        with open(explainer_info_path, 'w') as f:
            json.dump(explainer_info, f, indent=2)
        print(f"✓ Explainer info saved: {explainer_info_path}")
    
    # Save label encoders
    encoders_path = MODELS_DIR / "prepayment_label_encoders.pkl"
    with open(encoders_path, 'wb') as f:
        pickle.dump(label_encoders, f)
    print(f"✓ Label encoders saved: {encoders_path}")
    
    # Save config
    config = {
        'model_type': 'XGBoost Classifier',
        'version': '1.0',
        'target': 'prepaid_early',
        'prepayment_threshold': PREPAYMENT_THRESHOLD,
        'features': {
            'numeric': NUMERIC_FEATURES,
            'categorical': CATEGORICAL_FEATURES,
            'derived': DERIVED_FEATURES,
            'all': feature_names
        },
        'training_date': datetime.now().isoformat(),
        'data_source': str(DATA_PATH),
        'shap_base_value': float(base_value) if base_value else None,
    }
    
    config_path = MODELS_DIR / "prepayment_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✓ Config saved: {config_path}")
    
    # Save metrics
    metrics_path = MODELS_DIR / "prepayment_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✓ Metrics saved: {metrics_path}")
    
    # Save feature importance
    importance_path = MODELS_DIR / "prepayment_feature_importance.json"
    importance_dict = importance_df.set_index('feature')['importance'].to_dict()
    with open(importance_path, 'w') as f:
        json.dump(importance_dict, f, indent=2)
    print(f"✓ Feature importance saved: {importance_path}")
    
    print("\n✅ All artifacts saved successfully!")


def main():
    """Main training pipeline."""
    print("="*60)
    print("PREPAYMENT RISK MODEL - PRODUCTION TRAINING")
    print("="*60)
    print(f"Started: {datetime.now().isoformat()}")
    
    # Load data
    df = load_and_prepare_data(sample_size=200000)
    
    # Engineer features
    df = engineer_features(df)
    
    # Prepare features
    X, y, feature_names, label_encoders = prepare_features(df)
    
    print(f"\nFinal feature matrix shape: {X.shape}")
    print(f"Target distribution: {np.bincount(y)}")
    
    # Split data
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )
    
    print(f"\nTrain: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Train model
    model = train_model(X_train, y_train, X_val, y_val)
    
    # Evaluate
    metrics, importance_df = evaluate_model(model, X_test, y_test, feature_names)
    
    # Check if meets target
    if metrics['roc_auc'] >= 0.70:
        print("\n✅ Model meets target AUC >= 0.70!")
    else:
        print(f"\n⚠️ Model AUC {metrics['roc_auc']:.4f} below target 0.70")
    
    # Create SHAP explainer
    explainer, base_value = create_shap_explainer(model, X_train)
    
    # Save artifacts
    save_artifacts(
        model, explainer, feature_names, label_encoders,
        metrics, importance_df, base_value
    )
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"Final AUC: {metrics['roc_auc']:.4f}")
    print(f"Finished: {datetime.now().isoformat()}")
    
    return metrics


if __name__ == "__main__":
    metrics = main()
