"""
Generate ML Model for Breach Prediction - LoanGuard AI

This script creates a trained XGBoost model with SHAP explainability
using synthetic data. For demo purposes when real training data is unavailable.

Output:
- models/breach_predictor.pkl (XGBoost model)
- models/shap_base_values.json (SHAP configuration)
- models/feature_names.json (Feature list)

Run: python scripts/generate_ml_model.py
"""

import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime

# Ensure models directory exists
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    import shap
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install xgboost shap scikit-learn pandas numpy")
    sys.exit(1)


# Feature definitions matching V6 architecture
FEATURE_NAMES = [
    "debt_to_ebitda_ratio",
    "interest_coverage_ratio",
    "current_ratio",
    "debt_to_ebitda_velocity",
    "interest_coverage_velocity",
    "headroom_percent",
    "days_to_maturity",
    "revenue_growth_yoy",
    "ebitda_margin",
    "industry_risk_score",
    "historical_breach_count",
    "is_sll_loan",
]


def generate_synthetic_training_data(n_samples: int = 5000) -> pd.DataFrame:
    """
    Generate synthetic training data for breach prediction.
    
    Creates realistic feature distributions that model actual loan behavior.
    """
    np.random.seed(42)
    
    data = {
        # Financial ratios
        "debt_to_ebitda_ratio": np.clip(np.random.lognormal(1.0, 0.5, n_samples), 0.5, 8.0),
        "interest_coverage_ratio": np.clip(np.random.lognormal(1.2, 0.4, n_samples), 0.5, 10.0),
        "current_ratio": np.clip(np.random.lognormal(0.5, 0.3, n_samples), 0.5, 4.0),
        
        # Velocity (rate of change) - can be negative
        "debt_to_ebitda_velocity": np.random.normal(0.1, 0.3, n_samples),
        "interest_coverage_velocity": np.random.normal(-0.05, 0.2, n_samples),
        
        # Other metrics
        "headroom_percent": np.clip(np.random.normal(15, 10, n_samples), -20, 50),
        "days_to_maturity": np.random.randint(90, 1825, n_samples),
        "revenue_growth_yoy": np.random.normal(0.05, 0.15, n_samples),
        "ebitda_margin": np.clip(np.random.normal(0.15, 0.08, n_samples), 0.01, 0.5),
        "industry_risk_score": np.random.uniform(0.1, 0.9, n_samples),
        "historical_breach_count": np.random.poisson(0.3, n_samples),
        "is_sll_loan": np.random.binomial(1, 0.3, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Generate target variable (breach probability)
    # Based on realistic risk factors
    breach_score = (
        0.15 * (df["debt_to_ebitda_ratio"] > 3.5).astype(float) +
        0.20 * (df["debt_to_ebitda_ratio"] > 4.0).astype(float) +
        0.15 * (df["interest_coverage_ratio"] < 2.0).astype(float) +
        0.20 * (df["interest_coverage_ratio"] < 1.5).astype(float) +
        0.10 * (df["current_ratio"] < 1.2).astype(float) +
        0.15 * (df["debt_to_ebitda_velocity"] > 0.2).astype(float) +
        0.10 * (df["headroom_percent"] < 10).astype(float) +
        0.15 * (df["headroom_percent"] < 5).astype(float) +
        0.05 * (df["revenue_growth_yoy"] < 0).astype(float) +
        0.10 * (df["industry_risk_score"] > 0.7).astype(float) +
        0.05 * (df["historical_breach_count"] > 0).astype(float) +
        np.random.normal(0, 0.1, n_samples)  # Random noise
    )
    
    # Convert to binary target with threshold
    df["will_breach"] = (breach_score > 0.5).astype(int)
    
    # Ensure reasonable class balance (~20% breach rate)
    breach_rate = df["will_breach"].mean()
    print(f"Generated data with {breach_rate:.1%} breach rate")
    
    return df


def train_model(df: pd.DataFrame) -> tuple:
    """Train XGBoost model and return model with metrics."""
    
    X = df[FEATURE_NAMES]
    y = df["will_breach"]
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Train XGBoost model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        use_label_encoder=False,
        eval_metric="logloss",
    )
    
    print("\nTraining XGBoost model...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )
    
    # Predictions
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
    }
    
    print("\n📊 Model Performance:")
    print(f"  Accuracy:  {metrics['accuracy']:.3f}")
    print(f"  Precision: {metrics['precision']:.3f}")
    print(f"  Recall:    {metrics['recall']:.3f}")
    print(f"  F1 Score:  {metrics['f1']:.3f}")
    print(f"  ROC AUC:   {metrics['roc_auc']:.3f}")
    
    return model, X_test, metrics


def generate_shap_values(model, X_sample: pd.DataFrame) -> dict:
    """Generate SHAP explainer and base values."""
    
    print("\n🔍 Generating SHAP explainer...")
    
    # Use a sample for SHAP (faster)
    X_shap = X_sample.head(500)
    
    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_shap)
    
    # Get base value (expected value)
    base_value = float(explainer.expected_value)
    
    # Calculate mean absolute SHAP values for feature importance
    if isinstance(shap_values, list):
        shap_values = shap_values[1]  # For binary classification
    
    feature_importance = {}
    for i, feat in enumerate(FEATURE_NAMES):
        feature_importance[feat] = float(np.abs(shap_values[:, i]).mean())
    
    # Sort by importance
    feature_importance = dict(
        sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    )
    
    print("\n📈 Feature Importance (SHAP):")
    for feat, imp in list(feature_importance.items())[:5]:
        print(f"  {feat}: {imp:.4f}")
    
    return {
        "base_value": base_value,
        "feature_importance": feature_importance,
        "model_type": "XGBClassifier",
        "explainer_type": "TreeExplainer",
        "generated_at": datetime.now().isoformat(),
    }


