"""
Intelligence Layer for TfL Delay Anomaly Detection.

Transforms raw model predictions into rich, explainable intelligence outputs.
This layer is model-agnostic and works with any prediction probability.
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime
from .explanation_utils import (
    generate_explanation_text,
    calculate_baseline_comparison,
    generate_rolling_summary,
)
from .retrieval_utils import SimilarCaseRetriever


class IntelligenceLayer:
    """
    Transforms model predictions into rich intelligence outputs.
    
    Provides:
    - Risk level classification
    - Rule-based explanations
    - Baseline comparisons
    - Rolling trend analysis
    - Similar historical case retrieval
    - Template-based AI summaries
    """

    # Risk thresholds (configurable)
    RISK_THRESHOLDS = {
        "high": 0.7,
        "medium": 0.3,
    }

    def __init__(self, dataset_parquet_path: str = None):
        """
        Initialize the Intelligence Layer.
        
        Args:
            dataset_parquet_path: Path to historical data parquet file for similarity retrieval.
                                If None, similar case retrieval will be disabled.
        """
        self.retriever = None
        if dataset_parquet_path:
            try:
                self.retriever = SimilarCaseRetriever(dataset_parquet_path)
            except Exception as e:
                print(
                    f"Warning: Could not load dataset for similarity retrieval: {e}"
                )

    def build_intelligence_output(
        self,
        features: Dict[str, Any],
        prob: float,
        baseline: float,
        rolling_stats: Tuple[float, float, int] = None,
    ) -> Dict[str, Any]:
        """
        Build comprehensive intelligence output from prediction and features.
        
        Args:
            features: Feature dictionary from pipeline containing:
                - time_to_station: Current arrival time in seconds
                - baseline_median_tts: Baseline arrival time in seconds
                - roll_mean_tts_10m: Rolling mean over 10 minutes
                - roll_max_tts_10m: Rolling max over 10 minutes
                - roll_count_10m: Count of observations in 10-minute window
                - hour: Hour of day (0-23)
                - weekday: Weekday (0-6, where 5-6 are weekend)
                - is_weekend: Binary weekend indicator
                - stop_id: Station stop ID
                - line_id: Line identifier
                - direction: Travel direction
            
            prob: Risk probability from model (0.0 to 1.0)
            
            baseline: Baseline arrival time in seconds (typically from features)
            
            rolling_stats: Tuple of (mean, max, count) from rolling cache.
                          If None, will use features['roll_mean_tts_10m'], etc.
        
        Returns:
            Dictionary with keys:
                - risk_level: 'LOW', 'MEDIUM', or 'HIGH'
                - risk_probability: Raw probability score
                - explanation_text: Human-readable explanation
                - baseline_comparison: Dict with deviation metrics
                - rolling_summary: Trend analysis and context
                - similar_cases: List of similar historical patterns
                - ai_summary: Template-based narrative summary
                - metadata: Additional context (timestamps, feature flags)
        """
        # Classify risk level
        risk_level = self._classify_risk(prob)

        # Generate rule-based explanation
        explanation_text = generate_explanation_text(
            features=features,
            risk_level=risk_level,
            prob=prob,
        )

        # Calculate baseline comparison metrics
        baseline_comparison = calculate_baseline_comparison(
            current_tts=features["time_to_station"],
            baseline_tts=baseline,
        )

        # Generate rolling statistics summary
        rolling_summary = generate_rolling_summary(
            features=features,
            rolling_stats=rolling_stats,
            baseline=baseline,
        )

        # Retrieve similar historical cases
        similar_cases = self._get_similar_cases(features, prob)

        # Generate AI summary text
        ai_summary = self._generate_ai_summary(
            features=features,
            risk_level=risk_level,
            baseline_comparison=baseline_comparison,
            rolling_summary=rolling_summary,
        )

        return {
            "risk_level": risk_level,
            "risk_probability": float(prob),
            "explanation_text": explanation_text,
            "baseline_comparison": baseline_comparison,
            "rolling_summary": rolling_summary,
            "similar_cases": similar_cases,
            "ai_summary": ai_summary,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "stop_id": features.get("stop_id"),
                "line_id": features.get("line_id"),
                "direction": features.get("direction"),
                "hour": features.get("hour"),
                "weekday": features.get("weekday"),
                "is_weekend": features.get("is_weekend"),
            },
        }

    def _classify_risk(self, prob: float) -> str:
        """
        Classify risk level based on probability threshold.
        
        Args:
            prob: Risk probability (0.0 to 1.0)
        
        Returns:
            Risk level: 'LOW', 'MEDIUM', or 'HIGH'
        """
        if prob >= self.RISK_THRESHOLDS["high"]:
            return "HIGH"
        elif prob >= self.RISK_THRESHOLDS["medium"]:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_similar_cases(
        self,
        features: Dict[str, Any],
        prob: float,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar historical cases based on features.
        
        Args:
            features: Current feature set
            prob: Current risk probability
            top_k: Number of similar cases to return
        
        Returns:
            List of similar historical cases (up to top_k items)
        """
        if not self.retriever:
            return []

        try:
            similar = self.retriever.find_similar_cases(
                stop_id=features.get("stop_id"),
                line_id=features.get("line_id"),
                hour=features.get("hour"),
                weekday=features.get("weekday"),
                current_tts=features.get("time_to_station"),
                baseline_tts=features.get("baseline_median_tts"),
                top_k=top_k,
            )
            return similar
        except Exception as e:
            print(f"Warning: Could not retrieve similar cases: {e}")
            return []

    def _generate_ai_summary(
        self,
        features: Dict[str, Any],
        risk_level: str,
        baseline_comparison: Dict[str, Any],
        rolling_summary: Dict[str, Any],
    ) -> str:
        """
        Generate a template-based AI narrative summary.
        
        Args:
            features: Feature dictionary
            risk_level: Classified risk level
            baseline_comparison: Baseline comparison metrics
            rolling_summary: Rolling statistics summary
        
        Returns:
            Human-readable AI summary text
        """
        stop_name = features.get("stop_name", "Unknown Station")
        line_name = features.get("line_id", "Unknown Line").title()
        direction = features.get("direction", "unknown").title()

        # Risk-specific narratives
        if risk_level == "HIGH":
            template = (
                f"⚠️ High delay risk detected at {stop_name} ({line_name}, {direction}). "
                f"Current arrival time is {baseline_comparison.get('deviation_percent', 0):.0f}% "
                f"above normal. "
            )
            if rolling_summary.get("sustained_elevation"):
                template += "Delays have been elevated for the last 10 minutes. "
            template += (
                f"This pattern suggests potential service disruption. "
                f"Passengers should expect extended waiting times."
            )

        elif risk_level == "MEDIUM":
            template = (
                f"⏱️ Elevated delay risk at {stop_name} ({line_name}, {direction}). "
                f"Arrival time is {baseline_comparison.get('deviation_percent', 0):.0f}% "
                f"above typical levels. "
            )
            if rolling_summary.get("trend_direction") == "increasing":
                template += "Delays appear to be increasing. "
            template += "Passengers may experience some additional wait time."

        else:  # LOW
            template = (
                f"✓ Normal delay risk at {stop_name} ({line_name}, {direction}). "
                f"Service is operating close to baseline. "
                f"Arrival times are within expected range."
            )

        return template

    def get_risk_color(self, risk_level: str) -> str:
        """
        Get color code for risk level (useful for UI).
        
        Args:
            risk_level: Risk level ('LOW', 'MEDIUM', 'HIGH')
        
        Returns:
            Color code string
        """
        color_map = {
            "LOW": "#22c55e",      # Green
            "MEDIUM": "#f59e0b",   # Amber
            "HIGH": "#ef4444",     # Red
        }
        return color_map.get(risk_level, "#6b7280")

    def get_risk_emoji(self, risk_level: str) -> str:
        """
        Get emoji for risk level (useful for UI).
        
        Args:
            risk_level: Risk level ('LOW', 'MEDIUM', 'HIGH')
        
        Returns:
            Emoji string
        """
        emoji_map = {
            "LOW": "✓",
            "MEDIUM": "⏱️",
            "HIGH": "⚠️",
        }
        return emoji_map.get(risk_level, "?")
