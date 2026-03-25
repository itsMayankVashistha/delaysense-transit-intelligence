from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys
import pandas as pd
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from app.services.artifact_loader import load_model_artifact


REQUIRED_FEATURES = [
    "hour",
    "weekday",
    "is_weekend",
    "time_to_station",
    "roll_mean_tts_10m",
    "roll_max_tts_10m",
    "roll_count_10m",
    "baseline_median_tts",
    "deviation_from_baseline",
]


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(1)


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path", type=str, help="Path to .joblib artifact")
    args = parser.parse_args()

    model_path = Path(args.model_path)
    if not model_path.exists():
        fail(f"Model file not found: {model_path}")

    artifact = load_model_artifact(model_path)

    print("\n=== Artifact Summary ===")
    print(f"path: {artifact.source_path}")
    print(f"artifact_type: {artifact.artifact_type}")
    print(f"model_name: {artifact.model_name}")
    print(f"model_family: {artifact.model_family}")
    print(f"mode_name: {artifact.mode_name}")
    print(f"threshold: {artifact.threshold}")
    print(f"horizon_seconds: {artifact.horizon_seconds}")
    print(f"input_type: {artifact.input_type}")
    print(f"positive_class_index: {artifact.positive_class_index}")
    print(f"predict_method: {artifact.predict_method}")
    print(f"features: {artifact.features}")

    if artifact.predict_method != "predict_proba":
        fail(f"predict_method is '{artifact.predict_method}', expected 'predict_proba'")
    ok("predict method is predict_proba")

    if not hasattr(artifact.model_object, "predict_proba"):
        fail("model object does not expose predict_proba")
    ok("model object exposes predict_proba")

    if artifact.horizon_seconds is None:
        warn("horizon_seconds missing")
    elif int(artifact.horizon_seconds) != 300:
        warn(f"horizon_seconds is {artifact.horizon_seconds}, expected 300 for current deployment")
    else:
        ok("horizon is 300 seconds")

    target_name = artifact.metadata.get("target_name")
    if not target_name:
        warn("target_name missing in metadata")
    else:
        print(f"target_name: {target_name}")
        if "future" not in target_name:
            warn("target_name does not look like Path B future target")
        else:
            ok("target_name looks Path B compatible")

    if not artifact.features:
        fail("No feature list available from metadata/features/payload")

    if artifact.features != REQUIRED_FEATURES:
        warn("Feature order does not exactly match current deployment expectation")
        print("Expected:", REQUIRED_FEATURES)
        print("Received:", artifact.features)
    else:
        ok("feature order matches current deployment contract")

    validation_path = model_path.with_suffix(".validation_examples.csv")
    if validation_path.exists():
        ok(f"validation examples found: {validation_path}")
        val_df = pd.read_csv(validation_path)

        missing = [c for c in artifact.features if c not in val_df.columns]
        if missing:
            fail(f"validation_examples.csv missing required feature columns: {missing}")

        X = val_df[artifact.features].copy()

        try:
            proba = artifact.predict_proba(X)
        except Exception as e:
            fail(f"predict_proba failed on validation examples: {e}")

        if len(proba.shape) != 2 or proba.shape[1] < 2:
            fail(f"predict_proba output has unexpected shape: {proba.shape}")

        positive_idx = artifact.positive_class_index
        out = proba[:, positive_idx]

        print("\n=== Validation Example Predictions ===")
        print(pd.DataFrame({
            "expected_proba": val_df.get("expected_proba"),
            "predicted_proba": out,
        }).head(10).to_string(index=False))

        if "expected_proba" in val_df.columns:
            diff = (val_df["expected_proba"] - out).abs().max()
            print(f"max_abs_diff_vs_expected: {diff:.10f}")
            if diff > 1e-6:
                warn("Predicted probabilities differ from provided expected_proba")
            else:
                ok("Predicted probabilities match validation examples")
    else:
        warn("validation_examples.csv not found")

    print("\n=== Final Verdict ===")
    print("Artifact can be integrated if warnings are understood and acceptable.")


if __name__ == "__main__":
    main()