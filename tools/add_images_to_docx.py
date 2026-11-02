# Helper: inserts the screenshot PNGs into the report .docx above each figure caption.
import os
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(ROOT, "WGUPS_Task2_Report.docx")
images = {
    "Figure D1.": ("D1_status_0900.png", 6.5),
    "Figure D2.": ("D2_status_1000.png", 6.5),
    "Figure D3.": ("D3_status_1215.png", 6.5),
    "Figure E.": ("E_total_mileage.png", 3.8),
    "Figure E2.": ("single_package_lookup.png", 3.8),
}
doc = Document(path)
for p in list(doc.paragraphs):
    for prefix, (name, width) in images.items():
        if p.text.startswith(prefix):
            new_p = p.insert_paragraph_before()
            new_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            new_p.add_run().add_picture(os.path.join(ROOT, "screenshots", name), width=Inches(width))
doc.save(path)
print("images inserted")
