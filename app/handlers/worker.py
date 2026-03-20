"""
Worker handlers — processes text/voice messages and generates estimates.
"""
import io
import logging
import os
import tempfile
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.shop import Shop
from app.models.user import User
from app.models.membership import Membership
from app.models.subscription import Subscription
from app.models.estimate import Estimate, EstimateItem
from app.services.ai_service import extract_repair_data, transcribe_voice
from app.services.pricing_service import build_estimate, format_estimate_text
from app.services.pdf_service import generate_pdf
from app.keyboards.worker_kb import estimate_confirm_kb, main_menu_kb

router = Router()
logger = logging.getLogger(__name__)


def _check_subscription(subscription: Subscription | None) -> bool:
    if not subscription:
        return False
    if subscription.status != "active":
        return False
    if subscription.expires_at and subscription.expires_at < datetime.utcnow():
        return False
    if subscription.trial_ends_at and subscription.trial_ends_at < datetime.utcnow():
        if subscription.plan == "trial":
            return False
    return True


async def _process_repair(
    message: Message,
    text: str,
    db: Session,
    user: User,
    shop: Shop,
    subscription: Subscription,
    membership: Membership,
):
    # Subscription gate
    if not _check_subscription(subscription):
        await message.answer(
            "🔒 *Подписка неактивна*\n\n"
            "Для создания смет необходимо активировать подписку.\n"
            "Обратитесь к владельцу сервиса.",
            parse_mode="Markdown",
        )
        return

    thinking = await message.answer("⏳ Анализирую описание ремонта...")

    try:
        # AI extraction
        ai_data = extract_repair_data(text)

        # Pricing
        estimate_data = build_estimate(shop.id, ai_data, db)

        # Save to DB
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

        # Format and send
        currency = shop.currency or "KZT"
        cur_sym = "₸" if currency == "KZT" else currency
        text_out = format_estimate_text(estimate_data, currency=cur_sym)

        await thinking.delete()
        await message.answer(
            f"📋 *Смета #{estimate.id}*\n\n{text_out}",
            parse_mode="Markdown",
            reply_markup=estimate_confirm_kb(estimate.id),
        )

    except Exception as e:
        logger.error(f"Estimate processing failed: {e}", exc_info=True)
        await thinking.edit_text("❌ Произошла ошибка при анализе. Попробуйте ещё раз.")


@router.message(F.text == "🔧 Новая смета")
async def btn_new_estimate(message: Message):
    await message.answer(
        "📝 Опишите ремонт голосовым сообщением или текстом.\n\n"
        "_Пример: Toyota Camry 2019, замена масла и фильтра, колодки передние_",
        parse_mode="Markdown",
    )


@router.message(F.voice)
async def handle_voice(
    message: Message, bot: Bot, db: Session, user: User,
    shop: Shop | None, subscription: Subscription | None, membership: Membership | None,
):
    if not shop:
        await message.answer("❗ Вы не привязаны к сервису. Используйте пригласительную ссылку.")
        return

    thinking = await message.answer("🎙 Распознаю голосовое сообщение...")
    try:
        voice = message.voice
        file = await bot.get_file(voice.file_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, destination=buf)
        text = transcribe_voice(buf.getvalue(), filename="voice.ogg")
        await thinking.edit_text(f"✅ Распознал: _{text}_\n\nОбрабатываю...", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        await thinking.edit_text("❌ Не удалось распознать голос. Напишите текстом.")
        return

    await _process_repair(message, text, db, user, shop, subscription, membership)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(
    message: Message, db: Session, user: User,
    shop: Shop | None, subscription: Subscription | None, membership: Membership | None,
):
    if not shop:
        await message.answer("❗ Вы не привязаны к сервису. Используйте пригласительную ссылку.")
        return

    # Skip admin button texts
    if message.text in ("⚙️ Админ панель", "❌ Отмена"):
        return

    await _process_repair(message, message.text, db, user, shop, subscription, membership)


@router.callback_query(F.data.startswith("estimate:confirm:"))
async def confirm_estimate(
    call: CallbackQuery, bot: Bot, db: Session, shop: Shop | None
):
    estimate_id = int(call.data.split(":")[-1])
    estimate_obj = db.query(Estimate).filter(Estimate.id == estimate_id).first()
    if not estimate_obj:
        await call.answer("Смета не найдена", show_alert=True)
        return

    await call.message.edit_reply_markup(reply_markup=None)
    generating = await call.message.answer("📄 Генерирую PDF...")

    try:
        # Reconstruct estimate_data from DB for PDF
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

        with open(pdf_path, "rb") as f:
            await generating.delete()
            await call.message.answer_document(
                BufferedInputFile(f.read(), filename=f"estimate_{estimate_id}.pdf"),
                caption=f"✅ Смета #{estimate_id} подтверждена",
            )
        os.unlink(pdf_path)

    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        await generating.edit_text("❌ Ошибка генерации PDF.")

    await call.answer()


@router.callback_query(F.data.startswith("estimate:cancel:"))
async def cancel_estimate(call: CallbackQuery, db: Session):
    estimate_id = int(call.data.split(":")[-1])
    estimate_obj = db.query(Estimate).filter(Estimate.id == estimate_id).first()
    if estimate_obj:
        estimate_obj.status = "cancelled"
        db.commit()
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("🗑 Смета отменена.")
    await call.answer()
