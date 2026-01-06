"""
Two-Stage LGD Predictor for Production Use.

Uses two LightGBM models:
- Stage 1: Classifier to predict P(has_recovery)  
- Stage 2: Regressor to predict recovery_rate given recovery exists
- Final: recovery_rate = P(has_recovery) × predicted_recovery_rate
- LGD = 1 - recovery_rate

For Basel III compliance: ECL = PD × LGD × EAD
"""

import logging
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

import numpy as np

logger = logging.getLogger(__name__)

# Model paths
MODEL_DIR = Path(__file__).parent.parent.parent.parent / "models"
STAGE1_MODEL_PATH = MODEL_DIR / "lgd_stage1_classifier.pkl"
STAGE2_MODEL_PATH = MODEL_DIR / "lgd_stage2_regressor.pkl"
STAGE1_EXPLAINER_PATH = MODEL_DIR / "lgd_stage1_explainer.pkl"
STAGE2_EXPLAINER_PATH = MODEL_DIR / "lgd_stage2_explainer.pkl"
CONFIG_PATH = MODEL_DIR / "lgd_two_stage_config.json"
METRICS_PATH = MODEL_DIR / "lgd_two_stage_metrics.json"


@dataclass
class LGDPrediction:
    """Two-stage LGD prediction result."""
    loan_id: str
    p_has_recovery: float
    predicted_recovery_rate: float
    final_recovery_rate: float
    lgd: float
    lgd_pct: str
    recovery_category: str
    model_version: str = "2.0.0-two-stage"
    stage1_confidence: str = "N/A"
    success: bool = True


@dataclass  
class LGDExplanation:
    """SHAP explanation for LGD prediction."""
    loan_id: str
    stage1_factors: List[Dict[str, Any]]
    stage2_factors: List[Dict[str, Any]]
    success: bool = True


