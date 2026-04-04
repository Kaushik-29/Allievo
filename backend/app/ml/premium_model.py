"""
Premium Model — Section 9.1
Phase 1: XGBoost trained on synthetic data from PremiumEngine formulas.
Includes SHAP-based plain-language explanations.
"""
import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "artifacts" / "premium_model.pkl"
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


class PremiumModel:
    """
    XGBoost regressor predicting optimal weekly premium per worker.
    Phase 1: trained on synthetic data from PremiumEngine formula.
    """

    FEATURE_NAMES = [
        "zone_risk_multiplier",
        "seasonal_factor",
        "hist_risk_score",
        "weather_risk",
        "aqi_risk",
        "traffic_risk",
        "live_event_risk",
        "loyalty_weeks",
        "tier_encoded",       # 0=basic, 1=standard, 2=premium
        "dae_normalized",     # DAE / 2000
    ]

    def __init__(self):
        self.model = None
        self._load_or_train()

    def _load_or_train(self):
        if MODEL_PATH.exists():
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                logger.info("Premium model loaded from disk")
                return
            except Exception as e:
                logger.warning(f"Model load failed: {e}, retraining...")

        self._train_synthetic()

    def _generate_synthetic_data(self, n: int = 5000) -> tuple:
        """Generate synthetic training data from PremiumEngine formulas."""
        from app.services.premium_engine import PremiumEngine
        pe = PremiumEngine()

        rng = np.random.default_rng(42)
        X_rows, y_rows = [], []

        for _ in range(n):
            zmr = rng.uniform(0.8, 1.8)
            seasonal = rng.choice([1.0, 1.2, 1.35, 1.4])
            hist = rng.uniform(0, 1)
            weather = rng.uniform(0, 1)
            aqi = rng.uniform(0, 1)
            traffic = rng.uniform(0, 1)
            events = rng.choice([0.0, 0.5, 1.0])
            loyalty = int(rng.integers(0, 25))
            tier = rng.choice(["basic", "standard", "premium"])
            dae = rng.uniform(200, 2000)

            tier_enc = {"basic": 0, "standard": 1, "premium": 2}[tier]
            sbp = pe.static_base_premium(zmr, tier, loyalty, seasonal)
            risk_score_data = pe.compute_risk_score(
                int(hist * 365), weather, 1.0, aqi * 500, (1 - traffic) * 25, events
            )
            rs = risk_score_data["risk_score"]
            wp = pe.weekly_premium(sbp, rs, loyalty)

            X_rows.append([zmr, seasonal, hist, weather, aqi, traffic, events, loyalty, tier_enc, dae / 2000])
            y_rows.append(wp)

        return np.array(X_rows), np.array(y_rows)

    def _train_synthetic(self):
        """Train XGBoost on synthetic data."""
        try:
            import xgboost as xgb

            X, y = self._generate_synthetic_data(5000)
            self.model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
            )
            self.model.fit(X, y)
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(self.model, f)
            logger.info("Premium model trained on synthetic data and saved")
        except ImportError:
            logger.warning("XGBoost not available — using formula fallback")
            self.model = None

    def train(self, X: np.ndarray, y: np.ndarray):
        """Retrain on real data (Phase 2)."""
        import xgboost as xgb
        self.model = xgb.XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42)
        self.model.fit(X, y)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)

    def predict(self, features_dict: dict) -> float:
        """Predict weekly premium from feature dictionary."""
        if self.model is None:
            return self._formula_fallback(features_dict)

        row = [features_dict.get(f, 0.0) for f in self.FEATURE_NAMES]
        pred = self.model.predict(np.array([row]))[0]
        # Clamp to [30, 100]
        return round(float(np.clip(pred, 30.0, 100.0)), 2)

    def explain(self, features_dict: dict) -> str:
        """
        Returns plain-language premium explanation using SHAP values.
        Example: "Rain forecast (+₹12), High AQI history (+₹8)"
        """
        if self.model is None:
            return "Premium based on zone risk and coverage tier."

        try:
            import shap
            row = np.array([[features_dict.get(f, 0.0) for f in self.FEATURE_NAMES]])
            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(row)[0]

            factors = []
            label_map = {
                "zone_risk_multiplier": "Zone risk",
                "seasonal_factor": "Seasonal adjustment",
                "hist_risk_score": "Historical disruptions",
                "weather_risk": "Rain forecast",
                "aqi_risk": "High AQI history",
                "traffic_risk": "Traffic congestion",
                "live_event_risk": "Live event nearby",
                "loyalty_weeks": "Loyalty discount",
                "tier_encoded": "Coverage tier",
                "dae_normalized": "Earnings level",
            }
            for i, (feat, sv) in enumerate(zip(self.FEATURE_NAMES, shap_values)):
                if abs(sv) >= 1.0:
                    sign = "+" if sv > 0 else "-"
                    factors.append(f"{label_map[feat]} ({sign}₹{abs(sv):.0f})")

            factors.sort(key=lambda x: -abs(float(x.split("₹")[1].rstrip(")"))))
            return ", ".join(factors[:3]) if factors else "Stable zone, standard premium."
        except Exception as e:
            logger.warning(f"SHAP explain error: {e}")
            return "Premium based on your zone's current risk profile."

    def _formula_fallback(self, features_dict: dict) -> float:
        """Fallback to PremiumEngine formula when model unavailable."""
        from app.services.premium_engine import PremiumEngine
        pe = PremiumEngine()
        zmr = features_dict.get("zone_risk_multiplier", 1.0)
        tier_enc = features_dict.get("tier_encoded", 1)
        tier = ["basic", "standard", "premium"][int(tier_enc)]
        loyalty = int(features_dict.get("loyalty_weeks", 0))
        seasonal = features_dict.get("seasonal_factor", 1.0)
        sbp = pe.static_base_premium(zmr, tier, loyalty, seasonal)
        rs = features_dict.get("hist_risk_score", 0.2)
        return pe.weekly_premium(sbp, rs, loyalty)
