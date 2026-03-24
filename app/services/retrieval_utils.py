"""
Similarity retrieval utilities for finding related historical delay patterns.

Searches historical dataset for cases with similar characteristics
to provide context and historical precedent for current predictions.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path


class SimilarCaseRetriever:
    """
    Retrieves historical cases similar to current prediction.
    
    Uses feature matching and similarity metrics to find relevant
    historical delay patterns that can provide context and insights.
    """

    def __init__(self, dataset_parquet_path: str):
        """
        Initialize retriever with historical dataset.
        
        Args:
            dataset_parquet_path: Path to parquet file with historical data.
                                 Must contain columns: stop_id, line_id, hour, weekday, time_to_station, baseline_median_tts
        
        Raises:
            FileNotFoundError: If dataset file doesn't exist
            ValueError: If required columns are missing
        """
        path = Path(dataset_parquet_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Dataset not found at {dataset_parquet_path}"
            )

        self.df = pd.read_parquet(path)

        # Validate required columns
        required_cols = {
            "stop_id",
            "line_id",
            "hour",
            "weekday",
            "time_to_station",
        }
        missing = required_cols - set(self.df.columns)
        if missing:
            raise ValueError(
                f"Dataset missing required columns: {missing}"
            )

        print(
            f"Loaded {len(self.df)} historical records for similarity retrieval"
        )

    def find_similar_cases(
        self,
        stop_id: str,
        line_id: str,
        hour: int,
        weekday: int,
        current_tts: float,
        baseline_tts: float,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find historical cases similar to current conditions.
        
        Searches for records with:
        - Same stop and line
        - Same or similar hour
        - Same or similar weekday
        - Similar delay departure (time_to_station relative to baseline)
        
        Args:
            stop_id: Current station stop ID
            line_id: Current line ID
            hour: Current hour of day (0-23)
            weekday: Current weekday (0-6)
            current_tts: Current time to station (seconds)
            baseline_tts: Baseline time to station (seconds)
            top_k: Maximum number of results to return
        
        Returns:
            List of similar historical cases (dict), up to top_k items
        """
        candidates = self.df.copy()

        # Mandatory filters: stop and line
        candidates = candidates[
            (candidates["stop_id"] == stop_id)
            & (candidates["line_id"] == line_id)
        ]

        if len(candidates) == 0:
            # Fallback to same line if no stop+line match
            candidates = self.df[self.df["line_id"] == line_id].copy()

        if len(candidates) == 0:
            return []

        # Calculate similarity metrics for each candidate
        candidates["similarity_score"] = candidates.apply(
            lambda row: self._calculate_similarity(
                row_hour=row.get("hour", hour),
                row_weekday=row.get("weekday", weekday),
                row_tts=row.get("time_to_station", 0),
                current_hour=hour,
                current_weekday=weekday,
                current_tts=current_tts,
                baseline_tts=baseline_tts,
            ),
            axis=1,
        )

        # Sort by similarity and get top k
        candidates = candidates.nlargest(top_k, "similarity_score")

        # Format results
        results = []
        for _, row in candidates.iterrows():
            result = {
                "stop_id": row.get("stop_id", "unknown"),
                "line_id": row.get("line_id", "unknown"),
                "hour": int(row.get("hour", -1)),
                "weekday": int(row.get("weekday", -1)),
                "time_to_station_minutes": round(
                    row.get("time_to_station", 0) / 60, 1
                ),
                "baseline_minutes": round(
                    row.get("baseline_median_tts", 300) / 60, 1
                ),
                "deviation_percent": round(
                    self._calculate_deviation_percent(
                        row.get("time_to_station", 0),
                        row.get("baseline_median_tts", 300),
                    ),
                    1,
                ),
                "similarity_score": float(row["similarity_score"]),
            }

            # Add optional fields if available
            if "destination_name" in row and pd.notna(row["destination_name"]):
                result["destination"] = str(row["destination_name"])
            if "platform_name" in row and pd.notna(row["platform_name"]):
                result["platform"] = str(row["platform_name"])
            if "timestamp" in row and pd.notna(row["timestamp"]):
                result["timestamp"] = str(row["timestamp"])

            results.append(result)

        return results

    def _calculate_similarity(
        self,
        row_hour: int,
        row_weekday: int,
        row_tts: float,
        current_hour: int,
        current_weekday: int,
        current_tts: float,
        baseline_tts: float,
    ) -> float:
        """
        Calculate similarity score between historical and current case.
        
        Factors:
        - Hour similarity (exact match highest)
        - Weekday similarity (exact match for weekday category)
        - Time-to-station pattern (similar deviation from baseline)
        
        Args:
            row_hour: Historical hour
            row_weekday: Historical weekday
            row_tts: Historical time to station
            current_hour: Current hour
            current_weekday: Current weekday
            current_tts: Current time to station
            baseline_tts: Baseline time to station
        
        Returns:
            Similarity score (0.0 to 1.0)
        """
        score = 0.0

        # Hour similarity (0-0.4 points)
        hour_diff = abs(row_hour - current_hour)
        if hour_diff == 0:
            score += 0.4
        elif hour_diff <= 2:
            score += 0.3
        elif hour_diff <= 4:
            score += 0.2
        else:
            score += 0.1

        # Weekday similarity (0-0.3 points)
        # Group into weekday vs weekend
        row_is_weekend = row_weekday >= 5
        current_is_weekend = current_weekday >= 5

        if row_is_weekend == current_is_weekend:
            if row_weekday == current_weekday:
                score += 0.3  # Exact match
            else:
                score += 0.2  # Same category
        else:
            score += 0.1  # Different category

        # Time-to-station pattern similarity (0-0.3 points)
        if baseline_tts > 0 and row_tts > 0:
            row_deviation = (row_tts - baseline_tts) / baseline_tts
            current_deviation = (current_tts - baseline_tts) / baseline_tts

            # Lower deviation difference = higher similarity
            deviation_diff = abs(row_deviation - current_deviation)
            if deviation_diff < 0.1:
                score += 0.3
            elif deviation_diff < 0.2:
                score += 0.25
            elif deviation_diff < 0.4:
                score += 0.2
            elif deviation_diff < 0.6:
                score += 0.15
            else:
                score += 0.05

        return min(score, 1.0)

    @staticmethod
    def _calculate_deviation_percent(tts: float, baseline: float) -> float:
        """
        Calculate deviation from baseline as percentage.
        
        Args:
            tts: Time to station (seconds)
            baseline: Baseline time to station (seconds)
        
        Returns:
            Deviation percentage
        """
        if baseline <= 0:
            return 0.0
        return ((tts - baseline) / baseline) * 100
