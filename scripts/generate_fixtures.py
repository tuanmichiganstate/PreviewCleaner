"""Regenerate authorized synthetic PDFs. No real user documents are included."""
import io
import json
import hashlib
from pathlib import Path

import pymupdf
import reportlab
from reportlab.pdfgen import canvas
from fpdf import FPDF
import fpdf

root = Path(__file__).resolve().parents[1] / "tests/fixtures"
root.mkdir(exist_ok=True)
manifest = []


def save(name, data, producer, expected):
    (root / name).write_bytes(data)
    manifest.append(dict(file=name, producer=producer, expected=expected,
                         sha256=hashlib.sha256(data).hexdigest()))


buffer = io.BytesIO()
c = canvas.Canvas(buffer, pagesize=(612, 792), invariant=True)
c.setTitle("Synthetic ReportLab fixture")
c.drawString(40, 750, "Keep this ReportLab text and vector artwork.")
c.rect(40, 600, 400, 50)
c.saveState()
c.translate(120, 230)
c.rotate(45)
c.setFont("Helvetica", 72)
c.drawString(0, 0, "Preview")
c.restoreState()
c.showPage()
c.save()
save("reportlab-supported.pdf", buffer.getvalue(), f"ReportLab {reportlab.Version}", "removed")

p = FPDF(unit="pt", format=(612, 792))
p.add_page()
p.set_font("Helvetica", size=12)
p.text(40, 42, "Keep this fpdf2 text and vector artwork.")
p.rect(40, 142, 400, 50)
p.set_font("Helvetica", size=72)
with p.rotation(45, x=120, y=562):
    p.text(120, 562, "Preview")
save("fpdf2-supported.pdf", bytes(p.output()), f"fpdf2 {fpdf.__version__}", "removed")

with pymupdf.open(root / "reportlab-supported.pdf") as source:
    with pymupdf.open() as doc:
        page = doc.new_page(width=612, height=792)
        page.show_pdf_page(page.rect, source, 0)
        save("mupdf-nested-form.pdf", doc.tobytes(), f"PyMuPDF {pymupdf.VersionBind}", "unsupported")
    with pymupdf.open() as doc:
        page = doc.new_page(width=612, height=792)
        page.insert_image(page.rect, pixmap=source[0].get_pixmap())
        save("mupdf-raster.pdf", doc.tobytes(), f"PyMuPDF {pymupdf.VersionBind}", "no_candidate")
save("malformed.pdf", b"%PDF-1.7\nnot a valid document\n", "synthetic malformed bytes", "error")
(root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
