"""
Prepayment Risk Predictor - Production Inference Class
V9 NEW - XGBoost classifier for early loan payoff prediction

Usage:
    from covenant_service.covenant_service.tools.prepayment_predictor import PrepaymentPredictor
    
    predictor = PrepaymentPredictor()
    result = predictor.predict(loan_features)
    explanation = predictor.explain(loan_features)
"""

import os
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class PrepaymentPrediction:
    """Structured prepayment prediction result."""
    prepay_probability: float
    prepay_probability_pct: str
    will_prepay: bool
    risk_category: str  # HIGH_PREPAY, MODERATE_PREPAY, LOW_PREPAY
    model_version: str
    
    def to_dict(self) -> Dict:
        return {
            'prepay_probability': self.prepay_probability,
            'prepay_probability_pct': self.prepay_probability_pct,
            'will_prepay': self.will_prepay,
            'risk_category': self.risk_category,
            'model_version': self.model_version,
        }


class PrepaymentPredictor:
    """
    Production-ready prepayment risk predictor.
    
    Uses XGBoost classifier trained on Lending Club data.
    Predicts probability of early loan payoff (before 90% of term).
    """
    
    MODEL_PATH = Path("models/prepayment_risk_model.pkl")
    CONFIG_PATH = Path("models/prepayment_config.json")
    ENCODERS_PATH = Path("models/prepayment_label_encoders.pkl")
    IMPORTANCE_PATH = Path("models/prepayment_feature_importance.json")
    
    def __init__(self, models_dir: str = None):
        """Initialize predictor with model artifacts."""
        if models_dir:
            self.MODEL_PATH = Path(models_dir) / "prepayment_risk_model.pkl"
            self.CONFIG_PATH = Path(models_dir) / "prepayment_config.json"
            self.ENCODERS_PATH = Path(models_dir) / "prepayment_label_encoders.pkl"
            self.IMPORTANCE_PATH = Path(models_dir) / "prepayment_feature_importance.json"
        
        self.model = None
        self.config = None
        self.label_encoders = None
        self.feature_importance = None
        self._loaded = False
        
        self._load_artifacts()
    
    def _load_artifacts(self):
        """Load all model artifacts."""
        try:
            # Load model
            with open(self.MODEL_PATH, 'rb') as f:
                self.model = pickle.load(f)
            
            # Load config
            with open(self.CONFIG_PATH, 'r') as f:
                self.config = json.load(f)
            
            # Load label encoders
            with open(self.ENCODERS_PATH, 'rb') as f:
                self.label_encoders = pickle.load(f)
            
            # Load feature importance
            with open(self.IMPORTANCE_PATH, 'r') as f:
                self.feature_importance = json.load(f)
            
            self._loaded = True
            
        except FileNotFoundError as e:
            print(f"Warning: Could not load prepayment model artifacts: {e}")
            self._loaded = False
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
    
    def _prepare_features(self, loan_data: Dict) -> pd.DataFrame:
        """Prepare feature vector from loan data."""
        # Get feature names from config
        all_features = self.config['features']['all']
        
        # Create dataframe with single row
        df = pd.DataFrame([loan_data])
        
        # Engineer derived features
        if 'fico_range_low' in df.columns and 'fico_range_high' in df.columns:
            df['fico_avg'] = (df['fico_range_low'] + df['fico_range_high']) / 2
        else:
            df['fico_avg'] = loan_data.get('fico_avg', 700)
        
        if 'loan_amnt' in df.columns and 'annual_inc' in df.columns:
            df['loan_to_income'] = df['loan_amnt'] / (df['annual_inc'] + 1)
        else:
            df['loan_to_income'] = 0.1
        
        if 'installment' in df.columns and 'annual_inc' in df.columns:
            df['installment_to_income'] = (df['installment'] * 12) / (df['annual_inc'] + 1)
        else:
            df['installment_to_income'] = 0.05
        
        df['credit_age_months'] = loan_data.get('credit_age_months', 120)
        
        # Encode categorical features
        for col, encoder in self.label_encoders.items():
            if col in df.columns:
                try:
                    df[col] = encoder.transform(df[col].fillna('Unknown').astype(str))
                except ValueError:
                    # Unknown category - use most common
                    df[col] = 0
            else:
                df[col] = 0
        
        # Ensure all features present
        for feat in all_features:
            if feat not in df.columns:
                df[feat] = 0
        
        # Fill missing values
        df = df.fillna(0)
        
        # Select and order features
        return df[all_features]
    
    def predict(self, loan_data: Dict) -> PrepaymentPrediction:
        """
        Predict prepayment probability for a loan.
        
        Args:
            loan_data: Dict with loan features
                Required: term, grade, int_rate, loan_amnt
                Optional: fico_range_low, annual_inc, dti, etc.
        
        Returns:
            PrepaymentPrediction with probability and category
        """
        if not self._loaded:
            # Return default prediction if model not loaded
            return PrepaymentPrediction(
                prepay_probability=0.5,
                prepay_probability_pct="50.0%",
                will_prepay=False,
                risk_category="UNKNOWN",
                model_version="not_loaded"
            )
        
        # Prepare features
        X = self._prepare_features(loan_data)
        
        # Predict
        probability = float(self.model.predict_proba(X)[0, 1])
        
        # Categorize
        if probability >= 0.7:
            category = "HIGH_PREPAY"
        elif probability >= 0.4:
            category = "MODERATE_PREPAY"
        else:
            category = "LOW_PREPAY"
        
        return PrepaymentPrediction(
            prepay_probability=probability,
            prepay_probability_pct=f"{probability * 100:.1f}%",
            will_prepay=probability >= 0.5,
            risk_category=category,
            model_version=self.config.get('version', '1.0')
        )
    
    def explain(self, loan_data: Dict, top_n: int = 5) -> Dict:
        """
        Get feature importance explanation for prediction.
        
        Uses global feature importance (SHAP not available due to compatibility).
        
        Args:
            loan_data: Dict with loan features
            top_n: Number of top features to return
        
        Returns:
            Dict with feature contributions
        """
        if not self._loaded or not self.feature_importance:
            return {
                'success': False,
                'error': 'Model not loaded'
            }
        
        # Get prediction first
        prediction = self.predict(loan_data)
        
        # Prepare features to get values
        X = self._prepare_features(loan_data)
        
        # Get top features by importance
        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        factors = []
        for feature, importance in sorted_features:
            if feature in X.columns:
                value = float(X[feature].iloc[0])
                factors.append({
                    'feature': feature,
                    'importance': float(importance),
                    'value': value,
                    'impact': 'HIGH' if importance > 0.05 else 'MEDIUM' if importance > 0.01 else 'LOW'
                })
        
        return {
            'success': True,
            'prepay_probability': prediction.prepay_probability,
            'risk_category': prediction.risk_category,
            'factors': factors,
            'explanation': self._generate_explanation(factors, prediction),
            'model_version': self.config.get('version', '1.0')
        }
    
    def _generate_explanation(self, factors: List[Dict], prediction: PrepaymentPrediction) -> str:
        """Generate human-readable explanation."""
        if not factors:
            return "Insufficient data for explanation"
        
        top_factor = factors[0]['feature']
        prob = prediction.prepay_probability * 100
        
        explanations = {
            'term': f"Loan term is the primary driver. Shorter terms have higher prepayment likelihood.",
            'int_rate': f"Interest rate influences prepayment behavior - higher rates may drive refinancing.",
            'grade': f"Credit grade affects borrower's ability to refinance.",
            'application_type': f"Application type (individual vs joint) impacts financial flexibility.",
            'loan_amnt': f"Loan amount affects burden and payoff capacity.",
        }
        
        base = explanations.get(top_factor, f"Top factor is {top_factor}.")
        
        return f"This loan has a {prob:.1f}% prepayment probability. {base}"
    
    def get_model_info(self) -> Dict:
        """Get model metadata."""
        if not self._loaded:
            return {'error': 'Model not loaded'}
        
        return {
            'model_type': 'XGBoost Classifier',
            'version': self.config.get('version', '1.0'),
            'target': 'prepaid_early (before 90% of term)',
            'training_data': 'Lending Club 2007-2018',
            'training_samples': 200000,
            'features': {
                'numeric': len(self.config['features'].get('numeric', [])),
                'categorical': len(self.config['features'].get('categorical', [])),
                'derived': len(self.config['features'].get('derived', [])),
                'total': len(self.config['features'].get('all', []))
            },
            'top_features': list(sorted(
                self.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            ))[:5] if self.feature_importance else []
        }


# Singleton instance
_prepayment_predictor: Optional[PrepaymentPredictor] = None


def get_prepayment_predictor() -> PrepaymentPredictor:
    """Get or create prepayment predictor singleton."""
    global _prepayment_predictor
    if _prepayment_predictor is None:
        _prepayment_predictor = PrepaymentPredictor()
    return _prepayment_predictor
