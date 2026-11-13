from collections import deque
from datetime import datetime, timezone
import math
import random

from backend.config import FFT_WINDOW_SIZE, SAMPLE_RATE_HZ


class ReadingBuffer:
    def __init__(self, maxlen=FFT_WINDOW_SIZE):
        self._readings = deque(maxlen=maxlen)

    def add(self, reading):
        self._readings.append(reading)

    def samples(self):
        return list(self._readings)

    def latest(self):
        return self._readings[-1] if self._readings else {"ax": 0, "ay": 0, "az": 0, "temperature": 0}

    def series(self):
        return {
            "labels": [item["timestamp"][11:19] for item in self._readings],
            "ax": [item["ax"] for item in self._readings],
            "ay": [item["ay"] for item in self._readings],
            "az": [item["az"] for item in self._readings],
        }


class FeatureExtractor:
    def synthetic_samples(self, count=FFT_WINDOW_SIZE):
        now = datetime.now(timezone.utc)
        for idx in range(count):
            phase = idx / SAMPLE_RATE_HZ
            yield {
                "ax": 0.04 * math.sin(2 * math.pi * 4 * phase) + random.uniform(-0.015, 0.015),
                "ay": 0.03 * math.sin(2 * math.pi * 7 * phase) + random.uniform(-0.015, 0.015),
                "az": 9.81 + 0.06 * math.sin(2 * math.pi * 4 * phase) + random.uniform(-0.02, 0.02),
                "temperature": 30 + random.uniform(-1.2, 1.2),
                "timestamp": now.isoformat(),
            }

    def magnitudes(self, samples):
        if not samples:
            return [0.0]
        return [math.sqrt(item["ax"] ** 2 + item["ay"] ** 2 + item["az"] ** 2) for item in samples]

    def extract(self, samples):
        signal = self.magnitudes(samples)
        mean = sum(signal) / len(signal)
        centered = [value - mean for value in signal]
        freqs, spectrum = self._rfft(centered)
        peak_index = max(range(len(spectrum)), key=spectrum.__getitem__) if spectrum else 0
        energy = sum(value**2 for value in centered)
        magnitude_sum = sum(spectrum)
        spectral_centroid = sum(freq * mag for freq, mag in zip(freqs, spectrum)) / magnitude_sum if magnitude_sum else 0.0
        return {
            "rms": round(math.sqrt(sum(value**2 for value in signal) / len(signal)), 4),
            "std_dev": round(math.sqrt(sum((value - mean) ** 2 for value in signal) / len(signal)), 4),
            "energy": round(float(energy), 4),
            "peak_frequency": round(freqs[peak_index], 4),
            "peak_magnitude": round(spectrum[peak_index], 4),
            "spectral_centroid": round(spectral_centroid, 4),
        }

    def fft_series(self, samples):
        signal = self.magnitudes(samples)
        mean = sum(signal) / len(signal)
        centered = [value - mean for value in signal]
        freqs, spectrum = self._rfft(centered)
        return {
            "frequency": [round(value, 2) for value in freqs],
            "magnitude": [round(value, 4) for value in spectrum],
        }

    def _rfft(self, values):
        count = len(values)
        bins = (count // 2) + 1
        freqs = []
        spectrum = []
        for k in range(bins):
            real = 0.0
            imag = 0.0
            for n, value in enumerate(values):
                angle = 2 * math.pi * k * n / count
                real += value * math.cos(angle)
                imag -= value * math.sin(angle)
            freqs.append(k * SAMPLE_RATE_HZ / count)
            spectrum.append(math.sqrt(real**2 + imag**2))
        return freqs, spectrum
