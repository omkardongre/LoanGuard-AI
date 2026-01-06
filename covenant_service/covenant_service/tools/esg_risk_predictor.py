"""
ESG Risk Predictor - Production Inference Class
V9 NEW Feature: ESG Risk Scoring for SLL Loans

Loads trained XGBoost model and provides prediction interface.
"""

import pickle
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np


class ESGRiskPredictor:
    """
    Production-ready ESG Risk Scoring predictor.
    
    Predicts ESG Risk Level (LOW_RISK, MEDIUM_RISK, HIGH_RISK) for companies
    based on ESG metrics and environmental impact data.
    """
    
    MODEL_DIR = Path(__file__).parent.parent.parent.parent / "models"
    
    # Risk level descriptions
    RISK_DESCRIPTIONS = {
        'LOW_RISK': 'Company demonstrates strong ESG practices across all dimensions',
        'MEDIUM_RISK': 'Company shows moderate ESG performance with room for improvement',
        'HIGH_RISK': 'Company has significant ESG concerns requiring attention'
    }
    
    # Risk level colors for UI
    RISK_COLORS = {
        'LOW_RISK': 'green',
        'MEDIUM_RISK': 'amber',
        'HIGH_RISK': 'red'
    }
    
    def __init__(self, model_dir: str = None):
        """Initialize predictor with model directory."""
        if model_dir:
            self.model_dir = Path(model_dir)
        else:
            self.model_dir = self.MODEL_DIR
        
        self.model = None
        self.preprocessor = None
        self.label_encoder = None
        self.config = None
        self.feature_importance = None
        
        self._load_model()
    
    def _load_model(self):
        """Load model artifacts from disk."""
        try:
            # Load model
            model_path = self.model_dir / "esg_risk_model.pkl"
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Load preprocessor
            preprocessor_path = self.model_dir / "esg_risk_preprocessor.pkl"
            with open(preprocessor_path, 'rb') as f:
                self.preprocessor = pickle.load(f)
            
            # Load label encoder
            encoder_path = self.model_dir / "esg_risk_label_encoder.pkl"
            with open(encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            # Load config
            config_path = self.model_dir / "esg_risk_config.json"
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            
            # Load feature importance
            importance_path = self.model_dir / "esg_risk_feature_importance.json"
            with open(importance_path, 'r') as f:
                self.feature_importance = json.load(f)
                
        except FileNotFoundError as e:
            raise RuntimeError(f"Model files not found. Train model first: {e}")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict ESG risk level for a company.
        
        Args:
            features: Dictionary with ESG metrics:
                - ESG_Environmental: float (0-100)
                - ESG_Social: float (0-100)
                - ESG_Governance: float (0-100)
                - CarbonEmissions: float (tons CO2)
                - WaterUsage: float (cubic meters)
                - EnergyConsumption: float (MWh)
                - Industry: str
                - Region: str
                - Revenue: float (optional)
                - ProfitMargin: float (optional)
        
        Returns:
            Dictionary with prediction results
        """
        import pandas as pd
        
        # Create dataframe
        df = pd.DataFrame([features])
        
        # Fill missing features with defaults
        numeric_features = self.config.get('numeric_features', [])
        categorical_features = self.config.get('categorical_features', [])
        
        for col in numeric_features:
            if col not in df.columns:
                df[col] = 50.0  # Default middle value
        
        for col in categorical_features:
            if col not in df.columns:
                df[col] = 'Unknown'
        
        # Get feature names from config
        feature_names = self.config.get('feature_names', numeric_features + categorical_features)
        feature_cols = [col for col in feature_names if col in df.columns]
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
        
        # Calculate composite ESG score (weighted average if components provided)
        esg_components = {
            'environmental': features.get('ESG_Environmental', 50),
            'social': features.get('ESG_Social', 50),
            'governance': features.get('ESG_Governance', 50)
        }
        
        # Equal weighted composite score
        composite_score = round(
            (esg_components['environmental'] + 
             esg_components['social'] + 
             esg_components['governance']) / 3, 
            1
        )
        
        return {
            'risk_level': risk_level,
            'risk_level_display': risk_level.replace('_', ' ').title(),
            'confidence': round(float(max(pred_proba)), 4),
            'confidence_pct': f"{round(float(max(pred_proba)) * 100, 1)}%",
            'probabilities': probabilities,
            'composite_score': composite_score,
            'esg_components': esg_components,
            'description': self.RISK_DESCRIPTIONS.get(risk_level, ''),
            'color': self.RISK_COLORS.get(risk_level, 'gray'),
            'industry': features.get('Industry', 'Unknown'),
            'region': features.get('Region', 'Unknown')
        }
    
    def explain(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get feature importance explanation for prediction.
        
        Returns top contributing factors.
        """
        # Get prediction first
        prediction = self.predict(features)
        
        # Return feature importance as explanation
        # (For production, could use SHAP values)
        top_features = list(self.feature_importance.items())[:5]
        
        explanation = {
            'prediction': prediction,
            'top_factors': [
                {
                    'feature': feat,
                    'importance': imp,
                    'importance_pct': f"{imp * 100:.1f}%",
                    'value': features.get(feat, 'N/A')
                }
                for feat, imp in top_features
            ],
            'interpretation': self._generate_interpretation(features, prediction['risk_level'])
        }
        
        return explanation
    
    def _generate_interpretation(self, features: Dict[str, Any], risk_level: str) -> str:
        """Generate human-readable interpretation."""
        env_score = features.get('ESG_Environmental', 50)
        soc_score = features.get('ESG_Social', 50)
        gov_score = features.get('ESG_Governance', 50)
        
        interpretations = []
        
        if env_score < 40:
            interpretations.append("Environmental score is concerning (below 40)")
        elif env_score >= 60:
            interpretations.append("Strong environmental performance")
        
        if soc_score < 40:
            interpretations.append("Social responsibility score needs improvement")
        elif soc_score >= 60:
            interpretations.append("Good social responsibility practices")
        
        if gov_score < 40:
            interpretations.append("Governance practices require attention")
        elif gov_score >= 60:
            interpretations.append("Solid corporate governance")
        
        if risk_level == 'LOW_RISK':
            prefix = "Overall: Company demonstrates strong ESG practices."
        elif risk_level == 'MEDIUM_RISK':
            prefix = "Overall: Company has moderate ESG performance."
        else:
            prefix = "Overall: Company has significant ESG concerns."
        
        return f"{prefix} {' '.join(interpretations)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model metadata."""
        metrics_path = self.model_dir / "esg_risk_metrics.json"
        
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
        except FileNotFoundError:
            metrics = {}
        
        return {
            'model_name': 'ESG Risk Scoring Model',
            'model_type': self.config.get('model_type', 'XGBClassifier'),
            'version': self.config.get('version', 'v1.0'),
            'target': 'ESG Risk Level (LOW/MEDIUM/HIGH)',
            'classes': self.config.get('classes', []),
            'risk_thresholds': self.config.get('risk_thresholds', {}),
            'numeric_features': self.config.get('numeric_features', []),
            'categorical_features': self.config.get('categorical_features', []),
            'performance': {
                'accuracy': metrics.get('accuracy'),
                'f1_score': metrics.get('f1_score'),
                'auc_roc': metrics.get('auc_roc')
            },
            'training_data': {
                'source': 'Kaggle ESG & Financial Performance Dataset',
                'samples': metrics.get('train_samples', 0) + metrics.get('test_samples', 0),
                'companies': 1000,
                'years': '2015-2025'
            },
            'feature_importance': self.feature_importance,
            'trained_at': metrics.get('trained_at')
        }


# Singleton instance
_predictor_instance: Optional[ESGRiskPredictor] = None


def get_esg_risk_predictor() -> ESGRiskPredictor:
    """Get singleton ESGRiskPredictor instance."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = ESGRiskPredictor()
    return _predictor_instance
