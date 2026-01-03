"""
GCS Model Loader for ML models.

Based on EnergyAgentAI pattern for loading XGBoost models and SHAP explainers from GCS.
"""

import logging
import pickle
import json
from typing import Any, Dict, Optional
import os

logger = logging.getLogger(__name__)

# Configuration
GCS_BUCKET = os.getenv("GCS_MODEL_BUCKET", "loanguard-models")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# Model cache
_model_cache: Dict[str, Any] = {}
_explainer_cache: Dict[str, Any] = {}
_categories_cache: Dict[str, Any] = {}


class ModelLoader:
    """
    Load and cache ML models from Google Cloud Storage.
    
    Pattern adapted from EnergyAgentAI SimpleXGBoostScorer.
    """
    
    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or GCS_BUCKET
        self._client = None
        self._bucket = None
        
        # Base values for probability conversion (calibrated per model)
        self.base_values = {
            "breach_predictor": -0.15,
            "debt_ebitda_predictor": -0.12,
            "interest_coverage_predictor": -0.18,
        }
        
        # Feature definitions
        self.numeric_features = [
            "debt_to_ebitda_ratio",
            "interest_coverage_ratio",
            "current_ratio",
            "net_worth",
            "revenue_growth",
            "ebitda_margin",
            "debt_service_coverage",
            "quick_ratio",
            "operating_cash_flow",
            "capex_to_revenue",
            "days_since_last_measurement",
            "measurement_volatility",
            "industry_risk_score",
        ]
        
        self.categorical_features = [
            "industry_sector",
            "loan_type",
            "covenant_type",
            "borrower_rating",
            "geographic_region",
        ]
    
    @property
    def client(self):
        """Lazy initialization of GCS client."""
        if self._client is None:
            try:
                from google.cloud import storage
                self._client = storage.Client(project=PROJECT_ID)
                self._bucket = self._client.bucket(self.bucket_name)
                logger.info(f"GCS client initialized for bucket: {self.bucket_name}")
            except Exception as e:
                logger.warning(f"GCS client initialization failed: {e}")
                self._client = False  # Mark as unavailable
        return self._client
    
    def load_model(self, model_name: str) -> Optional[Any]:
        """
        Load a model from GCS or cache.
        
        Args:
            model_name: Name of the model (e.g., 'breach_predictor')
            
        Returns:
            Loaded model or None
        """
        if model_name in _model_cache:
            logger.debug(f"Returning cached model: {model_name}")
            return _model_cache[model_name]
        
        model_path = f"models/{model_name}.pkl"
        
        try:
            if self.client and self.client is not False:
                blob = self._bucket.blob(model_path)
                model_bytes = blob.download_as_bytes()
                model = pickle.loads(model_bytes)
                _model_cache[model_name] = model
                logger.info(f"Loaded model from GCS: {model_name}")
                return model
        except Exception as e:
            logger.warning(f"Could not load model from GCS: {e}")
        
        # Fallback: Try local models directory
        local_path = f"models/{model_name}.pkl"
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                model = pickle.load(f)
            _model_cache[model_name] = model
            logger.info(f"Loaded model from local: {model_name}")
            return model
        
        logger.error(f"Model not found: {model_name}")
        return None
    
    def load_shap_explainer(self, model_name: str) -> Optional[Any]:
        """
        Load SHAP explainer from GCS or cache.
        
        Args:
            model_name: Name of the model
            
        Returns:
            SHAP explainer or None
        """
        explainer_name = f"{model_name}_shap"
        
        if explainer_name in _explainer_cache:
            return _explainer_cache[explainer_name]
        
        explainer_path = f"shap_explainers/{model_name}_explainer.pkl"
        
        try:
            if self.client and self.client is not False:
                blob = self._bucket.blob(explainer_path)
                explainer_bytes = blob.download_as_bytes()
                explainer = pickle.loads(explainer_bytes)
                _explainer_cache[explainer_name] = explainer
                logger.info(f"Loaded SHAP explainer from GCS: {model_name}")
                return explainer
        except Exception as e:
            logger.warning(f"Could not load SHAP explainer: {e}")
        
        return None
    
    def load_categories(self, filename: str = "train_categories.json") -> Optional[Dict]:
        """
        Load training categories for categorical features.
        
        Args:
            filename: Categories file name
            
        Returns:
            Categories dictionary or None
        """
        if filename in _categories_cache:
            return _categories_cache[filename]
        
        try:
            if self.client and self.client is not False:
                blob = self._bucket.blob(f"categories/{filename}")
                categories_json = blob.download_as_text()
                categories = json.loads(categories_json)
                _categories_cache[filename] = categories
                logger.info(f"Loaded categories from GCS: {filename}")
                return categories
        except Exception as e:
            logger.warning(f"Could not load categories: {e}")
        
        return None
    
    def get_base_value(self, model_name: str) -> float:
        """Get calibrated base value for a model."""
        return self.base_values.get(model_name, 0.0)
    
    def sigmoid(self, x: float) -> float:
        """Convert log-odds to probability."""
        import numpy as np
        return 1 / (1 + np.exp(-x))


