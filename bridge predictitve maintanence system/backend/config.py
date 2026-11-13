from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = BASE_DIR / "database" / "bridge_monitoring.db"
UPLOAD_FOLDER = BASE_DIR / "data" / "uploads"
MODEL_PATH = BASE_DIR / "models" / "bridge_health_model.joblib"
SAMPLE_RATE_HZ = 50
FFT_WINDOW_SIZE = 128
MAX_CONTENT_LENGTH = 8 * 1024 * 1024
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
