# Bridge Predictive Maintenance System

AI-powered Flask dashboard for bridge structural health monitoring using MPU6050 vibration data, FFT feature extraction, machine learning prediction, image-based crack analysis, SQLite storage, and CSV/PDF reporting.

## Features

- Live MPU6050-style sensor API for acceleration and temperature
- Real-time dashboard with sensor cards, vibration chart, FFT chart, health score, status, and history
- FFT feature extraction: RMS, standard deviation, energy, peak frequency, peak magnitude, spectral centroid
- Rule-based fallback predictor with optional Joblib model loading
- Secure image uploads for crack analysis
- SQLite database for sensor readings, vibration features, predictions, and crack results
- CSV and PDF report downloads

## Project Structure

```text
backend/
frontend/
templates/
static/
sensor/
ai/
vision/
database/
models/
reports/
data/
```

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m backend.app
```

Open:

```text
http://127.0.0.1:5000
```

## API

### POST `/api/sensor`

Receives live sensor data from ESP32/Arduino gateway.

```json
{
  "ax": 0.01,
  "ay": 0.02,
  "az": 9.81,
  "temperature": 31.2
}
```

### GET `/api/live`

Returns the latest readings, FFT features, prediction, and history for dashboard polling.

### POST `/api/crack-detect`

Upload a bridge image using form field `image`.

### GET `/reports/export.csv`

Downloads inspection history as CSV.

### GET `/reports/report.pdf`

Downloads a PDF summary report.

## Hardware Integration

For ESP32, send JSON sensor payloads over Wi-Fi to `/api/sensor`. Keep sample frequency stable and set `SAMPLE_RATE_HZ` in `backend/config.py` to match your device.

## Model Integration

Place a trained model at:

```text
models/bridge_health_model.joblib
```

The model should accept these feature columns:

```text
rms, std_dev, energy, peak_frequency, peak_magnitude, spectral_centroid, temperature, crack_severity
```

If no model is present, the application uses a deterministic rule-based predictor.
