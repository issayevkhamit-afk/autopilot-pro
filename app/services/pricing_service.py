import logging
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.labor_price import LaborPrice
from app.models.part_price import PartPrice

logger = logging.getLogger(__name__)

# Default fallback prices (when shop has no custom prices)
DEFAULT_LABOR_PRICE = Decimal("3500")
DEFAULT_PART_PRICE = Decimal("5000")


def _fuzzy_match(name: str, rows: list, key: str = "name") -> object | None:
    """Case-insensitive substring match."""
    name_lower = name.lower()
    for row in rows:
        row_name = getattr(row, key, "").lower()
        if row_name in name_lower or name_lower in row_name:
            return row
    return None


def build_estimate(shop_id: int, ai_data: dict, db: Session) -> dict:
    """
    Match AI-extracted items against shop price lists.
    Returns structured estimate with totals.
    """
    labor_items = []
    parts_items = []
    total_labor = Decimal("0")
    total_parts = Decimal("0")

    # Load all shop prices once
    labor_prices = db.query(LaborPrice).filter(LaborPrice.shop_id == shop_id).all()
    part_prices = db.query(PartPrice).filter(PartPrice.shop_id == shop_id).all()

    # ── Labor ─────────────────────────────────────────────────────────────
    for item in ai_data.get("labor", []):
        name = item.get("name", "")
        qty = Decimal(str(item.get("qty", 1)))
        matched = _fuzzy_match(name, labor_prices)
        if matched:
            unit_price = Decimal(str(matched.price))
            is_manual = False
        else:
            unit_price = DEFAULT_LABOR_PRICE
            is_manual = True
        line_total = unit_price * qty
        total_labor += line_total
        labor_items.append({
            "name": name,
            "qty": float(qty),
            "unit_price": float(unit_price),
            "total_price": float(line_total),
            "is_manual": is_manual,
        })

    # ── Parts ──────────────────────────────────────────────────────────────
    for item in ai_data.get("parts", []):
        name = item.get("name", "")
        qty = Decimal(str(item.get("qty", 1)))
        unit = item.get("unit", "pcs")
        matched = _fuzzy_match(name, part_prices)
        if matched:
            unit_price = Decimal(str(matched.price))
            is_manual = False
        else:
            unit_price = DEFAULT_PART_PRICE
            is_manual = True
        line_total = unit_price * qty
        total_parts += line_total
        parts_items.append({
            "name": name,
            "qty": float(qty),
            "unit": unit,
            "unit_price": float(unit_price),
            "total_price": float(line_total),
            "is_manual": is_manual,
        })

    total = total_labor + total_parts
    has_manual = any(i["is_manual"] for i in labor_items + parts_items)

    return {
        "car": ai_data.get("car", {}),
        "labor": labor_items,
        "parts": parts_items,
        "total_labor": float(total_labor),
        "total_parts": float(total_parts),
        "total": float(total),
        "has_manual_prices": has_manual,
        "notes": ai_data.get("notes", ""),
    }


def format_estimate_text(estimate: dict, currency: str = "₸") -> str:
    """Render estimate as Telegram-ready text."""
    car = estimate["car"]
    car_str = f"{car.get('make','')} {car.get('model','')} {car.get('year','')}".strip()

    lines = [f"🚗 *{car_str or 'Автомобиль'}*\n"]

    if estimate["labor"]:
        lines.append("🔧 *Работы:*")
        for i in estimate["labor"]:
            manual_flag = " ⚠️" if i["is_manual"] else ""
            lines.append(f"  • {i['name']} × {i['qty']} = {currency}{i['total_price']:,.0f}{manual_flag}")
        lines.append(f"  *Итого работы: {currency}{estimate['total_labor']:,.0f}*\n")

    if estimate["parts"]:
        lines.append("🔩 *Запчасти:*")
        for i in estimate["parts"]:
            manual_flag = " ⚠️" if i["is_manual"] else ""
            lines.append(f"  • {i['name']} × {i['qty']} {i.get('unit','')} = {currency}{i['total_price']:,.0f}{manual_flag}")
        lines.append(f"  *Итого запчасти: {currency}{estimate['total_parts']:,.0f}*\n")

    lines.append(f"💰 *ИТОГО: {currency}{estimate['total']:,.0f}*")

    if estimate.get("has_manual_prices"):
        lines.append("\n⚠️ _Цены помечены ⚠️ — не найдены в прайсе, указаны ориентировочно_")

    if estimate.get("notes"):
        lines.append(f"\n📝 {estimate['notes']}")

    return "\n".join(lines)
