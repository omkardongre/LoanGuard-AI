"""
Production Recovery Rate / LGD Predictor.

Predicts loan recovery rates for Basel III capital adequacy calculations.
LGD (Loss Given Default) = 1 - recovery_rate

Uses LightGBM trained on Lending Club charged-off loans with actual recoveries.
"""

import logging
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

import numpy as np

logger = logging.getLogger(__name__)

# Model file paths - detect app root for Docker compatibility
def _get_model_dir() -> Path:
    """Get model directory path, works in both local and Docker."""
    import os
    if os.environ.get("MODEL_DIR"):
        return Path(os.environ["MODEL_DIR"])
    local_path = Path(__file__).parent.parent.parent.parent / "models"
    if local_path.exists():
        return local_path
    docker_path = Path("/app/models")
    if docker_path.exists():
        return docker_path
    return Path.cwd() / "models"

MODEL_DIR = _get_model_dir()
MODEL_PATH = MODEL_DIR / "recovery_rate_predictor.pkl"
EXPLAINER_PATH = MODEL_DIR / "recovery_rate_explainer.pkl"
CONFIG_PATH = MODEL_DIR / "recovery_rate_config.json"
METRICS_PATH = MODEL_DIR / "recovery_rate_metrics.json"
IMPORTANCE_PATH = MODEL_DIR / "recovery_rate_feature_importance.json"


@dataclass
class RecoveryRateResult:
    """Recovery rate prediction result."""
    loan_id: str
    recovery_rate: float
    recovery_rate_pct: str
    lgd: float  # Loss Given Default = 1 - recovery_rate
    lgd_pct: str
    recovery_category: str
    model_version: str
    features_used: List[str]
    data_source: str = "Lending Club 2007-2018 (Charged Off)"
    success: bool = True


@dataclass
class RecoveryExplanation:
    """SHAP explanation for recovery rate prediction."""
    loan_id: str
    explanation_type: str
    base_value: float
    top_factors: List[Dict[str, Any]]
    total_features_analyzed: int
    success: bool = True


