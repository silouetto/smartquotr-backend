# services/pdf_generator.py

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
import os
import qrcode
from io import BytesIO


def generate_qr_image(data):
    qr = qrcode.make(data)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return RLImage(buf, width=50, height=50)

def create_pdf(filename, caption, intent, description, category, blocks):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    if os.path.exists("static/logo.png"):
        elements.append(RLImage("static/logo.png", width=100, height=60))

    elements += [
        Paragraph("<strong>SmartQuotr Project Estimate</strong>", styles['Title']),
        Spacer(1, 12),
        Paragraph(f"<b>Category:</b> {category}", styles['Normal']),
        Paragraph(f"<b>User Intent:</b> {intent}", styles['Normal']),
        Paragraph(f"<b>Image Caption:</b> {caption}", styles['Normal']),
        Paragraph(f"<b>Description:</b> {description}", styles['Normal']),
        Spacer(1, 12)
    ]

    cell_style = ParagraphStyle(
        name="TableCell",
        fontSize=10,
        leading=12,
        alignment=TA_LEFT,
        wordWrap='CJK'
    )

    for section, items in blocks.items():
        if "helpful product links" in section.lower():
            continue
        
        if "coupon" in section.lower() or "promo" in section.lower():
            elements.append(Paragraph(f"<b>{section}</b>", styles['Heading4']))
            for item in items:
                elements.append(Paragraph(item, styles["Normal"]))
                elements.append(generate_qr_image(item))
            elements.append(Spacer(1, 12))
            continue

        if "contractor" in section.lower():
            elements.append(Paragraph(f"<b>{section}</b>", styles['Heading4']))
            for item in items:
                elements.append(Paragraph(f"🏢 {item}", styles["Normal"]))
            elements.append(Spacer(1, 12))
            continue

        clean_items = [i for i in items if "href=" not in i]
        if not clean_items:
            continue

        elements.append(Paragraph(f"<b>{section}</b>", styles['Heading4']))

        table_data = []
        for i in range(0, len(clean_items), 2):
            row = [
                Paragraph(clean_items[i], cell_style),
                Paragraph(clean_items[i + 1], cell_style) if i + 1 < len(clean_items) else Paragraph("", cell_style)
            ]
            table_data.append(row)

        table = Table(table_data, colWidths=[270, 270])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.gray),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 12))

    doc.build(elements)
