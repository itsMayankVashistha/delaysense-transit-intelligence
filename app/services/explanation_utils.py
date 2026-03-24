"""
Explanation utilities for generating rule-based explanations of delay anomalies.

These functions generate human-readable explanations without using LLMs,
based on feature values and statistical deviations.
"""

from typing import Dict, Any, Tuple


def generate_explanation_text(
    features: Dict[str, Any],
    risk_level: str,
    prob: float,
) -> str:
    """
    Generate detailed rule-based explanation of delay risk.
    
    Args:
        features: Feature dictionary from pipeline
        risk_level: Classified risk level ('LOW', 'MEDIUM', 'HIGH')
        prob: Risk probability score
    
    Returns:
        Human-readable explanation text
    """
    current_min = features["time_to_station"] / 60
    baseline_min = features["baseline_median_tts"] / 60
    deviation_percent = (
        (features["time_to_station"] - features["baseline_median_tts"])
        / features["baseline_median_tts"]
        * 100
    )

    explanations = []

    # Main comparison
    if risk_level == "HIGH":
        explanations.append(
            f"Current arrival estimate is {current_min:.1f} minutes, "
            f"significantly above the usual {baseline_min:.1f} minutes "
            f"for this time and location."
        )
        explanations.append(
            f"Deviation: {deviation_percent:+.0f}% from baseline."
        )

    elif risk_level == "MEDIUM":
        explanations.append(
            f"Current arrival estimate is {current_min:.1f} minutes, "
            f"compared with a typical {baseline_min:.1f} minutes."
        )
        explanations.append(
            f"Moderate elevation: {deviation_percent:+.0f}% above baseline."
        )

    else:  # LOW
        explanations.append(
            f"Current arrival estimate is {current_min:.1f} minutes, "
            f"close to the usual {baseline_min:.1f} minutes."
        )
        explanations.append("Service is operating at normal speed.")

    # Rolling window analysis
    roll_mean = features.get("roll_mean_tts_10m", 0)
    if roll_mean > 0:
        roll_mean_min = roll_mean / 60
        roll_deviation_percent = (
            (roll_mean - features["baseline_median_tts"])
            / features["baseline_median_tts"]
            * 100
        )

        if roll_mean > features["baseline_median_tts"] * 1.3:
            explanations.append(
                f"Rolling 10-minute average is {roll_mean_min:.1f} minutes "
                f"({roll_deviation_percent:+.0f}% deviation). "
                "Pattern sustained over recent period."
            )
        elif roll_mean > features["baseline_median_tts"] * 1.1:
            explanations.append(
                f"Rolling average shows mild elevation at {roll_mean_min:.1f} minutes."
            )

    # Time-of-day context
    hour = features.get("hour", -1)
    if hour != -1:
        if 7 <= hour < 10:
            explanations.append("During morning peak hours (7-10 AM).")
        elif 17 <= hour < 20:
            explanations.append("During evening peak hours (5-8 PM).")
        elif 22 <= hour or hour < 5:
            explanations.append("During late night/early morning (off-peak).")

    # Weekend context
    if features.get("is_weekend"):
        explanations.append("Operating on weekend.")

    # Rolling max analysis
    roll_max = features.get("roll_max_tts_10m", 0)
    if roll_max > 0 and risk_level == "HIGH":
        roll_max_min = roll_max / 60
        explanations.append(
            f"Peak wait in recent window: {roll_max_min:.1f} minutes."
        )

    return " ".join(explanations)


def calculate_baseline_comparison(
    current_tts: float,
    baseline_tts: float,
) -> Dict[str, Any]:
    """
    Calculate detailed baseline comparison metrics.
    
    Args:
        current_tts: Current time to station (seconds)
        baseline_tts: Baseline time to station (seconds)
    
    Returns:
        Dictionary with comparison metrics
    """
    absolute_deviation = current_tts - baseline_tts
    deviation_percent = (absolute_deviation / baseline_tts) * 100 if baseline_tts > 0 else 0

    # Classify deviation severity
    if deviation_percent >= 50:
        severity = "critical"
    elif deviation_percent >= 30:
        severity = "elevated"
    elif deviation_percent >= 10:
        severity = "mild"
    else:
        severity = "normal"

    return {
        "current_minutes": round(current_tts / 60, 1),
        "baseline_minutes": round(baseline_tts / 60, 1),
        "absolute_deviation_minutes": round(absolute_deviation / 60, 1),
        "deviation_percent": round(deviation_percent, 1),
        "severity": severity,
        "ratio": round(current_tts / baseline_tts, 2) if baseline_tts > 0 else 0,
    }


