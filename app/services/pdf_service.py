import os
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register DejaVu for Cyrillic support
_FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fonts")
_REGULAR = os.path.join(_FONT_DIR, "DejaVuSans.ttf")
_BOLD    = os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")

_fonts_registered = False


def _ensure_fonts():
    global _fonts_registered
    if _fonts_registered:
        return
    if os.path.exists(_REGULAR):
        pdfmetrics.registerFont(TTFont("DejaVu", _REGULAR))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", _BOLD))
        _fonts_registered = True


NAVY  = colors.HexColor("#1b3a5c")
TEAL  = colors.HexColor("#00879a")
LIGHT = colors.HexColor("#f4f6f8")
WHITE = colors.white


def generate_pdf(estimate: dict, shop: object, output_path: str | None = None) -> str:
    """
    Generate a styled PDF estimate.
    Returns path to the created PDF file.
    """
    _ensure_fonts()
    font_name      = "DejaVu"      if _fonts_registered else "Helvetica"
    font_name_bold = "DejaVu-Bold" if _fonts_registered else "Helvetica-Bold"

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        output_path = tmp.name
        tmp.close()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle("normal", fontName=font_name, fontSize=9, leading=14)
    style_bold   = ParagraphStyle("bold",   fontName=font_name_bold, fontSize=9, leading=14)
    style_h1     = ParagraphStyle("h1",     fontName=font_name_bold, fontSize=18, textColor=NAVY)
    style_h2     = ParagraphStyle("h2",     fontName=font_name_bold, fontSize=11, textColor=NAVY)
    style_center = ParagraphStyle("center", fontName=font_name, fontSize=9, alignment=TA_CENTER)
    style_right  = ParagraphStyle("right",  fontName=font_name, fontSize=9, alignment=TA_RIGHT)

    currency = getattr(shop, "currency", "KZT") or "KZT"
    cur_sym  = "₸" if currency == "KZT" else currency

    story = []

    # ── HEADER ────────────────────────────────────────────────────────────
    header_data = []

    # Logo column
    logo_cell = []
    if shop.logo_path and os.path.exists(shop.logo_path):
        logo_cell.append(Image(shop.logo_path, width=3 * cm, height=3 * cm))
    else:
        logo_cell.append(Paragraph("🔧", style_h1))

    # Shop info column
    shop_cell = [
        Paragraph(shop.name or "AutoPilot Pro", style_h1),
    ]
    if getattr(shop, "city", None):
        shop_cell.append(Paragraph(shop.city, style_normal))
    if getattr(shop, "phone", None):
        shop_cell.append(Paragraph(shop.phone, style_normal))
    if getattr(shop, "address", None):
        shop_cell.append(Paragraph(shop.address, style_normal))

    # Date column
    date_cell = [
        Paragraph("СМЕТА", ParagraphStyle("sm", fontName=font_name_bold, fontSize=22, textColor=TEAL, alignment=TA_RIGHT)),
        Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y')}", style_right),
        Paragraph(f"№ {datetime.now().strftime('%Y%m%d%H%M')}", style_right),
    ]

    header_table = Table([[logo_cell, shop_cell, date_cell]], colWidths=[3.5 * cm, 9 * cm, 5 * cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=12))

    # ── CAR INFO ──────────────────────────────────────────────────────────
    car = estimate.get("car", {})
    car_str = f"{car.get('make','')} {car.get('model','')} {car.get('year','')}".strip()
    if car_str:
        story.append(Paragraph(f"🚗 Автомобиль: <b>{car_str}</b>", style_normal))
        if car.get("vin"):
            story.append(Paragraph(f"VIN: {car['vin']}", style_normal))
        story.append(Spacer(1, 10))

    # ── LABOR TABLE ───────────────────────────────────────────────────────
    if estimate.get("labor"):
        story.append(Paragraph("Работы", style_h2))
        story.append(Spacer(1, 4))
        table_data = [["Наименование работы", "Кол-во", "Цена", "Сумма"]]
        for item in estimate["labor"]:
            manual = " *" if item.get("is_manual") else ""
            table_data.append([
                Paragraph(item["name"] + manual, style_normal),
                str(item["qty"]),
                f"{cur_sym}{item['unit_price']:,.0f}",
                f"{cur_sym}{item['total_price']:,.0f}",
            ])
        table_data.append([
            Paragraph("<b>Итого работы</b>", style_bold), "", "",
            Paragraph(f"<b>{cur_sym}{estimate['total_labor']:,.0f}</b>", style_bold),
        ])
        t = Table(table_data, colWidths=[10 * cm, 2 * cm, 3 * cm, 3 * cm])
        t.setStyle(_item_table_style())
        story.append(t)
        story.append(Spacer(1, 10))

    # ── PARTS TABLE ───────────────────────────────────────────────────────
    if estimate.get("parts"):
        story.append(Paragraph("Запчасти", style_h2))
        story.append(Spacer(1, 4))
        table_data = [["Наименование запчасти", "Кол-во", "Цена", "Сумма"]]
        for item in estimate["parts"]:
            manual = " *" if item.get("is_manual") else ""
            table_data.append([
                Paragraph(item["name"] + manual, style_normal),
                f"{item['qty']} {item.get('unit','')}",
                f"{cur_sym}{item['unit_price']:,.0f}",
                f"{cur_sym}{item['total_price']:,.0f}",
            ])
        table_data.append([
            Paragraph("<b>Итого запчасти</b>", style_bold), "", "",
            Paragraph(f"<b>{cur_sym}{estimate['total_parts']:,.0f}</b>", style_bold),
        ])
        t = Table(table_data, colWidths=[10 * cm, 2 * cm, 3 * cm, 3 * cm])
        t.setStyle(_item_table_style())
        story.append(t)
        story.append(Spacer(1, 10))

    # ── TOTAL ─────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL, spaceBefore=6, spaceAfter=6))
    total_table = Table([
        ["", Paragraph(f"<b>ИТОГО: {cur_sym}{estimate['total']:,.0f}</b>",
                       ParagraphStyle("total", fontName=font_name_bold, fontSize=14, textColor=NAVY, alignment=TA_RIGHT))]
    ], colWidths=[12 * cm, 6 * cm])
    total_table.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    story.append(total_table)

    # ── NOTES & DISCLAIMER ────────────────────────────────────────────────
    if estimate.get("notes"):
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Примечание: {estimate['notes']}", style_normal))

    if estimate.get("has_manual_prices"):
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "* Цены, отмеченные звёздочкой, являются ориентировочными (не найдены в прайс-листе сервиса).",
            ParagraphStyle("disc", fontName=font_name, fontSize=8, textColor=colors.grey),
        ))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Создано с помощью AutoPilot Pro · t.me/AutoPilotProBot",
        ParagraphStyle("footer", fontName=font_name, fontSize=8, textColor=colors.grey, alignment=TA_CENTER),
    ))

    doc.build(story)
    return output_path


def _item_table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "DejaVu-Bold" if _fonts_registered else "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
        ("ALIGN",       (3, 0), (3, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [WHITE, LIGHT]),
        ("BACKGROUND",  (0, -1), (-1, -1), colors.HexColor("#e8ecf0")),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d8e0")),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (0, -1), 6),
    ])
