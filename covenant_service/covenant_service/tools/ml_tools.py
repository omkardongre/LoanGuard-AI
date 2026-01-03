"""
Machine learning tools for breach prediction with SHAP explanations.

Based on patterns from EnergyAgentAI's ML implementation.
"""

import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from covenant_service.covenant_service.config import (
    BREACH_MODEL_PATH,
    SHAP_BASE_VALUES_PATH,
)

logger = logging.getLogger(__name__)

# Feature definitions for breach prediction
BREACH_FEATURES = [
    "debt_to_ebitda_ratio",
    "interest_coverage_ratio",
    "current_ratio",
    "revenue_growth_yoy",
    "ebitda_margin",
    "debt_growth_yoy",
    "days_to_maturity",
    "previous_breaches",
    "industry_risk_score",
    "economic_cycle_indicator",
]


def predict_breach_probability(
    loan_id: str,
    financial_metrics: Dict[str, float],
    use_mock: bool = True,
) -> Dict[str, Any]:
    """
    Predict probability of covenant breach using XGBoost model.

    Args:
        loan_id: Loan identifier
        financial_metrics: Dictionary of financial metrics
        use_mock: Use mock prediction if model not available

    Returns:
        Prediction result with probability
    """
    try:
        # Prepare features
        features = _prepare_features(financial_metrics)
        
        if not use_mock:
            try:
                import xgboost as xgb
                import pickle
                
                model_path = Path(BREACH_MODEL_PATH)
                if model_path.exists():
                    with open(model_path, "rb") as f:
                        model = pickle.load(f)
                    
                    feature_array = np.array([features])
                    probability = float(model.predict_proba(feature_array)[0][1])
                else:
                    logger.warning(f"Model not found at {model_path}, using mock")
                    probability = _mock_prediction(features)
            except ImportError:
                logger.warning("XGBoost not installed, using mock prediction")
                probability = _mock_prediction(features)
        else:
            probability = _mock_prediction(features)

        # Determine risk level
        if probability >= 0.7:
            risk_level = "HIGH"
        elif probability >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "success": True,
            "loan_id": loan_id,
            "breach_probability": round(probability, 4),
            "breach_probability_pct": f"{probability:.1%}",
            "risk_level": risk_level,
            "prediction_horizon": "90 days",
            "model_version": "1.0.0",
            "features_used": list(financial_metrics.keys()),
        }
    except Exception as e:
        logger.error(f"Breach prediction error: {e}")
        return {"success": False, "error": str(e)}


def get_shap_explanation(
    loan_id: str,
    financial_metrics: Dict[str, float],
    top_n: int = 5,
) -> Dict[str, Any]:
    """
    Get SHAP explanation for breach prediction.

    Args:
        loan_id: Loan identifier
        financial_metrics: Dictionary of financial metrics
        top_n: Number of top features to explain

    Returns:
        SHAP explanation with feature contributions
    """
    try:
        features = _prepare_features(financial_metrics)
        
        # Generate mock SHAP values based on feature importance
        shap_values = _mock_shap_values(features, financial_metrics)
        
        # Sort by absolute SHAP value
        sorted_features = sorted(
            shap_values.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )[:top_n]

        explanations = []
        for feature_name, shap_value in sorted_features:
            feature_value = financial_metrics.get(feature_name, 0)
            direction = "increases" if shap_value > 0 else "decreases"
            
            explanations.append({
                "feature": feature_name,
                "value": feature_value,
                "shap_value": round(shap_value, 4),
                "impact": direction,
                "explanation": _generate_explanation(feature_name, feature_value, shap_value),
            })

        return {
            "success": True,
            "loan_id": loan_id,
            "explanation_type": "SHAP",
            "top_factors": explanations,
            "base_value": 0.3,  # Base probability before features
            "total_features_analyzed": len(financial_metrics),
        }
    except Exception as e:
        logger.error(f"SHAP explanation error: {e}")
        return {"success": False, "error": str(e)}


def get_feature_importance(
    model_type: str = "breach_predictor",
) -> Dict[str, Any]:
    """
    Get global feature importance from the model.

    Args:
        model_type: Type of model

    Returns:
        Feature importance rankings
    """
    # Mock feature importance based on domain knowledge
    importance = {
        "debt_to_ebitda_ratio": 0.25,
        "interest_coverage_ratio": 0.20,
        "ebitda_margin": 0.15,
        "revenue_growth_yoy": 0.12,
        "current_ratio": 0.08,
        "previous_breaches": 0.07,
        "debt_growth_yoy": 0.05,
        "industry_risk_score": 0.04,
        "days_to_maturity": 0.02,
        "economic_cycle_indicator": 0.02,
    }

    ranked = sorted(importance.items(), key=lambda x: x[1], reverse=True)

    return {
        "success": True,
        "model_type": model_type,
        "feature_importance": [
            {"feature": f, "importance": round(i, 4), "rank": idx + 1}
            for idx, (f, i) in enumerate(ranked)
        ],
    }


