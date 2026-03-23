"""
Worker handlers — processes text/voice messages and generates estimates.
Includes: subscription gate, AI price learning, RU/KZ i18n.
"""
import io
import logging
import os
import traceback
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy.orm import Session

from app.config import settings
from app.i18n import t
from app.models.shop import Shop
from app.models.user import User
from app.models.membership import Membership
from app.models.subscription import Subscription
from app.models.estimate import Estimate, EstimateItem
from app.models.labor_price import LaborPrice
from app.services.ai_service import extract_repair_data, transcribe_voice
from app.services.pricing_service import build_estimate, format_estimate_text
from app.services.pdf_service import generate_pdf
from app.keyboards.worker_kb import estimate_confirm_kb, main_menu_kb, payment_kb
from app.handlers.payment import is_subscription_active

router = Router()
logger = logging.getLogger(__name__)


def _lang(user: User | None) -> str:
    return (user.language or "ru") if user else "ru"


# ── Subscription check helper ─────────────────────────────────────────────

async def _gate(message: Message, subscription: Subscription | None,
                shop: Shop | None, lang: str) -> bool:
    """Returns True if OK to proceed, False if blocked (and sends message)."""
    if not is_subscription_active(subscription):
        key = "trial_expired" if (subscription and subscription.plan == "trial") else "subscription_inactive"
        await message.answer(t(key, lang), parse_mode="Markdown", reply_markup=payment_kb(lang))
        return False
    return True


# ── Main processing function ──────────────────────────────────────────────

async def _process_repair(
    message: Message,
    text: str,
    db: Session,
    user: User,
    shop: Shop,
    subscription: Subscription,
    membership: Membership,
):
    lang = _lang(user)

    if not await _gate(message, subscription, shop, lang):
        return

    thinking = await message.answer(t("processing", lang))

    try:
        ai_data = extract_repair_data(text)
        estimate_data = build_estimate(shop.id, ai_data, db)

        estimate = Estimate(
            shop_id=shop.id,
            created_by=user.id,
            car_make=estimate_data["car"].get("make"),
            car_model=estimate_data["car"].get("model"),
            car_year=estimate_data["car"].get("year"),
            car_vin=estimate_data["car"].get("vin"),
            raw_input=text,
            total_labor=estimate_data["total_labor"],
            total_parts=estimate_data["total_parts"],
            total=estimate_data["total"],
            notes=estimate_data.get("notes"),
            status="draft",
        )
        db.add(estimate)
        db.flush()

        for item in estimate_data["labor"]:
            db.add(EstimateItem(
                estimate_id=estimate.id,
                item_type="labor",
                name=item["name"],
                qty=item["qty"],
                unit_price=item["unit_price"],
                total_price=item["total_price"],
                is_manual=str(item["is_manual"]).lower(),
            ))

        for item in estimate_data["parts"]:
            db.add(EstimateItem(
                estimate_id=estimate.id,
                item_type="part",
                name=item["name"],
                qty=item["qty"],
                unit_price=item["unit_price"],
                total_price=item["total_price"],
                is_manual=str(item["is_manual"]).lower(),
            ))

        db.commit()
        db.refresh(estimate)

        cur_sym = "₸"
        text_out = format_estimate_text(estimate_data, currency=cur_sym)

        await thinking.delete()
        await message.answer(
            t("estimate_ready", lang, text=text_out),
            parse_mode="Markdown",
            reply_markup=estimate_confirm_kb(estimate.id, lang),
        )

    except Exception as e:
        logger.error(f"Estimate processing failed: {e}\n{traceback.format_exc()}")
        await thinking.edit_text(t("ai_error", lang))


# ── Button: "Новая смета" ─────────────────────────────────────────────────

@router.message(F.text.in_({"🔧 Новая смета", "🔧 Жаңа смета"}))
async def btn_new_estimate(message: Message, user: User | None = None):
    lang = _lang(user)
    await message.answer(
        "📝 Опишите ремонт голосовым сообщением или текстом.\n\n"
        "_Пример: Toyota Camry 2019, замена масла и фильтра, колодки передние_",
        parse_mode="Markdown",
    )


# ── Voice message ─────────────────────────────────────────────────────────