class RecoveryRatePredictor:
    """
    Production recovery rate predictor using LightGBM with SHAP.
    Trained on 98,125 Lending Club charged-off loans with recoveries.
    
    Target: recovery_rate = recoveries / (funded_amnt - total_rec_prncp)
    LGD = 1 - recovery_rate
    """
    
    def __init__(self):
        self.model = None
        self.explainer = None
        self.base_value = None
        self.feature_importance = None
        self.config = None
        self.feature_order = []
        self.encodings = {}
        self.numeric_features = []
        self.categorical_features = []
        self._loaded = False
    
    def load(self) -> bool:
        """Load model, explainer, and config from disk."""
        if self._loaded:
            return True
        
        try:
            # Load config
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r") as f:
                    self.config = json.load(f)
                    self.feature_order = self.config.get("feature_order", [])
                    self.encodings = self.config.get("encodings", {})
                    self.numeric_features = self.config.get("numeric_features", [])
                    self.categorical_features = self.config.get("categorical_features", [])
                    self.base_value = self.config.get("base_value", 0.17)
                logger.info(f"Loaded config: {len(self.feature_order)} features")
            else:
                logger.warning(f"Config not found: {CONFIG_PATH}")
                return False
            
            # Load model
            if MODEL_PATH.exists():
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                logger.info(f"Loaded recovery rate model from {MODEL_PATH}")
            else:
                logger.warning(f"Model not found: {MODEL_PATH}")
                return False
            
            # Load explainer (optional)
            if EXPLAINER_PATH.exists():
                with open(EXPLAINER_PATH, "rb") as f:
                    self.explainer = pickle.load(f)
                logger.info(f"Loaded explainer from {EXPLAINER_PATH}")
            
            # Load feature importance
            if IMPORTANCE_PATH.exists():
                with open(IMPORTANCE_PATH, "r") as f:
                    self.feature_importance = json.load(f)
            
            self._loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Error loading recovery rate model: {e}")
            return False
    
    def _get_default_values(self) -> Dict[str, Any]:
        """Get default values for features."""
        return {
            "loan_amnt": 15000.0,
            "funded_amnt": 15000.0,
            "int_rate": 13.5,
            "installment": 450.0,
            "annual_inc": 75000.0,
            "dti": 18.0,
            "fico_range_low": 690.0,
            "open_acc": 11.0,
            "revol_bal": 15000.0,
            "revol_util": 50.0,
            "total_acc": 25.0,
            "delinq_2yrs": 0.0,
            "inq_last_6mths": 0.0,
            "pub_rec": 0.0,
            "mort_acc": 1.0,
            "grade": 2,
            "home_ownership": 1,
            "verification_status": 0,
            "purpose": 2,
            "term": 0,
        }
    
    def _encode_categorical(self, feature: str, value: Any) -> int:
        """Encode a categorical feature value."""
        if feature not in self.encodings:
            return 0
        
        encoding = self.encodings[feature]
        if isinstance(value, str):
            # Try with and without whitespace
            clean_value = value.strip()
            return encoding.get(value, encoding.get(clean_value, 0))
        return int(value) if value is not None else 0
    
    def _prepare_features(self, loan_data: Dict[str, Any]) -> List[float]:
        """Prepare feature array from loan data dict."""
        defaults = self._get_default_values()
        features = []
        
        for feature_name in self.feature_order:
            if feature_name in loan_data:
                value = loan_data[feature_name]
            else:
                value = defaults.get(feature_name, 0.0)
            
            # Encode categoricals
            if feature_name in self.categorical_features:
                value = self._encode_categorical(feature_name, value)
            
            # Ensure numeric
            try:
                features.append(float(value) if value is not None else 0.0)
            except (ValueError, TypeError):
                features.append(defaults.get(feature_name, 0.0))
        
        return features
    
    def predict(
        self,
        loan_id: str,
        loan_data: Dict[str, Any],
    ) -> RecoveryRateResult:
        """
        Predict recovery rate and LGD for a loan.
        
        Args:
            loan_id: Loan identifier
            loan_data: Loan features dictionary
            
        Returns:
            RecoveryRateResult with recovery rate and LGD
        """
        if not self.load():
            return RecoveryRateResult(
                loan_id=loan_id,
                recovery_rate=0.17,  # Mean recovery rate from training
                recovery_rate_pct="17.0%",
                lgd=0.83,
                lgd_pct="83.0%",
                recovery_category="AVERAGE",
                model_version="not_loaded",
                features_used=[],
                success=False,
            )
        
        try:
            features = self._prepare_features(loan_data)
            feature_array = np.array([features])
            
            # Predict recovery rate
            recovery_rate = float(self.model.predict(feature_array)[0])
            recovery_rate = max(0.0, min(1.0, recovery_rate))  # Clamp to [0, 1]
            
            # Calculate LGD
            lgd = 1.0 - recovery_rate
            
            # Categorize
            if recovery_rate >= 0.30:
                category = "HIGH_RECOVERY"
            elif recovery_rate >= 0.15:
                category = "MODERATE_RECOVERY"
            elif recovery_rate >= 0.05:
                category = "LOW_RECOVERY"
            else:
                category = "MINIMAL_RECOVERY"
            
            return RecoveryRateResult(
                loan_id=loan_id,
                recovery_rate=round(recovery_rate, 4),
                recovery_rate_pct=f"{recovery_rate:.1%}",
                lgd=round(lgd, 4),
                lgd_pct=f"{lgd:.1%}",
                recovery_category=category,
                model_version="1.0.0",
                features_used=self.feature_order,
            )
            
        except Exception as e:
            logger.error(f"Recovery rate prediction error: {e}")
            return RecoveryRateResult(
                loan_id=loan_id,
                recovery_rate=0.17,
                recovery_rate_pct="17.0%",
                lgd=0.83,
                lgd_pct="83.0%",
                recovery_category="UNKNOWN",
                model_version="1.0.0",
                features_used=[],
                success=False,
            )
    
    def explain(
        self,
        loan_id: str,
        loan_data: Dict[str, Any],
        top_n: int = 5,
    ) -> RecoveryExplanation:
        """Get SHAP explanation for recovery rate prediction."""
        if not self.load() or self.explainer is None:
            return RecoveryExplanation(
                loan_id=loan_id,
                explanation_type="SHAP",
                base_value=0.17,
                top_factors=[],
                total_features_analyzed=0,
                success=False,
            )
        
        try:
            features = self._prepare_features(loan_data)
            feature_array = np.array([features])
            
            shap_values = self.explainer.shap_values(feature_array)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]
            shap_values = shap_values[0] if len(shap_values.shape) > 1 else shap_values
            
            feature_shap = list(zip(self.feature_order, shap_values, features))
            feature_shap.sort(key=lambda x: abs(x[1]), reverse=True)
            
            top_factors = []
            for feature_name, shap_value, feature_value in feature_shap[:top_n]:
                direction = "increases recovery" if shap_value > 0 else "decreases recovery"
                top_factors.append({
                    "feature": feature_name,
                    "value": round(feature_value, 4),
                    "shap_value": round(float(shap_value), 4),
                    "impact": direction,
                })
            
            return RecoveryExplanation(
                loan_id=loan_id,
                explanation_type="SHAP",
                base_value=round(self.base_value or 0.17, 4),
                top_factors=top_factors,
                total_features_analyzed=len(self.feature_order),
            )
            
        except Exception as e:
            logger.error(f"SHAP explanation error: {e}")
            return RecoveryExplanation(
                loan_id=loan_id,
                explanation_type="SHAP",
                base_value=0.17,
                top_factors=[],
                total_features_analyzed=0,
                success=False,
            )
    
    def get_feature_importance(self) -> Dict[str, Any]:
        """Get global feature importance."""
        if not self.load():
            return {"success": False, "error": "Model not loaded"}
        
        if self.feature_importance:
            return {
                "success": True,
                "model_type": "recovery_rate_predictor",
                "model_version": "1.0.0",
                "data_source": "Lending Club 2007-2018 (Charged Off)",
                "total_training_samples": 98125,
                "feature_importance": [
                    {"feature": f["feature"], "importance": f["importance"], "rank": idx + 1}
                    for idx, f in enumerate(self.feature_importance[:15])
                ],
            }
        
        return {"success": False, "error": "Feature importance not available"}