class TwoStageLGDPredictor:
    """
    Production two-stage LGD predictor.
    
    Stage 1: Classification - P(has_recovery)
    Stage 2: Regression - recovery_rate given recovery exists
    Final: P(has_recovery) × recovery_rate
    """
    
    def __init__(self):
        self.stage1_model = None
        self.stage2_model = None
        self.stage1_explainer = None
        self.stage2_explainer = None
        self.config = None
        self.feature_order = []
        self.encodings = {}
        self._loaded = False
    
    def load(self) -> bool:
        """Load both models and config."""
        if self._loaded:
            return True
        
        try:
            # Load config
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r") as f:
                    self.config = json.load(f)
                    self.feature_order = self.config.get("feature_order", [])
                    self.encodings = self.config.get("encodings", {})
            else:
                logger.warning(f"Config not found: {CONFIG_PATH}")
                return False
            
            # Load Stage 1 model
            if STAGE1_MODEL_PATH.exists():
                with open(STAGE1_MODEL_PATH, "rb") as f:
                    self.stage1_model = pickle.load(f)
            else:
                logger.warning(f"Stage 1 model not found")
                return False
            
            # Load Stage 2 model
            if STAGE2_MODEL_PATH.exists():
                with open(STAGE2_MODEL_PATH, "rb") as f:
                    self.stage2_model = pickle.load(f)
            else:
                logger.warning(f"Stage 2 model not found")
                return False
            
            # Load explainers (optional)
            if STAGE1_EXPLAINER_PATH.exists():
                with open(STAGE1_EXPLAINER_PATH, "rb") as f:
                    self.stage1_explainer = pickle.load(f)
            if STAGE2_EXPLAINER_PATH.exists():
                with open(STAGE2_EXPLAINER_PATH, "rb") as f:
                    self.stage2_explainer = pickle.load(f)
            
            logger.info("Loaded Two-Stage LGD models successfully")
            self._loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Error loading LGD models: {e}")
            return False
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Default feature values."""
        return {
            "loan_amnt": 15000.0, "funded_amnt": 15000.0,
            "int_rate": 13.5, "installment": 450.0,
            "annual_inc": 75000.0, "dti": 18.0,
            "fico_range_low": 690.0, "fico_range_high": 710.0,
            "open_acc": 11.0, "revol_bal": 15000.0,
            "revol_util": 50.0, "total_acc": 25.0,
            "delinq_2yrs": 0.0, "inq_last_6mths": 0.0,
            "pub_rec": 0.0, "mort_acc": 1.0,
            "pub_rec_bankruptcies": 0.0,
            "grade": 2, "home_ownership": 1,
            "verification_status": 0, "purpose": 2,
            "term": 0, "application_type": 0,
            # Engineered features
            "fico_avg": 700.0, "income_to_loan": 5.0,
            "inst_to_inc": 0.07, "high_revol_util": 0,
            "has_delinq": 0, "has_bankruptcy": 0,
        }
    
    def _encode_categorical(self, feature: str, value: Any) -> int:
        """Encode categorical feature."""
        if feature not in self.encodings:
            return 0
        encoding = self.encodings[feature]
        if isinstance(value, str):
            return encoding.get(value.strip(), 0)
        return int(value) if value is not None else 0
    
    def _prepare_features(self, loan_data: Dict[str, Any]) -> np.ndarray:
        """Prepare feature array from loan data."""
        defaults = self._get_defaults()
        
        # Engineer features if raw data provided
        if "fico_avg" not in loan_data and "fico_range_low" in loan_data:
            low = float(loan_data.get("fico_range_low", 690))
            high = float(loan_data.get("fico_range_high", low + 20))
            loan_data["fico_avg"] = (low + high) / 2
        
        if "income_to_loan" not in loan_data:
            inc = float(loan_data.get("annual_inc", 75000))
            amt = float(loan_data.get("loan_amnt", 15000))
            loan_data["income_to_loan"] = inc / (amt + 1)
        
        if "inst_to_inc" not in loan_data:
            inst = float(loan_data.get("installment", 450))
            inc = float(loan_data.get("annual_inc", 75000))
            loan_data["inst_to_inc"] = inst / (inc / 12 + 1)
        
        if "high_revol_util" not in loan_data:
            util = float(loan_data.get("revol_util", 50))
            loan_data["high_revol_util"] = 1 if util > 80 else 0
        
        if "has_delinq" not in loan_data:
            loan_data["has_delinq"] = 1 if float(loan_data.get("delinq_2yrs", 0)) > 0 else 0
        
        if "has_bankruptcy" not in loan_data:
            loan_data["has_bankruptcy"] = 1 if float(loan_data.get("pub_rec_bankruptcies", 0)) > 0 else 0
        
        features = []
        categorical_features = self.config.get("categorical_features", [])
        
        for feature_name in self.feature_order:
            value = loan_data.get(feature_name, defaults.get(feature_name, 0))
            
            if feature_name in categorical_features:
                value = self._encode_categorical(feature_name, value)
            
            try:
                features.append(float(value) if value is not None else 0.0)
            except (ValueError, TypeError):
                features.append(defaults.get(feature_name, 0.0))
        
        return np.array([features])
    
    def predict(self, loan_id: str, loan_data: Dict[str, Any]) -> LGDPrediction:
        """
        Predict LGD using two-stage model.
        
        Returns:
            LGDPrediction with recovery rate and LGD
        """
        if not self.load():
            return LGDPrediction(
                loan_id=loan_id,
                p_has_recovery=0.65,
                predicted_recovery_rate=0.17,
                final_recovery_rate=0.11,
                lgd=0.89,
                lgd_pct="89.0%",
                recovery_category="LOW_RECOVERY",
                success=False,
            )
        
        try:
            features = self._prepare_features(loan_data)
            
            # Stage 1: P(has_recovery)
            p_has_recovery = float(self.stage1_model.predict_proba(features)[0, 1])
            
            # Stage 2: Predicted recovery rate
            pred_recovery = float(self.stage2_model.predict(features)[0])
            pred_recovery = max(0.0, min(1.0, pred_recovery))
            
            # Final: Combine
            final_recovery = p_has_recovery * pred_recovery
            lgd = 1.0 - final_recovery
            
            # Categorize
            if final_recovery >= 0.25:
                category = "HIGH_RECOVERY"
            elif final_recovery >= 0.10:
                category = "MODERATE_RECOVERY"
            elif final_recovery >= 0.03:
                category = "LOW_RECOVERY"
            else:
                category = "MINIMAL_RECOVERY"
            
            # Confidence
            confidence = "HIGH" if abs(p_has_recovery - 0.5) > 0.3 else "MEDIUM" if abs(p_has_recovery - 0.5) > 0.1 else "LOW"
            
            return LGDPrediction(
                loan_id=loan_id,
                p_has_recovery=round(p_has_recovery, 4),
                predicted_recovery_rate=round(pred_recovery, 4),
                final_recovery_rate=round(final_recovery, 4),
                lgd=round(lgd, 4),
                lgd_pct=f"{lgd:.1%}",
                recovery_category=category,
                stage1_confidence=confidence,
            )
            
        except Exception as e:
            logger.error(f"LGD prediction error: {e}")
            return LGDPrediction(
                loan_id=loan_id,
                p_has_recovery=0.65,
                predicted_recovery_rate=0.17,
                final_recovery_rate=0.11,
                lgd=0.89,
                lgd_pct="89.0%",
                recovery_category="UNKNOWN",
                success=False,
            )
    
    def explain(self, loan_id: str, loan_data: Dict[str, Any], top_n: int = 5) -> LGDExplanation:
        """Get SHAP explanation for both stages."""
        if not self.load() or not self.stage1_explainer or not self.stage2_explainer:
            return LGDExplanation(loan_id=loan_id, stage1_factors=[], stage2_factors=[], success=False)
        
        try:
            features = self._prepare_features(loan_data)
            
            # Stage 1 SHAP
            shap1 = self.stage1_explainer.shap_values(features)
            if isinstance(shap1, list):
                shap1 = shap1[1]  # Class 1 (has_recovery)
            shap1 = shap1[0]
            
            s1_factors = sorted(
                zip(self.feature_order, shap1, features[0]),
                key=lambda x: abs(x[1]), reverse=True
            )[:top_n]
            
            stage1_factors = [
                {"feature": f, "impact": round(float(s), 4), "value": round(float(v), 2)}
                for f, s, v in s1_factors
            ]
            
            # Stage 2 SHAP
            shap2 = self.stage2_explainer.shap_values(features)[0]
            s2_factors = sorted(
                zip(self.feature_order, shap2, features[0]),
                key=lambda x: abs(x[1]), reverse=True
            )[:top_n]
            
            stage2_factors = [
                {"feature": f, "impact": round(float(s), 4), "value": round(float(v), 2)}
                for f, s, v in s2_factors
            ]
            
            return LGDExplanation(
                loan_id=loan_id,
                stage1_factors=stage1_factors,
                stage2_factors=stage2_factors,
            )
            
        except Exception as e:
            logger.error(f"SHAP explanation error: {e}")
            return LGDExplanation(loan_id=loan_id, stage1_factors=[], stage2_factors=[], success=False)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and metrics."""
        if not self.load():
            return {"success": False, "error": "Model not loaded"}
        
        metrics = {}
        if METRICS_PATH.exists():
            with open(METRICS_PATH, "r") as f:
                metrics = json.load(f)
        
        return {
            "success": True,
            "model_type": "Two-Stage LGD",
            "version": "2.0.0",
            "stage1": {
                "type": "LightGBM Classifier",
                "target": "has_recovery",
                "auc": metrics.get("stage1_classifier", {}).get("test_auc", "N/A"),
            },
            "stage2": {
                "type": "LightGBM Regressor",
                "target": "recovery_rate",
                "mae": metrics.get("stage2_regressor", {}).get("test_mae", "N/A"),
            },
            "combined_mae": metrics.get("stage2_regressor", {}).get("combined_mae", "N/A"),
            "training_data": "Lending Club 2007-2018 (150K charged-off loans)",
            "formula": "LGD = 1 - (P(has_recovery) × recovery_rate)",
        }


# Singleton instance
_lgd_predictor: Optional[TwoStageLGDPredictor] = None


def get_lgd_predictor() -> TwoStageLGDPredictor:
    """Get singleton LGD predictor."""
    global _lgd_predictor
    if _lgd_predictor is None:
        _lgd_predictor = TwoStageLGDPredictor()
    return _lgd_predictor


# Public API functions
def predict_lgd(loan_id: str, loan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Predict LGD for a loan using two-stage model."""
    predictor = get_lgd_predictor()
    result = predictor.predict(loan_id, loan_data)
    return asdict(result)


def explain_lgd(loan_id: str, loan_data: Dict[str, Any], top_n: int = 5) -> Dict[str, Any]:
    """Get SHAP explanation for LGD prediction."""
    predictor = get_lgd_predictor()
    result = predictor.explain(loan_id, loan_data, top_n)
    return asdict(result)


def get_lgd_model_info() -> Dict[str, Any]:
    """Get LGD model information."""
    predictor = get_lgd_predictor()
    return predictor.get_model_info()