def generate_risk_score(
    breach_probability: float,
    compliance_status: Dict[str, Any],
    historical_breaches: int = 0,
) -> Dict[str, Any]:
    """
    Generate composite risk score on 0-100 scale.

    Args:
        breach_probability: Predicted breach probability
        compliance_status: Current compliance status dict
        historical_breaches: Number of past breaches

    Returns:
        Risk score with breakdown
    """
    try:
        # Component scores (0-100)
        probability_score = breach_probability * 100
        
        # Status score based on colors
        status_scores = {"GREEN": 0, "AMBER": 50, "RED": 100}
        status = compliance_status.get("overall_status", "GREEN")
        status_score = status_scores.get(status, 50)
        
        # History score
        history_score = min(historical_breaches * 20, 100)
        
        # Weighted composite
        weights = {"probability": 0.5, "status": 0.3, "history": 0.2}
        composite = (
            probability_score * weights["probability"] +
            status_score * weights["status"] +
            history_score * weights["history"]
        )

        # Determine risk category
        if composite >= 70:
            category = "HIGH RISK"
        elif composite >= 40:
            category = "MODERATE RISK"
        else:
            category = "LOW RISK"

        return {
            "success": True,
            "risk_score": round(composite, 1),
            "risk_category": category,
            "components": {
                "probability_component": round(probability_score, 1),
                "status_component": round(status_score, 1),
                "history_component": round(history_score, 1),
            },
            "weights": weights,
            "recommendation": _get_risk_recommendation(category),
        }
    except Exception as e:
        logger.error(f"Risk score generation error: {e}")
        return {"success": False, "error": str(e)}


def _prepare_features(metrics: Dict[str, float]) -> List[float]:
    """Prepare feature array for model input."""
    return [metrics.get(f, 0) for f in BREACH_FEATURES]


def _mock_prediction(features: List[float]) -> float:
    """Generate mock prediction based on features."""
    # Simple heuristic based on key ratios
    debt_ebitda = features[0] if len(features) > 0 else 3.0
    interest_coverage = features[1] if len(features) > 1 else 3.0
    
    # Higher debt/EBITDA increases breach probability
    base_prob = 0.2
    if debt_ebitda > 5:
        base_prob += 0.4
    elif debt_ebitda > 4:
        base_prob += 0.2
    elif debt_ebitda > 3:
        base_prob += 0.1
    
    # Lower interest coverage increases breach probability
    if interest_coverage < 1.5:
        base_prob += 0.3
    elif interest_coverage < 2.0:
        base_prob += 0.15
    
    return min(base_prob, 0.95)


def _mock_shap_values(features: List[float], metrics: Dict[str, float]) -> Dict[str, float]:
    """Generate mock SHAP values."""
    shap_values = {}
    
    # Key features with domain-based impact
    if metrics.get("debt_to_ebitda_ratio", 0) > 4:
        shap_values["debt_to_ebitda_ratio"] = 0.15
    else:
        shap_values["debt_to_ebitda_ratio"] = -0.05
    
    if metrics.get("interest_coverage_ratio", 0) < 2:
        shap_values["interest_coverage_ratio"] = 0.12
    else:
        shap_values["interest_coverage_ratio"] = -0.08
    
    if metrics.get("ebitda_margin", 0) < 0.1:
        shap_values["ebitda_margin"] = 0.08
    else:
        shap_values["ebitda_margin"] = -0.05
    
    if metrics.get("revenue_growth_yoy", 0) < 0:
        shap_values["revenue_growth_yoy"] = 0.06
    else:
        shap_values["revenue_growth_yoy"] = -0.03
    
    if metrics.get("previous_breaches", 0) > 0:
        shap_values["previous_breaches"] = 0.1
    else:
        shap_values["previous_breaches"] = -0.02
    
    return shap_values


def _generate_explanation(feature: str, value: float, shap_value: float) -> str:
    """Generate human-readable explanation for SHAP value."""
    direction = "increases" if shap_value > 0 else "decreases"
    impact = "significantly" if abs(shap_value) > 0.1 else "moderately"
    
    explanations = {
        "debt_to_ebitda_ratio": f"Debt/EBITDA of {value:.1f}x {impact} {direction} breach risk",
        "interest_coverage_ratio": f"Interest coverage of {value:.1f}x {impact} {direction} breach risk",
        "ebitda_margin": f"EBITDA margin of {value:.1%} {impact} {direction} breach risk",
        "revenue_growth_yoy": f"Revenue growth of {value:.1%} {impact} {direction} breach risk",
        "previous_breaches": f"{int(value)} previous breach(es) {impact} {direction} future risk",
    }
    
    return explanations.get(
        feature,
        f"{feature} value of {value} {impact} {direction} breach risk"
    )


def _get_risk_recommendation(category: str) -> str:
    """Get recommendation based on risk category."""
    recommendations = {
        "HIGH RISK": "Immediate review required. Consider covenant waiver or amendment discussions.",
        "MODERATE RISK": "Enhanced monitoring recommended. Schedule borrower review within 30 days.",
        "LOW RISK": "Standard monitoring sufficient. Continue quarterly reviews.",
    }
    return recommendations.get(category, "Review risk factors and monitoring frequency.")
