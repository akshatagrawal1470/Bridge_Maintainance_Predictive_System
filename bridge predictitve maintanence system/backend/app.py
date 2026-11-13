import csv
import io
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from backend.config import ALLOWED_EXTENSIONS, BASE_DIR, MAX_CONTENT_LENGTH, UPLOAD_FOLDER
from ai.predictor import BridgeHealthPredictor
from database.db import Database
from reports.pdf_report import build_pdf_report
from reports.recommendations import build_condition_summary
from sensor.processing import FeatureExtractor, ReadingBuffer
from vision.crack_detector import CrackDetector


def create_app():
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    db = Database()
    db.init_schema()
    buffer = ReadingBuffer()
    extractor = FeatureExtractor()
    crack_detector = CrackDetector()
    predictor = BridgeHealthPredictor()

    latest_crack = {"severity": 0.0, "probability": 0.0, "status": "NO_IMAGE", "filename": None}

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.post("/api/sensor")
    def ingest_sensor():
        payload = request.get_json(silent=True) or {}
        try:
            reading = {
                "ax": float(payload.get("ax", 0)),
                "ay": float(payload.get("ay", 0)),
                "az": float(payload.get("az", 0)),
                "temperature": float(payload.get("temperature", 0)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except (TypeError, ValueError):
            return jsonify({"error": "ax, ay, az, and temperature must be numeric"}), 400

        db.insert_sensor_reading(reading)
        buffer.add(reading)
        features = extractor.extract(buffer.samples())
        prediction = predictor.predict(features, reading["temperature"], latest_crack["severity"])
        db.insert_analysis(features, prediction, latest_crack)

        return jsonify({"reading": reading, "features": features, "prediction": prediction})

    @app.get("/api/live")
    def live_data():
        if not buffer.samples():
            for sample in extractor.synthetic_samples():
                db.insert_sensor_reading(sample)
                buffer.add(sample)

        latest = buffer.latest()
        features = extractor.extract(buffer.samples())
        prediction = predictor.predict(features, latest["temperature"], latest_crack["severity"])
        summary = build_condition_summary(prediction, features, latest_crack, latest)
        history = db.latest_history(limit=30)
        return jsonify(
            {
                "latest": latest,
                "series": buffer.series(),
                "fft": extractor.fft_series(buffer.samples()),
                "features": features,
                "prediction": prediction,
                "crack": latest_crack,
                "summary": summary,
                "history": history,
            }
        )

    @app.post("/api/crack-detect")
    def crack_detect():
        image = request.files.get("image")
        if not image or image.filename == "":
            return jsonify({"error": "Upload an image using the 'image' form field"}), 400

        extension = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else ""
        if extension not in ALLOWED_EXTENSIONS:
            return jsonify({"error": "Allowed image types: png, jpg, jpeg, webp"}), 400

        filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{secure_filename(image.filename)}"
        path = UPLOAD_FOLDER / filename
        image.save(path)
        result = crack_detector.analyze(path)
        result["filename"] = filename
        latest_crack.update(result)
        db.insert_crack_result(result)
        return jsonify(result)

    @app.get("/reports/export.csv")
    def export_csv():
        rows = db.latest_history(limit=500)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["timestamp", "status", "health", "confidence", "temperature"])
        writer.writeheader()
        writer.writerows(rows)
        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="text/csv",
            as_attachment=True,
            download_name="bridge_inspection_history.csv",
        )

    @app.get("/reports/report.pdf")
    def export_pdf():
        latest = buffer.latest()
        features = extractor.extract(buffer.samples()) if buffer.samples() else {}
        prediction = predictor.predict(features, latest["temperature"], latest_crack["severity"]) if features else {}
        summary = build_condition_summary(prediction, features, latest_crack, latest) if features else {}
        pdf_bytes = build_pdf_report(
            history=db.latest_history(limit=50),
            latest=latest,
            features=features,
            prediction=prediction,
            crack=latest_crack,
            summary=summary,
        )
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="bridge_health_report.pdf",
        )

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
