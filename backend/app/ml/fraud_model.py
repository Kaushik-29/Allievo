"""
Fraud Model — Section 9.2
Phase 1: Isolation Forest for unsupervised anomaly detection.
Phase 2: LightGBM classifier with labeled outcomes.
"""
import logging
import pickle
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "artifacts" / "fraud_model.pkl"
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


class FraudModel:
    """
    Phase 1: Isolation Forest on 8 numerical features.
    Maps anomaly score to [0, 1] fraud probability.
    """

    FEATURE_NAMES = [
        "gps_trajectory_score",
        "platform_activity_score",
        "zone_presence_score",     # inverted: 0 = high suspicion
        "device_fp_match",         # 0 / 1
        "cell_tower_match",        # 0 / 1
        "accelerometer_score",
        "claim_freq_ratio",
        "loyalty_weeks_normalized", # loyalty_weeks / 52
    ]

    def __init__(self):
        self.model = None
        self._load_or_train()

    def _load_or_train(self):
        if MODEL_PATH.exists():
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                logger.info("Fraud model loaded from disk")
                return
            except Exception as e:
                logger.warning(f"Model load failed: {e}, retraining...")

        self._train_synthetic()

    def _generate_synthetic_profiles(self, n: int = 3000):
        """Generate synthetic fraud/legitimate profiles for Phase 1 training."""
        rng = np.random.default_rng(42)

        # Legitimate profiles (80%)
        n_legit = int(n * 0.8)
        legit = np.column_stack([
            rng.uniform(0.0, 0.25, n_legit),   # gps_trajectory_score (low suspicion)
            rng.uniform(0.0, 0.40, n_legit),   # platform_activity_score
            rng.uniform(0.4, 1.0, n_legit),    # zone_presence_score
            rng.integers(0, 2, n_legit),        # device_fp_match
            rng.integers(0, 2, n_legit),        # cell_tower_match
            rng.uniform(0.0, 0.3, n_legit),    # accelerometer_score
            rng.uniform(0.1, 0.8, n_legit),    # claim_freq_ratio
            rng.uniform(0.0, 0.5, n_legit),    # loyalty_weeks_normalized
        ])

        # Fraud profiles (20%)
        n_fraud = n - n_legit
        fraud = np.column_stack([
            rng.uniform(0.5, 1.0, n_fraud),    # high gps_trajectory_score
            rng.uniform(0.6, 1.0, n_fraud),    # high platform_activity_score (no activity)
            rng.uniform(0.0, 0.1, n_fraud),    # very low zone_presence
            rng.integers(0, 2, n_fraud),
            np.zeros(n_fraud),                  # cell tower mismatch
            rng.uniform(0.5, 1.0, n_fraud),    # high accelerometer suspicion
            rng.uniform(0.8, 1.0, n_fraud),    # high claim frequency
            rng.uniform(0.0, 0.1, n_fraud),    # very low loyalty
        ])

        return np.vstack([legit, fraud])

    def _train_synthetic(self):
        try:
            from sklearn.ensemble import IsolationForest

            X = self._generate_synthetic_profiles(3000)
            self.model = IsolationForest(
                n_estimators=200,
                contamination=0.20,
                random_state=42,
                n_jobs=-1,
            )
            self.model.fit(X)
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(self.model, f)
            logger.info("Fraud Isolation Forest trained on synthetic data and saved")
        except ImportError:
            logger.warning("sklearn not available — using scoring fallback")
            self.model = None

    def train(self, X: np.ndarray):
        """Retrain Isolation Forest (Phase 1) or replace with LightGBM (Phase 2)."""
        from sklearn.ensemble import IsolationForest
        self.model = IsolationForest(n_estimators=200, contamination=0.20, random_state=42)
        self.model.fit(X)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)

    def predict_score(self, features_dict: dict) -> float:
        """
        Returns fraud score 0.0–1.0.
        Isolation Forest returns -1 (anomaly) or 1 (normal).
        decision_function returns negative = more anomalous.
        We map to [0, 1] where 1.0 = max fraud.
        """
        if self.model is None:
            return self._fallback_score(features_dict)

        row = np.array([[features_dict.get(f, 0.5) for f in self.FEATURE_NAMES]])
        try:
            score = self.model.decision_function(row)[0]
            # Typical range: -0.5 to 0.5; map to [0, 1] with inversion
            fraud_score = 1.0 - (score + 0.5)  # higher anomaly = higher score
            return float(np.clip(fraud_score, 0.0, 1.0))
        except Exception:
            return self._fallback_score(features_dict)

    def apply_baseline_adjustment(self, score: float, adjustment: float) -> float:
        """Apply downward baseline adjustment for workers with repeat false positives."""
        return max(0.0, score - adjustment)

    def _fallback_score(self, features_dict: dict) -> float:
        """Simple weighted scoring fallback when model unavailable."""
        gps = features_dict.get("gps_trajectory_score", 0.3)
        activity = features_dict.get("platform_activity_score", 0.3)
        zone = 1.0 - features_dict.get("zone_presence_score", 0.5)
        device = 0.0 if features_dict.get("device_fp_match", 1) else 0.5
        tower = 0.0 if features_dict.get("cell_tower_match", 1) else 0.5
        return round(
            0.25 * gps + 0.25 * activity + 0.20 * zone + 0.15 * tower + 0.15 * device, 4
        )
