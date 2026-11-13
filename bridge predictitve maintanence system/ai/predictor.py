from backend.config import MODEL_PATH


class BridgeHealthPredictor:
    def __init__(self):
        self.model = None
        if MODEL_PATH.exists():
            try:
                import joblib

                self.model = joblib.load(MODEL_PATH)
            except ImportError:
                self.model = None

    def predict(self, features, temperature, crack_severity):
        vector = [[
            features["rms"],
            features["std_dev"],
            features["energy"],
            features["peak_frequency"],
            features["peak_magnitude"],
            features["spectral_centroid"],
            temperature,
            crack_severity,
        ]]

        if self.model:
            label = str(self.model.predict(vector)[0]).upper()
            confidence = self._model_confidence(vector)
            health = self._health_from_label(label, confidence)
            return {"status": label, "confidence": confidence, "health": health, "source": "model"}

        risk = (
            min(features["std_dev"] * 110, 35)
            + min(features["energy"] * 2.5, 30)
            + min(crack_severity * 0.45, 30)
            + (8 if temperature > 45 else 0)
        )
        health = int(max(0, min(100, 100 - risk)))
        if health >= 76:
            status = "SAFE"
        elif health >= 48:
            status = "WARNING"
        else:
            status = "UNSAFE"
        confidence = int(max(62, min(96, 100 - abs(health - 62) * 0.35)))
        return {"status": status, "confidence": confidence, "health": health, "source": "rules"}

    def _model_confidence(self, vector):
        if hasattr(self.model, "predict_proba"):
            return int(max(self.model.predict_proba(vector)[0]) * 100)
        return 85

    def _health_from_label(self, label, confidence):
        base = {"SAFE": 90, "WARNING": 62, "UNSAFE": 28}.get(label, 60)
        return int(round((base * 0.8) + (confidence * 0.2)))
