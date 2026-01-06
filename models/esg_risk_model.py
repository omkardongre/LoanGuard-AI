#!/usr/bin/env python3
"""
ESG Risk Scoring Model - Production Training Script
V9 NEW Feature: ML-based ESG Risk Classification

Model: XGBoost Classifier
Target: ESG Risk Level (LOW_RISK, MEDIUM_RISK, HIGH_RISK)
Data: Kaggle ESG & Financial Performance Dataset (11K rows, 1000 companies)
"""

import pandas as pd
import numpy as np
import json
import pickle
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# ML imports
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder, OrdinalEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    roc_auc_score, f1_score
)
import xgboost as xgb

# Explainability
import shap

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')


class ESGRiskModel:
    """
    Production-level ESG Risk Scoring Model.
    
    Classifies companies into LOW_RISK, MEDIUM_RISK, HIGH_RISK
    based on ESG metrics and environmental impact data.
    """
    
    # Risk level thresholds (based on ESG_Overall 0-100 scale)
    RISK_THRESHOLDS = {
        'HIGH_RISK': (0, 40),      # ESG_Overall < 40
        'MEDIUM_RISK': (40, 60),   # 40 <= ESG_Overall < 60
        'LOW_RISK': (60, 100)      # ESG_Overall >= 60
    }
    
    # Feature definitions
    NUMERIC_FEATURES = [
        'ESG_Environmental',
        'ESG_Social', 
        'ESG_Governance',
        'CarbonEmissions',
        'WaterUsage',
        'EnergyConsumption',
        'Revenue',
        'ProfitMargin'
    ]
    
    CATEGORICAL_FEATURES = [
        'Industry',
        'Region'
    ]
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.model = None
        self.preprocessor = None
        self.label_encoder = None
        self.feature_names = None
        self.metrics = {}
        
    def load_data(self, data_path: str = None) -> pd.DataFrame:
        """Load the ESG dataset."""
        if data_path is None:
            # Default path for Kaggle ESG dataset
            data_path = "self-docs/data/ESG & Financial Performance Dataset/company_esg_financial_dataset.csv"
        
        print(f"📂 Loading data from: {data_path}")
        df = pd.read_csv(data_path)
        print(f"   Loaded {len(df):,} rows, {len(df.columns)} columns")
        return df
    
    def create_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create ESG Risk Level target variable."""
        def assign_risk_level(score):
            if score < 40:
                return 'HIGH_RISK'
            elif score < 60:
                return 'MEDIUM_RISK'
            else:
                return 'LOW_RISK'
        
        df = df.copy()
        df['ESG_Risk_Level'] = df['ESG_Overall'].apply(assign_risk_level)
        
        print(f"\n📊 Target Distribution:")
        print(df['ESG_Risk_Level'].value_counts())
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target for training."""
        # Select features
        feature_cols = self.NUMERIC_FEATURES + self.CATEGORICAL_FEATURES
        
        # Check which features exist in dataset
        available_features = [col for col in feature_cols if col in df.columns]
        missing_features = [col for col in feature_cols if col not in df.columns]
        
        if missing_features:
            print(f"⚠️  Missing features (will skip): {missing_features}")
        
        X = df[available_features].copy()
        y = df['ESG_Risk_Level'].copy()
        
        # Store feature names
        self.feature_names = available_features
        
        print(f"\n🔧 Features prepared: {len(available_features)} features")
        return X, y
    
    def build_preprocessor(self, X: pd.DataFrame) -> ColumnTransformer:
        """Build sklearn preprocessing pipeline."""
        numeric_cols = [col for col in self.NUMERIC_FEATURES if col in X.columns]
        categorical_cols = [col for col in self.CATEGORICAL_FEATURES if col in X.columns]
        
        numeric_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline(steps=[
            ('encoder', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))
        ])
        
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_cols),
                ('cat', categorical_transformer, categorical_cols)
            ],
            remainder='passthrough'
        )
        
        return preprocessor
    
    def train(self, df: pd.DataFrame = None, test_size: float = 0.2) -> Dict[str, Any]:
        """
        Train the ESG Risk Scoring model.
        
        Returns:
            Dictionary with training metrics
        """
        print("=" * 60)
        print("🚀 ESG Risk Scoring Model - Training")
        print("=" * 60)
        
        # Load data if not provided
        if df is None:
            df = self.load_data()
        
        # Create target
        df = self.create_target(df)
        
        # Handle missing values
        df = df.dropna(subset=['ESG_Overall'])
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        # Handle any remaining missing values in features
        X = X.fillna(X.median(numeric_only=True))
        for col in X.select_dtypes(include=['object']).columns:
            X[col] = X[col].fillna('Unknown')
        
        # Encode target
        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y)
        
        print(f"\n📋 Classes: {list(self.label_encoder.classes_)}")
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=test_size, random_state=42, stratify=y_encoded
        )
        
        print(f"\n📊 Data Split:")
        print(f"   Train: {len(X_train):,} samples")
        print(f"   Test: {len(X_test):,} samples")
        
        # Build preprocessor
        self.preprocessor = self.build_preprocessor(X_train)
        
        # Preprocess data
        X_train_processed = self.preprocessor.fit_transform(X_train)
        X_test_processed = self.preprocessor.transform(X_test)
        
        # Train XGBoost
        print("\n🔄 Training XGBoost Classifier...")
        
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss',
            n_jobs=-1
        )
        
        self.model.fit(
            X_train_processed, 
            y_train,
            eval_set=[(X_test_processed, y_test)],
            verbose=False
        )
        
        # Evaluate
        y_pred = self.model.predict(X_test_processed)
        y_pred_proba = self.model.predict_proba(X_test_processed)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # Multi-class AUC (one-vs-rest)
        try:
            auc = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
        except Exception:
            auc = 0.0
        
        self.metrics = {
            'accuracy': round(accuracy, 4),
            'f1_score': round(f1, 4),
            'auc_roc': round(auc, 4),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'n_features': X_train_processed.shape[1],
            'classes': list(self.label_encoder.classes_),
            'trained_at': datetime.now().isoformat()
        }
        
        print("\n" + "=" * 60)
        print("📈 Model Performance")
        print("=" * 60)
        print(f"   Accuracy:  {accuracy:.4f} ({accuracy*100:.1f}%)")
        print(f"   F1 Score:  {f1:.4f}")
        print(f"   AUC-ROC:   {auc:.4f}")
        
        print("\n📋 Classification Report:")
        print(classification_report(
            y_test, y_pred,
            target_names=self.label_encoder.classes_
        ))
        
        # Feature importance
        self._compute_feature_importance(X_train_processed, X_train)
        
        return self.metrics
    
    def _compute_feature_importance(self, X_processed: np.ndarray, X_original: pd.DataFrame):
        """Compute and save feature importance."""
        # Get feature names after preprocessing
        numeric_cols = [col for col in self.NUMERIC_FEATURES if col in X_original.columns]
        categorical_cols = [col for col in self.CATEGORICAL_FEATURES if col in X_original.columns]
        processed_features = numeric_cols + categorical_cols
        
        # XGBoost native importance
        importances = self.model.feature_importances_
        
        # Create importance dict
        importance_dict = {}
        for i, feat in enumerate(processed_features[:len(importances)]):
            importance_dict[feat] = round(float(importances[i]), 4)
        
        # Sort by importance
        importance_dict = dict(sorted(
            importance_dict.items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        self.feature_importance = importance_dict
        
        print("\n🔍 Top Feature Importance:")
        for i, (feat, imp) in enumerate(list(importance_dict.items())[:5]):
            print(f"   {i+1}. {feat}: {imp:.4f} ({imp*100:.1f}%)")
    
    def save(self):
        """Save model artifacts."""
        print("\n💾 Saving model artifacts...")
        
        # Save model
        model_path = self.model_dir / "esg_risk_model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"   ✓ Model: {model_path}")
        
        # Save preprocessor
        preprocessor_path = self.model_dir / "esg_risk_preprocessor.pkl"
        with open(preprocessor_path, 'wb') as f:
            pickle.dump(self.preprocessor, f)
        print(f"   ✓ Preprocessor: {preprocessor_path}")
        
        # Save label encoder
        encoder_path = self.model_dir / "esg_risk_label_encoder.pkl"
        with open(encoder_path, 'wb') as f:
            pickle.dump(self.label_encoder, f)
        print(f"   ✓ Label Encoder: {encoder_path}")
        
        # Save metrics
        metrics_path = self.model_dir / "esg_risk_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        print(f"   ✓ Metrics: {metrics_path}")
        
        # Save feature importance
        importance_path = self.model_dir / "esg_risk_feature_importance.json"
        with open(importance_path, 'w') as f:
            json.dump(self.feature_importance, f, indent=2)
        print(f"   ✓ Feature Importance: {importance_path}")
        
        # Save config
        config = {
            'model_type': 'XGBClassifier',
            'version': 'v1.0',
            'target': 'ESG_Risk_Level',
            'classes': list(self.label_encoder.classes_),
            'risk_thresholds': self.RISK_THRESHOLDS,
            'numeric_features': self.NUMERIC_FEATURES,
            'categorical_features': self.CATEGORICAL_FEATURES,
            'feature_names': self.feature_names,
            'trained_at': self.metrics.get('trained_at')
        }
        config_path = self.model_dir / "esg_risk_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"   ✓ Config: {config_path}")
        
        print("\n✅ All artifacts saved!")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction on new data."""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Create dataframe from features
        df = pd.DataFrame([features])
        
        # Fill missing features with defaults
        for col in self.NUMERIC_FEATURES:
            if col not in df.columns:
                df[col] = 0.0
        for col in self.CATEGORICAL_FEATURES:
            if col not in df.columns:
                df[col] = 'Unknown'
        
        # Reorder columns
        feature_cols = [col for col in self.feature_names if col in df.columns]
        X = df[feature_cols]
        
        # Preprocess
        X_processed = self.preprocessor.transform(X)
        
        # Predict
        pred_class = self.model.predict(X_processed)[0]
        pred_proba = self.model.predict_proba(X_processed)[0]
        
        # Decode
        risk_level = self.label_encoder.inverse_transform([pred_class])[0]
        
        # Build probability dict
        probabilities = {}
        for i, cls in enumerate(self.label_encoder.classes_):
            probabilities[cls] = round(float(pred_proba[i]), 4)
        
        return {
            'risk_level': risk_level,
            'confidence': round(float(max(pred_proba)), 4),
            'probabilities': probabilities
        }


def main():
    """Main training pipeline."""
    print("\n" + "=" * 60)
    print("🌍 ESG Risk Scoring Model - Training Pipeline")
    print("=" * 60)
    
    # Initialize model
    model = ESGRiskModel(model_dir="models")
    
    # Train
    metrics = model.train()
    
    # Save
    model.save()
    
    # Test prediction
    print("\n" + "=" * 60)
    print("🧪 Test Prediction")
    print("=" * 60)
    
    test_company = {
        'ESG_Environmental': 65.0,
        'ESG_Social': 55.0,
        'ESG_Governance': 70.0,
        'CarbonEmissions': 25000,
        'WaterUsage': 15000,
        'EnergyConsumption': 50000,
        'Revenue': 5000,
        'ProfitMargin': 12.0,
        'Industry': 'Technology',
        'Region': 'North America'
    }
    
    result = model.predict(test_company)
    print(f"\n   Test Company Prediction:")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Confidence: {result['confidence']:.1%}")
    print(f"   Probabilities: {result['probabilities']}")
    
    print("\n" + "=" * 60)
    print("✅ Training Complete!")
    print("=" * 60)
    
    return model


if __name__ == "__main__":
    main()
