"""
Visualization tools for dashboards and charts.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def create_status_chart(
    statuses: Dict[str, int],
    title: str = "Covenant Status",
) -> Dict[str, Any]:
    """
    Create status distribution chart data.

    Args:
        statuses: Dictionary of status counts
        title: Chart title

    Returns:
        Chart configuration
    """
    colors = {
        "GREEN": "#22c55e",
        "AMBER": "#f59e0b",
        "RED": "#ef4444",
        "UNKNOWN": "#6b7280",
    }

    total = sum(statuses.values())
    
    chart_data = {
        "type": "pie",
        "title": title,
        "data": [
            {
                "label": status,
                "value": count,
                "percentage": round(count / total * 100, 1) if total > 0 else 0,
                "color": colors.get(status, "#6b7280"),
            }
            for status, count in statuses.items()
        ],
        "total": total,
    }

    return {"success": True, "chart": chart_data}


def create_trend_chart(
    data_points: List[Dict[str, Any]],
    metric_name: str,
    title: str = "Trend Analysis",
) -> Dict[str, Any]:
    """
    Create trend line chart data.

    Args:
        data_points: List of data points with date and value
        metric_name: Name of the metric
        title: Chart title

    Returns:
        Chart configuration
    """
    chart_data = {
        "type": "line",
        "title": title,
        "metric": metric_name,
        "data": data_points,
        "x_axis": "date",
        "y_axis": metric_name,
    }

    # Calculate trend
    if len(data_points) >= 2:
        first_value = data_points[0].get("value", 0)
        last_value = data_points[-1].get("value", 0)
        
        if first_value > 0:
            change_pct = ((last_value - first_value) / first_value) * 100
            chart_data["trend"] = {
                "direction": "up" if change_pct > 0 else "down",
                "change_percentage": round(change_pct, 1),
            }

    return {"success": True, "chart": chart_data}


def create_portfolio_heatmap(
    loans: List[Dict[str, Any]],
    metric: str = "breach_probability",
) -> Dict[str, Any]:
    """
    Create portfolio heatmap data.

    Args:
        loans: List of loan data
        metric: Metric to visualize

    Returns:
        Heatmap configuration
    """
    # Sort loans by metric value
    sorted_loans = sorted(
        loans,
        key=lambda x: x.get(metric, 0),
        reverse=True,
    )

    # Assign colors based on metric thresholds
    heatmap_data = []
    for loan in sorted_loans:
        value = loan.get(metric, 0)
        
        if value >= 0.7:
            color = "#ef4444"  # Red
            risk_level = "HIGH"
        elif value >= 0.4:
            color = "#f59e0b"  # Amber
            risk_level = "MEDIUM"
        else:
            color = "#22c55e"  # Green
            risk_level = "LOW"

        heatmap_data.append({
            "loan_id": loan.get("loan_id", "Unknown"),
            "borrower": loan.get("borrower_name", "Unknown"),
            "value": value,
            "color": color,
            "risk_level": risk_level,
        })

    chart_data = {
        "type": "heatmap",
        "title": f"Portfolio {metric.replace('_', ' ').title()}",
        "metric": metric,
        "data": heatmap_data,
        "high_risk_count": sum(1 for d in heatmap_data if d["risk_level"] == "HIGH"),
        "medium_risk_count": sum(1 for d in heatmap_data if d["risk_level"] == "MEDIUM"),
        "low_risk_count": sum(1 for d in heatmap_data if d["risk_level"] == "LOW"),
    }

    return {"success": True, "chart": chart_data}
