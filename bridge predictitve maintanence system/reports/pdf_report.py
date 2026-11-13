from datetime import datetime


PAGE_W = 612
PAGE_H = 792
MARGIN = 46


def build_pdf_report(history, latest=None, features=None, prediction=None, crack=None, summary=None):
    latest = latest or {}
    features = features or {}
    prediction = prediction or {}
    crack = crack or {}
    summary = summary or {}

    pdf = _PdfDocument()
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    _draw_header(pdf, generated_at, prediction)
    _draw_summary(pdf, summary, prediction)
    _draw_vitals(pdf, latest, crack)
    _draw_fft_features(pdf, features)
    _draw_recommendations(pdf, summary.get("recommendations", []))
    _draw_history(pdf, history[-18:])

    return pdf.render()


def _draw_header(pdf, generated_at, prediction):
    pdf.fill_rect(0, PAGE_H - 96, PAGE_W, 96, (0.06, 0.18, 0.27))
    pdf.fill_rect(0, PAGE_H - 100, PAGE_W, 4, (0.07, 0.55, 0.49))
    pdf.text(MARGIN, PAGE_H - 42, "Bridge Predictive Maintenance Report", size=18, bold=True, color=(1, 1, 1))
    pdf.text(MARGIN, PAGE_H - 64, "AI vibration analysis, crack assessment, and maintenance guidance", size=9, color=(0.82, 0.9, 0.94))

    status = prediction.get("status", "UNKNOWN")
    pdf.text(PAGE_W - 190, PAGE_H - 42, f"STATUS: {status}", size=12, bold=True, color=_status_color(status))
    pdf.text(PAGE_W - 190, PAGE_H - 64, f"Generated: {generated_at}", size=8.5, color=(0.82, 0.9, 0.94))
    pdf.y = PAGE_H - 128


def _draw_summary(pdf, summary, prediction):
    pdf.section_title("Executive Summary")
    pdf.fill_rect(MARGIN, pdf.y - 92, PAGE_W - (MARGIN * 2), 82, (0.95, 0.98, 0.98))
    pdf.stroke_rect(MARGIN, pdf.y - 92, PAGE_W - (MARGIN * 2), 82, (0.78, 0.86, 0.87))
    pdf.text(MARGIN + 14, pdf.y - 28, f"Health Score: {prediction.get('health', '--')}%", size=13, bold=True)
    pdf.text(MARGIN + 190, pdf.y - 28, f"Confidence: {prediction.get('confidence', '--')}%", size=13, bold=True)
    pdf.text(MARGIN + 360, pdf.y - 28, f"Priority: {summary.get('priority', 'Not available')}", size=13, bold=True)
    pdf.wrapped_text(MARGIN + 14, pdf.y - 50, summary.get("condition", "No condition summary available."), width=88, size=9.5)
    pdf.y -= 116


def _draw_vitals(pdf, latest, crack):
    rows = [
        ("Acceleration X", f"{latest.get('ax', 0):.3f} m/s^2", "Horizontal vibration component"),
        ("Acceleration Y", f"{latest.get('ay', 0):.3f} m/s^2", "Lateral vibration component"),
        ("Acceleration Z", f"{latest.get('az', 0):.3f} m/s^2", "Vertical response including gravity"),
        ("Temperature", f"{latest.get('temperature', 0):.1f} deg C", "MPU6050 temperature reading"),
        ("Crack Status", crack.get("status", "NO_IMAGE"), "Computer vision result"),
        ("Crack Severity", f"{crack.get('severity', 0):.1f}%", "Estimated visible crack intensity"),
        ("Crack Probability", f"{crack.get('probability', 0):.1f}%", "Image-based crack likelihood"),
    ]
    _draw_table(pdf, "Important Vitals", ["Metric", "Value", "Meaning"], rows, [150, 120, 250])


def _draw_fft_features(pdf, features):
    rows = [
        ("RMS", features.get("rms", "--"), "Overall vibration level"),
        ("Standard Deviation", features.get("std_dev", "--"), "Signal stability variation"),
        ("Energy", features.get("energy", "--"), "Total vibration energy in sample window"),
        ("Peak Frequency", f"{features.get('peak_frequency', '--')} Hz", "Dominant frequency component"),
        ("Peak Magnitude", features.get("peak_magnitude", "--"), "Strength of dominant frequency"),
        ("Spectral Centroid", f"{features.get('spectral_centroid', '--')} Hz", "Center of vibration spectrum"),
    ]
    _draw_table(pdf, "FFT Vibration Analysis", ["Feature", "Reading", "Interpretation"], rows, [150, 120, 250])


def _draw_recommendations(pdf, recommendations):
    pdf.ensure_space(120)
    pdf.section_title("Maintenance Recommendations")
    if not recommendations:
        recommendations = ["No specific recommendation is available for the current data."]
    for index, item in enumerate(recommendations, start=1):
        pdf.ensure_space(38)
        pdf.text(MARGIN, pdf.y, f"{index}.", size=9.5, bold=True, color=(0.07, 0.32, 0.45))
        used = pdf.wrapped_text(MARGIN + 22, pdf.y, item, width=92, size=9.5)
        pdf.y -= max(20, used + 8)