def save_model(model, shap_config: dict, metrics: dict):
    """Save model and configuration files."""
    
    # Save XGBoost model
    model_path = os.path.join(MODELS_DIR, "breach_predictor.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"\n💾 Model saved to: {model_path}")
    
    # Save SHAP configuration
    shap_path = os.path.join(MODELS_DIR, "shap_base_values.json")
    with open(shap_path, "w") as f:
        json.dump(shap_config, f, indent=2)
    print(f"💾 SHAP config saved to: {shap_path}")
    
    # Save feature names
    features_path = os.path.join(MODELS_DIR, "feature_names.json")
    with open(features_path, "w") as f:
        json.dump({
            "features": FEATURE_NAMES,
            "count": len(FEATURE_NAMES),
        }, f, indent=2)
    print(f"💾 Features saved to: {features_path}")
    
    # Save metrics
    metrics_path = os.path.join(MODELS_DIR, "model_metrics.json")
    metrics["generated_at"] = datetime.now().isoformat()
    metrics["model_version"] = "1.0.0"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"💾 Metrics saved to: {metrics_path}")


def main():
    """Main function to generate ML model."""
    print("=" * 60)
    print("LoanGuard AI - ML Model Generator")
    print("=" * 60)
    
    # Generate synthetic data
    print("\n📝 Generating synthetic training data...")
    df = generate_synthetic_training_data(5000)
    
    # Train model
    model, X_test, metrics = train_model(df)
    
    # Generate SHAP values
    shap_config = generate_shap_values(model, X_test)
    
    # Save everything
    save_model(model, shap_config, metrics)
    
    print("\n" + "=" * 60)
    print("✅ ML Model generation complete!")
    print("=" * 60)
    print("\nFiles created:")
    print("  - models/breach_predictor.pkl")
    print("  - models/shap_base_values.json")
    print("  - models/feature_names.json")
    print("  - models/model_metrics.json")


if __name__ == "__main__":
    main()
