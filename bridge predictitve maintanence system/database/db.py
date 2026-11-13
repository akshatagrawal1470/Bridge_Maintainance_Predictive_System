import json
import sqlite3
from datetime import datetime, timezone

from backend.config import DATABASE_PATH


class Database:
    def __init__(self):
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.path = DATABASE_PATH

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_schema(self):
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    ax REAL NOT NULL,
                    ay REAL NOT NULL,
                    az REAL NOT NULL,
                    temperature REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    features_json TEXT NOT NULL,
                    prediction_json TEXT NOT NULL,
                    crack_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS crack_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    filename TEXT,
                    severity REAL NOT NULL,
                    probability REAL NOT NULL,
                    status TEXT NOT NULL
                );
                """
            )

    def insert_sensor_reading(self, reading):
        with self.connect() as db:
            db.execute(
                "INSERT INTO sensor_readings (timestamp, ax, ay, az, temperature) VALUES (?, ?, ?, ?, ?)",
                (reading["timestamp"], reading["ax"], reading["ay"], reading["az"], reading["temperature"]),
            )

    def insert_analysis(self, features, prediction, crack):
        with self.connect() as db:
            db.execute(
                "INSERT INTO analyses (timestamp, features_json, prediction_json, crack_json) VALUES (?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(features),
                    json.dumps(prediction),
                    json.dumps(crack),
                ),
            )

    def insert_crack_result(self, result):
        with self.connect() as db:
            db.execute(
                "INSERT INTO crack_results (timestamp, filename, severity, probability, status) VALUES (?, ?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    result.get("filename"),
                    result["severity"],
                    result["probability"],
                    result["status"],
                ),
            )

    def latest_history(self, limit=30):
        with self.connect() as db:
            rows = db.execute(
                "SELECT timestamp, prediction_json, crack_json FROM analyses ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

        history = []
        for row in reversed(rows):
            prediction = json.loads(row["prediction_json"])
            crack = json.loads(row["crack_json"])
            history.append(
                {
                    "timestamp": row["timestamp"],
                    "time": row["timestamp"][11:19],
                    "status": prediction["status"],
                    "health": prediction["health"],
                    "confidence": prediction["confidence"],
                    "crack_status": crack.get("status", "NO_IMAGE"),
                    "crack_severity": crack.get("severity", 0),
                }
            )
        return history