@router.message(F.voice)
async def handle_voice(
    message: Message,
    bot: Bot,
    db: Session | None = None,
    user: User | None = None,
    shop: Shop | None = None,
    subscription: Subscription | None = None,
    membership: Membership | None = None,
):
    lang = _lang(user)
    if not shop:
        await message.answer(t("no_shop", lang))
        return
    if db is None:
        await message.answer(t("service_unavailable", lang))
        return

    thinking = await message.answer("🎙 Распознаю голосовое сообщение...")
    try:
        file = await bot.get_file(message.voice.file_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, destination=buf)
        text = transcribe_voice(buf.getvalue(), filename="voice.ogg")
        await thinking.edit_text(f"✅ Распознал: _{text}_\n\nОбрабатываю...", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        await thinking.edit_text(t("voice_error", lang))
        return

    await _process_repair(message, text, db, user, shop, subscription, membership)


# ── Text message ──────────────────────────────────────────────────────────

@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(
    message: Message,
    db: Session | None = None,
    user: User | None = None,
    shop: Shop | None = None,
    subscription: Subscription | None = None,
    membership: Membership | None = None,
):
    lang = _lang(user)

    # Skip menu button texts
    skip = {
        "⚙️ Админ панель", "❌ Отмена", "❌ Болдырмау",
        "🔧 Новая смета", "🔧 Жаңа смета",
    }
    if message.text in skip:
        return

    if not shop:
        await message.answer(t("no_shop", lang))
        return
    if db is None:
        await message.answer(t("service_unavailable", lang))
        return

    await _process_repair(message, message.text, db, user, shop, subscription, membership)


# ── Confirm estimate → PDF ────────────────────────────────────────────────

@router.callback_query(F.data.startswith("estimate:confirm:"))
async def confirm_estimate(
    call: CallbackQuery,
    bot: Bot,
    db: Session | None = None,
    shop: Shop | None = None,
    user: User | None = None,
):
    lang = _lang(user)
    if db is None:
        await call.answer(t("service_unavailable", lang), show_alert=True)
        return

    estimate_id = int(call.data.split(":")[-1])
    estimate_obj = db.query(Estimate).filter(Estimate.id == estimate_id).first()
    if not estimate_obj:
        await call.answer("Смета не найдена", show_alert=True)
        return

    await call.message.edit_reply_markup(reply_markup=None)
    generating = await call.message.answer("📄 Генерирую PDF...")

    try:
        items = db.query(EstimateItem).filter(EstimateItem.estimate_id == estimate_id).all()
        labor = [
            {"name": i.name, "qty": float(i.qty), "unit_price": float(i.unit_price),
             "total_price": float(i.total_price), "is_manual": i.is_manual == "true"}
            for i in items if i.item_type == "labor"
        ]
        parts = [
            {"name": i.name, "qty": float(i.qty), "unit": "pcs",
             "unit_price": float(i.unit_price), "total_price": float(i.total_price),
             "is_manual": i.is_manual == "true"}
            for i in items if i.item_type == "part"
        ]
        estimate_data = {
            "car": {
                "make": estimate_obj.car_make or "",
                "model": estimate_obj.car_model or "",
                "year": estimate_obj.car_year or "",
                "vin": estimate_obj.car_vin or "",
            },
            "labor": labor,
            "parts": parts,
            "total_labor": float(estimate_obj.total_labor),
            "total_parts": float(estimate_obj.total_parts),
            "total": float(estimate_obj.total),
            "has_manual_prices": any(i.is_manual == "true" for i in items),
            "notes": estimate_obj.notes or "",
        }

        pdf_path = generate_pdf(estimate_data, shop)
        estimate_obj.status = "confirmed"
        estimate_obj.pdf_path = pdf_path
        db.commit()

        # ── AI price learning: save new manual labor prices ───────────────
        if shop:
            for item in labor:
                if item["is_manual"] and item["unit_price"] > 0:
                    existing = (
                        db.query(LaborPrice)
                        .filter(
                            LaborPrice.shop_id == shop.id,
                            LaborPrice.name == item["name"],
                        )
                        .first()
                    )
                    if not existing:
                        db.add(LaborPrice(
                            shop_id=shop.id,
                            name=item["name"],
                            price=item["unit_price"],
                        ))
                        logger.info(f"Learned price: shop={shop.id} '{item['name']}' = {item['unit_price']}")
            db.commit()

        with open(pdf_path, "rb") as f:
            await generating.delete()
            await call.message.answer_document(
                BufferedInputFile(f.read(), filename=f"estimate_{estimate_id}.pdf"),
                caption=f"✅ Смета #{estimate_id} подтверждена",
            )
        os.unlink(pdf_path)

    except Exception as e:
        logger.error(f"PDF generation failed: {e}\n{traceback.format_exc()}")
        await generating.edit_text(t("ai_error", lang))

    await call.answer()


# ── Cancel estimate ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("estimate:cancel:"))
async def cancel_estimate(
    call: CallbackQuery,
    db: Session | None = None,
    user: User | None = None,
):
    lang = _lang(user)
    if db:
        estimate_id = int(call.data.split(":")[-1])
        estimate_obj = db.query(Estimate).filter(Estimate.id == estimate_id).first()
        if estimate_obj:
            estimate_obj.status = "cancelled"
            db.commit()
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(t("estimate_cancelled", lang))
    await call.answer()