# Global loader instance
_loader: Optional[ModelLoader] = None


def get_model_loader() -> ModelLoader:
    """Get or create the global model loader."""
    global _loader
    if _loader is None:
        _loader = ModelLoader()
    return _loader


def predict_breach_probability(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict breach probability using loaded model.
    
    Args:
        features: Feature dictionary
        
    Returns:
        Prediction result with probability and SHAP explanation
    """
    import numpy as np
    
    loader = get_model_loader()
    model = loader.load_model("breach_predictor")
    
    if model is None:
        # Return simulated prediction if model not available
        logger.warning("Using simulated prediction - model not loaded")
        
        # Simple heuristic based on key features
        debt_ratio = features.get("debt_to_ebitda_ratio", 3.0)
        icr = features.get("interest_coverage_ratio", 3.0)
        
        risk_score = 0.0
        if debt_ratio > 4.0:
            risk_score += 0.3
        if debt_ratio > 5.0:
            risk_score += 0.2
        if icr < 2.0:
            risk_score += 0.3
        if icr < 1.5:
            risk_score += 0.2
        
        probability = min(0.95, risk_score)
        
        return {
            "success": True,
            "probability": round(probability, 4),
            "risk_level": "HIGH" if probability > 0.5 else "MEDIUM" if probability > 0.25 else "LOW",
            "model_version": "heuristic_v1",
            "explanation": {
                "top_factors": [
                    {"feature": "debt_to_ebitda_ratio", "impact": "high" if debt_ratio > 4 else "low"},
                    {"feature": "interest_coverage_ratio", "impact": "high" if icr < 2 else "low"},
                ],
            },
        }
    
    try:
        import xgboost as xgb
        import pandas as pd
        
        # Prepare features
        feature_df = pd.DataFrame([features])
        
        # Handle missing features
        for col in loader.numeric_features:
            if col not in feature_df.columns:
                feature_df[col] = 0.0
        
        for col in loader.categorical_features:
            if col not in feature_df.columns:
                feature_df[col] = "unknown"
        
        # Reorder columns
        feature_cols = loader.numeric_features + loader.categorical_features
        X = feature_df[feature_cols]
        
        # Make prediction
        dmatrix = xgb.DMatrix(X, enable_categorical=True)
        raw_prediction = model.predict(dmatrix)[0]
        probability = loader.sigmoid(raw_prediction)
        
        result = {
            "success": True,
            "probability": round(float(probability), 4),
            "risk_level": "HIGH" if probability > 0.5 else "MEDIUM" if probability > 0.25 else "LOW",
            "model_version": "xgboost_v1",
        }
        
        # Add SHAP explanation if available
        explainer = loader.load_shap_explainer("breach_predictor")
        if explainer is not None:
            shap_values = explainer.shap_values(dmatrix)
            base_value = loader.get_base_value("breach_predictor")
            
            # Get top contributing features
            feature_importance = list(zip(feature_cols, shap_values[0]))
            feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
            
            result["explanation"] = {
                "base_probability": round(loader.sigmoid(base_value), 4),
                "top_factors": [
                    {
                        "feature": f[0],
                        "shap_value": round(float(f[1]), 4),
                        "impact": "increases" if f[1] > 0 else "decreases",
                    }
                    for f in feature_importance[:5]
                ],
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return {"success": False, "error": str(e)}