def generate_rolling_summary(
    features: Dict[str, Any],
    rolling_stats: Tuple[float, float, int] = None,
    baseline: float = None,
) -> Dict[str, Any]:
    """
    Generate rolling window statistics summary and trend analysis.
    
    Args:
        features: Feature dictionary (contains roll_mean_tts_10m, roll_max_tts_10m, roll_count_10m)
        rolling_stats: Tuple of (mean, max, count) from cache. If provided, overrides features values.
        baseline: Baseline time to station for context. If None, uses features baseline.
    
    Returns:
        Dictionary with rolling window analysis
    """
    # Extract rolling stats
    if rolling_stats:
        roll_mean, roll_max, roll_count = rolling_stats
    else:
        roll_mean = features.get("roll_mean_tts_10m", 0)
        roll_max = features.get("roll_max_tts_10m", 0)
        roll_count = features.get("roll_count_10m", 0)

    if not baseline:
        baseline = features.get("baseline_median_tts", 300)

    # Analyze trend
    current_tts = features.get("time_to_station", 0)
    if roll_mean > 0:
        if current_tts > roll_mean * 1.1:
            trend_direction = "increasing"
            trend_text = "Delays are getting worse."
        elif current_tts < roll_mean * 0.9:
            trend_direction = "decreasing"
            trend_text = "Delays are improving."
        else:
            trend_direction = "stable"
            trend_text = "Delays are stable."
    else:
        trend_direction = "unknown"
        trend_text = "Insufficient data for trend analysis."

    # Check if elevation is sustained
    sustained_elevation = (
        roll_mean > baseline * 1.2
        and roll_count >= 3
    )

    return {
        "window_duration_minutes": 10,
        "observations_in_window": int(roll_count),
        "mean_tts_minutes": round(roll_mean / 60, 1) if roll_mean > 0 else 0,
        "max_tts_minutes": round(roll_max / 60, 1) if roll_max > 0 else 0,
        "mean_deviation_percent": (
            round(((roll_mean - baseline) / baseline) * 100, 1)
            if roll_mean > 0 and baseline > 0
            else 0
        ),
        "trend_direction": trend_direction,
        "trend_text": trend_text,
        "sustained_elevation": sustained_elevation,
        "data_quality": _assess_data_quality(roll_count),
    }


def _assess_data_quality(observation_count: int) -> str:
    """
    Assess quality of rolling window data based on observation count.
    
    Args:
        observation_count: Number of observations in rolling window
    
    Returns:
        Quality assessment string
    """
    if observation_count == 0:
        return "no_data"
    elif observation_count < 2:
        return "minimal"
    elif observation_count < 5:
        return "moderate"
    else:
        return "good"


def get_feature_importance_summary(
    features: Dict[str, Any],
) -> Dict[str, str]:
    """
    Generate summary of which features are driving risk.
    
    Args:
        features: Feature dictionary
    
    Returns:
        Dictionary mapping feature names to importance descriptions
    """
    importance = {}

    current_tts = features.get("time_to_station", 0)
    baseline = features.get("baseline_median_tts", 300)

    # Check which features suggest high risk
    deviation_percent = ((current_tts - baseline) / baseline * 100) if baseline > 0 else 0

    if deviation_percent > 30:
        importance["time_to_station"] = f"Very high ({deviation_percent:.0f}% above baseline)"

    roll_mean = features.get("roll_mean_tts_10m", 0)
    if roll_mean > baseline * 1.3:
        deviation = ((roll_mean - baseline) / baseline * 100)
        importance["rolling_mean"] = f"Sustained elevation ({deviation:.0f}% above baseline)"

    roll_max = features.get("roll_max_tts_10m", 0)
    if roll_max > baseline * 1.5:
        deviation = ((roll_max - baseline) / baseline * 100)
        importance["rolling_max"] = f"Peak spike ({deviation:.0f}% above baseline)"

    hour = features.get("hour", -1)
    if hour in [8, 9, 17, 18]:
        importance["hour_of_day"] = "During peak hours"

    if features.get("is_weekend"):
        importance["weekday"] = "Weekend operation"

    return importance