def _draw_history(pdf, history):
    rows = []
    for row in history:
        rows.append(
            (
                row.get("time", str(row.get("timestamp", ""))[11:19]),
                row.get("status", ""),
                f'{row.get("health", "--")}%',
                row.get("crack_status", "NO_IMAGE"),
            )
        )
    _draw_table(pdf, "Recent Inspection History", ["Time", "Status", "Health", "Crack"], rows, [110, 130, 110, 170])


def _draw_table(pdf, title, headers, rows, widths):
    pdf.ensure_space(80)
    pdf.section_title(title)
    row_h = 24
    x = MARGIN
    pdf.fill_rect(MARGIN, pdf.y - row_h + 5, sum(widths), row_h, (0.91, 0.95, 0.96))
    for header, width in zip(headers, widths):
        pdf.text(x + 7, pdf.y - 11, header, size=8.5, bold=True, color=(0.18, 0.27, 0.34))
        x += width
    pdf.y -= row_h

    for index, row in enumerate(rows):
        pdf.ensure_space(row_h + 12)
        fill = (0.99, 1, 1) if index % 2 == 0 else (0.96, 0.98, 0.99)
        pdf.fill_rect(MARGIN, pdf.y - row_h + 5, sum(widths), row_h, fill)
        pdf.stroke_rect(MARGIN, pdf.y - row_h + 5, sum(widths), row_h, (0.86, 0.9, 0.91))
        x = MARGIN
        for cell, width in zip(row, widths):
            pdf.text(x + 7, pdf.y - 11, str(cell), size=8.5, color=(0.12, 0.18, 0.24))
            x += width
        pdf.y -= row_h
    pdf.y -= 14


def _status_color(status):
    if status == "SAFE":
        return (0.39, 0.88, 0.67)
    if status == "WARNING":
        return (1.0, 0.77, 0.35)
    if status == "UNSAFE":
        return (1.0, 0.45, 0.42)
    return (1, 1, 1)


class _PdfDocument:
    def __init__(self):
        self.pages = []
        self.commands = []
        self.y = PAGE_H - 128

    def ensure_space(self, needed):
        if self.y - needed < 58:
            self.new_page()

    def new_page(self):
        self.pages.append("\n".join(self.commands))
        self.commands = []
        self.fill_rect(0, PAGE_H - 28, PAGE_W, 28, (0.06, 0.18, 0.27))
        self.text(MARGIN, PAGE_H - 18, "Bridge Predictive Maintenance Report", size=8.5, color=(1, 1, 1))
        self.y = PAGE_H - 58

    def section_title(self, title):
        self.ensure_space(36)
        self.text(MARGIN, self.y, title, size=12, bold=True, color=(0.06, 0.18, 0.27))
        self.fill_rect(MARGIN, self.y - 8, 46, 2, (0.07, 0.55, 0.49))
        self.y -= 20

    def text(self, x, y, text, size=10, bold=False, color=(0, 0, 0)):
        r, g, b = color
        font = "F2" if bold else "F1"
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
        self.commands.append(f"BT /{font} {size} Tf {x:.1f} {y:.1f} Td ({_escape(str(text))}) Tj ET")

    def wrapped_text(self, x, y, text, width=80, size=10, color=(0.15, 0.2, 0.26)):
        line_height = size + 4
        used = 0
        for line in _wrap(str(text), width):
            self.text(x, y - used, line, size=size, color=color)
            used += line_height
        return used

    def fill_rect(self, x, y, w, h, color):
        r, g, b = color
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg {x:.1f} {y:.1f} {w:.1f} {h:.1f} re f")

    def stroke_rect(self, x, y, w, h, color):
        r, g, b = color
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} RG {x:.1f} {y:.1f} {w:.1f} {h:.1f} re S")

    def render(self):
        self.pages.append("\n".join(self.commands))
        objects = ["<< /Type /Catalog /Pages 2 0 R >>"]
        page_ids = []
        content_ids = []
        next_id = 3
        for _ in self.pages:
            page_ids.append(next_id)
            content_ids.append(next_id + 1)
            next_id += 2
        objects.append(f"<< /Type /Pages /Kids [{' '.join(f'{pid} 0 R' for pid in page_ids)}] /Count {len(page_ids)} >>")
        font_obj_id = next_id
        bold_font_obj_id = next_id + 1
        for page_id, content_id, content in zip(page_ids, content_ids, self.pages):
            objects.append(
                f"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 {font_obj_id} 0 R /F2 {bold_font_obj_id} 0 R >> >> "
                f"/MediaBox [0 0 {PAGE_W} {PAGE_H}] /Contents {content_id} 0 R >>"
            )
            content_bytes = content.encode("latin-1", errors="replace")
            objects.append(f"<< /Length {len(content_bytes)} >>\nstream\n{content}\nendstream")
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

        pdf = "%PDF-1.4\n"
        offsets = [0]
        for number, obj in enumerate(objects, start=1):
            offsets.append(len(pdf.encode("latin-1")))
            pdf += f"{number} 0 obj\n{obj}\nendobj\n"
        xref_offset = len(pdf.encode("latin-1"))
        pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
        for offset in offsets[1:]:
            pdf += f"{offset:010d} 00000 n \n"
        pdf += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
        return pdf.encode("latin-1", errors="replace")


def _wrap(text, width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