# Global predictor instance
_recovery_predictor: Optional[RecoveryRatePredictor] = None


def get_recovery_predictor() -> RecoveryRatePredictor:
    """Get singleton recovery rate predictor instance."""
    global _recovery_predictor
    if _recovery_predictor is None:
        _recovery_predictor = RecoveryRatePredictor()
    return _recovery_predictor


# Public API functions
def predict_recovery_rate(
    loan_id: str,
    loan_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Predict recovery rate and LGD for a loan.
    
    Args:
        loan_id: Loan identifier
        loan_data: Loan features dictionary
        
    Returns:
        Dict with recovery rate and LGD
    """
    predictor = get_recovery_predictor()
    result = predictor.predict(loan_id, loan_data)
    return asdict(result)


def explain_recovery_prediction(
    loan_id: str,
    loan_data: Dict[str, Any],
    top_n: int = 5,
) -> Dict[str, Any]:
    """Get SHAP explanation for recovery rate prediction."""
    predictor = get_recovery_predictor()
    result = predictor.explain(loan_id, loan_data, top_n)
    return asdict(result)


def get_recovery_feature_importance() -> Dict[str, Any]:
    """Get global feature importance for recovery rate model."""
    predictor = get_recovery_predictor()
    return predictor.get_feature_importance()


def get_lgd(
    loan_id: str,
    loan_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Get Loss Given Default for a loan.
    
    LGD = 1 - recovery_rate
    Used in Basel III capital calculations: ECL = PD × LGD × EAD
    
    Args:
        loan_id: Loan identifier
        loan_data: Loan features
        
    Returns:
        Dict with LGD and related metrics
    """
    predictor = get_recovery_predictor()
    result = predictor.predict(loan_id, loan_data)
    
    return {
        "loan_id": loan_id,
        "lgd": result.lgd,
        "lgd_pct": result.lgd_pct,
        "recovery_rate": result.recovery_rate,
        "recovery_category": result.recovery_category,
        "ecl_formula": "ECL = PD × LGD × EAD",
        "model_version": result.model_version,
        "success": result.success,
    }
