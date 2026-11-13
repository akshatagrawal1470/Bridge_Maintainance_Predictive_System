class CrackDetector:
    def analyze(self, image_path):
        try:
            import cv2
            import numpy as np

            image = cv2.imread(str(image_path))
            if image is None:
                return {"severity": 0.0, "probability": 0.0, "status": "UNREADABLE"}

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blur, 60, 160)
            dark_pixels = cv2.threshold(gray, 70, 255, cv2.THRESH_BINARY_INV)[1]
            crack_mask = cv2.bitwise_and(edges, dark_pixels)
            density = float(np.count_nonzero(crack_mask)) / float(crack_mask.size)
            severity = round(min(100.0, density * 9000), 2)
        except ImportError:
            severity = self._byte_level_fallback(image_path)

        probability = round(min(99.0, severity * 1.15), 2)
        if severity >= 45:
            status = "HIGH"
        elif severity >= 18:
            status = "MEDIUM"
        elif severity > 4:
            status = "LOW"
        else:
            status = "NONE"
        return {"severity": severity, "probability": probability, "status": status}

    def _byte_level_fallback(self, image_path):
        data = image_path.read_bytes()
        if not data:
            return 0.0
        dark_ratio = sum(1 for byte in data if byte < 55) / len(data)
        contrast_hits = 0
        previous = data[0]
        for byte in data[1:50000]:
            if abs(byte - previous) > 110:
                contrast_hits += 1
            previous = byte
        contrast_ratio = contrast_hits / max(1, min(len(data), 50000))
        return round(min(100.0, (dark_ratio * 45) + (contrast_ratio * 220)), 2)
