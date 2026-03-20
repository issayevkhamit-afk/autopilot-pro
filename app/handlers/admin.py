"""
Admin handlers — manage shop settings, prices, logo, workers.
Only accessible to users with role=admin.
"""
import io
import logging
import os
import uuid
import pandas as pd
from decimal import Decimal, InvalidOperation

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from sqlalchemy.orm import Session

from app.models.shop import Shop
from app.models.user import User
from app.models.membership import Membership
from app.models.labor_price import LaborPrice
from app.models.part_price import PartPrice
from app.states.admin_states import AdminStates
from app.keyboards.admin_kb import (
    admin_menu_kb, admin_prices_kb, admin_parts_kb,
    admin_settings_kb, cancel_kb,
)
from app.keyboards.worker_kb import main_menu_kb

router = Router()
logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _is_admin(membership: Membership | None) -> bool:
    return membership is not None and membership.role == "admin"


def _admin_gate(membership: Membership | None) -> bool:
    return not _is_admin(membership)


# ── Entry points ───────────────────────────────────────────────────────────

@router.message(Command("admin"))
@router.message(F.text == "⚙️ Админ панель")
async def admin_menu(message: Message, membership: Membership | None, shop: Shop | None):
    if _admin_gate(membership):
        await message.answer("⛔ Доступ только для администраторов.")
        return
    await message.answer(
        f"⚙️ *Панель управления* — {shop.name}",
        parse_mode="Markdown",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(F.data == "admin:menu")
async def back_to_menu(call: CallbackQuery, membership: Membership | None, shop: Shop | None):
    if _admin_gate(membership):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    await call.message.edit_text(
        f"⚙️ *Панель управления* — {shop.name}",
        parse_mode="Markdown",
        reply_markup=admin_menu_kb(),
    )
    await call.answer()


# ── LABOR PRICES ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:labor")
async def labor_menu(call: CallbackQuery, membership: Membership | None):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    await call.message.edit_text("💰 *Управление ценами на работы*", parse_mode="Markdown", reply_markup=admin_prices_kb())
    await call.answer()


@router.callback_query(F.data == "labor:list")
async def labor_list(call: CallbackQuery, membership: Membership | None, shop: Shop, db: Session):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    prices = db.query(LaborPrice).filter(LaborPrice.shop_id == shop.id).all()
    if not prices:
        await call.answer("Список пуст. Добавьте работы.", show_alert=True)
        return
    text = "💰 *Прайс на работы:*\n\n"
    for p in prices:
        cur = "₸" if shop.currency == "KZT" else shop.currency
        text += f"  • {p.name} — {cur}{p.price:,.0f} ({p.unit})\n"
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=admin_prices_kb())
    await call.answer()


@router.callback_query(F.data == "labor:add")
async def labor_add_start(call: CallbackQuery, state: FSMContext, membership: Membership | None):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    await call.message.answer(
        "Введите *название работы*:\n_Пример: Замена масла_",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    await state.set_state(AdminStates.waiting_labor_name)
    await call.answer()


@router.message(AdminStates.waiting_labor_name)
async def labor_add_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
        return
    await state.update_data(labor_name=message.text.strip())
    await message.answer("Укажите *цену* (число в тенге):", parse_mode="Markdown", reply_markup=cancel_kb())
    await state.set_state(AdminStates.waiting_labor_price)


@router.message(AdminStates.waiting_labor_price)
async def labor_add_price(message: Message, state: FSMContext, db: Session, shop: Shop):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
        return
    try:
        price = Decimal(message.text.strip().replace(" ", "").replace(",", "."))
    except InvalidOperation:
        await message.answer("❌ Неверный формат цены. Введите число:")
        return

    data = await state.get_data()
    labor = LaborPrice(shop_id=shop.id, name=data["labor_name"], price=price, unit="flat")
    db.add(labor)
    db.commit()

    await state.clear()
    cur = "₸" if shop.currency == "KZT" else shop.currency
    await message.answer(
        f"✅ Добавлено: *{labor.name}* — {cur}{labor.price:,.0f}",
        parse_mode="Markdown",
        reply_markup=main_menu_kb(is_admin=True),
    )


@router.callback_query(F.data == "labor:delete")
async def labor_delete(call: CallbackQuery, membership: Membership | None, shop: Shop, db: Session):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    prices = db.query(LaborPrice).filter(LaborPrice.shop_id == shop.id).all()
    if not prices:
        await call.answer("Список работ пуст.", show_alert=True)
        return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🗑 {p.name}", callback_data=f"labor:del:{p.id}")]
        for p in prices
    ] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:labor")]])
    await call.message.edit_text("Выберите работу для удаления:", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("labor:del:"))
async def labor_delete_confirm(call: CallbackQuery, db: Session, membership: Membership | None):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    labor_id = int(call.data.split(":")[-1])
    item = db.query(LaborPrice).filter(LaborPrice.id == labor_id).first()
    if item:
        db.delete(item)
        db.commit()
    await call.answer("✅ Удалено", show_alert=True)
    await call.message.edit_reply_markup(reply_markup=admin_prices_kb())


# ── PARTS ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:parts")
async def parts_menu(call: CallbackQuery, membership: Membership | None):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    await call.message.edit_text("🔩 *Управление запчастями*", parse_mode="Markdown", reply_markup=admin_parts_kb())
    await call.answer()


@router.callback_query(F.data == "parts:upload")
async def parts_upload_start(call: CallbackQuery, state: FSMContext, membership: Membership | None):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    await call.message.answer(
        "📤 Отправьте файл *CSV или Excel* с прайсом запчастей.\n\n"
        "Формат колонок (любой порядок):\n"
        "`name` — название\n`price` — цена\n`brand` — бренд (необязательно)\n`part_number` — артикул (необязательно)",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    await state.set_state(AdminStates.waiting_parts_file)
    await call.answer()


@router.message(AdminStates.waiting_parts_file, F.document)
async def parts_upload_file(message: Message, state: FSMContext, bot: Bot, db: Session, shop: Shop):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
        return

    doc = message.document
    if not doc.file_name.endswith((".csv", ".xlsx", ".xls")):
        await message.answer("❌ Поддерживаются только CSV и Excel (.xlsx, .xls)")
        return

    processing = await message.answer("⏳ Обрабатываю файл...")
    try:
        file = await bot.get_file(doc.file_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, destination=buf)
        buf.seek(0)

        if doc.file_name.endswith(".csv"):
            df = pd.read_csv(buf)
        else:
            df = pd.read_excel(buf)

        df.columns = [c.lower().strip() for c in df.columns]

        required = {"name", "price"}
        if not required.issubset(set(df.columns)):
            await processing.edit_text(
                f"❌ Не найдены обязательные колонки: {required}\n"
                f"Найдены: {list(df.columns)}"
            )
            return

        count = 0
        for _, row in df.iterrows():
            try:
                name = str(row["name"]).strip()
                price = Decimal(str(row["price"]).replace(" ", "").replace(",", "."))
                if not name or price <= 0:
                    continue
                part = PartPrice(
                    shop_id=shop.id,
                    name=name,
                    price=price,
                    brand=str(row.get("brand", "")).strip() or None,
                    part_number=str(row.get("part_number", "")).strip() or None,
                )
                db.add(part)
                count += 1
            except Exception:
                continue

        db.commit()
        await state.clear()
        await processing.edit_text(f"✅ Загружено *{count}* позиций запчастей.", parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Parts upload failed: {e}", exc_info=True)
        await processing.edit_text("❌ Ошибка при обработке файла.")


@router.callback_query(F.data == "parts:list")
async def parts_list(call: CallbackQuery, membership: Membership | None, shop: Shop, db: Session):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    parts = db.query(PartPrice).filter(PartPrice.shop_id == shop.id).limit(30).all()
    if not parts:
        await call.answer("Список запчастей пуст.", show_alert=True)
        return
    cur = "₸" if shop.currency == "KZT" else shop.currency
    text = "🔩 *Прайс запчастей (первые 30):*\n\n"
    for p in parts:
        brand = f" [{p.brand}]" if p.brand else ""
        text += f"  • {p.name}{brand} — {cur}{p.price:,.0f}\n"
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=admin_parts_kb())
    await call.answer()


# ── LOGO ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:logo")
async def logo_start(call: CallbackQuery, state: FSMContext, membership: Membership | None):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    await call.message.answer("🖼 Отправьте фото логотипа вашего сервиса:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.waiting_logo)
    await call.answer()


@router.message(AdminStates.waiting_logo, F.photo)
async def logo_upload(message: Message, state: FSMContext, bot: Bot, db: Session, shop: Shop):
    photo = message.photo[-1]  # largest
    file = await bot.get_file(photo.file_id)
    logo_dir = os.path.join(UPLOAD_DIR, "logos")
    os.makedirs(logo_dir, exist_ok=True)
    filename = f"{shop.id}_{uuid.uuid4().hex}.jpg"
    logo_path = os.path.join(logo_dir, filename)

    buf = io.BytesIO()
    await bot.download_file(file.file_path, destination=buf)
    with open(logo_path, "wb") as f:
        f.write(buf.getvalue())

    shop.logo_path = logo_path
    db.commit()
    await state.clear()
    await message.answer("✅ Логотип сохранён!", reply_markup=main_menu_kb(is_admin=True))


# ── SETTINGS ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:settings")
async def settings_menu(call: CallbackQuery, membership: Membership | None, shop: Shop):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    text = (
        f"⚙️ *Настройки сервиса*\n\n"
        f"🏪 Название: {shop.name}\n"
        f"📍 Город: {shop.city or '—'}\n"
        f"📞 Телефон: {shop.phone or '—'}\n"
        f"💱 Валюта: {shop.currency}"
    )
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=admin_settings_kb())
    await call.answer()


@router.callback_query(F.data == "settings:name")
async def settings_name_start(call: CallbackQuery, state: FSMContext, membership: Membership | None):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    await call.message.answer("✏️ Введите новое название сервиса:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.waiting_shop_name)
    await call.answer()


@router.message(AdminStates.waiting_shop_name)
async def settings_name_save(message: Message, state: FSMContext, db: Session, shop: Shop):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
        return
    shop.name = message.text.strip()
    db.commit()
    await state.clear()
    await message.answer(f"✅ Название изменено: *{shop.name}*", parse_mode="Markdown", reply_markup=main_menu_kb(is_admin=True))


@router.callback_query(F.data == "settings:city")
async def settings_city_start(call: CallbackQuery, state: FSMContext, membership: Membership | None):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    await call.message.answer("📍 Введите город сервиса:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.waiting_shop_city)
    await call.answer()


@router.message(AdminStates.waiting_shop_city)
async def settings_city_save(message: Message, state: FSMContext, db: Session, shop: Shop):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
        return
    shop.city = message.text.strip()
    db.commit()
    await state.clear()
    await message.answer(f"✅ Город: *{shop.city}*", parse_mode="Markdown", reply_markup=main_menu_kb(is_admin=True))


@router.callback_query(F.data == "settings:phone")
async def settings_phone_start(call: CallbackQuery, state: FSMContext, membership: Membership | None):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    await call.message.answer("📞 Введите номер телефона:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.waiting_shop_phone)
    await call.answer()


@router.message(AdminStates.waiting_shop_phone)
async def settings_phone_save(message: Message, state: FSMContext, db: Session, shop: Shop):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
        return
    shop.phone = message.text.strip()
    db.commit()
    await state.clear()
    await message.answer(f"✅ Телефон: *{shop.phone}*", parse_mode="Markdown", reply_markup=main_menu_kb(is_admin=True))


# ── ESTIMATES HISTORY ──────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:estimates")
async def estimates_history(call: CallbackQuery, membership: Membership | None, shop: Shop, db: Session):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    from app.models.estimate import Estimate
    estimates = (
        db.query(Estimate)
        .filter(Estimate.shop_id == shop.id)
        .order_by(Estimate.created_at.desc())
        .limit(10)
        .all()
    )
    if not estimates:
        await call.answer("История пуста.", show_alert=True)
        return
    cur = "₸" if shop.currency == "KZT" else shop.currency
    text = "📋 *Последние 10 смет:*\n\n"
    for e in estimates:
        car = f"{e.car_make or ''} {e.car_model or ''} {e.car_year or ''}".strip() or "Авто"
        status_icon = {"confirmed": "✅", "cancelled": "❌", "draft": "📝"}.get(e.status, "📝")
        text += f"{status_icon} #{e.id} | {car} | {cur}{e.total:,.0f} | {e.created_at.strftime('%d.%m.%y')}\n"
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=admin_menu_kb())
    await call.answer()


# ── WORKERS ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:workers")
async def workers_list(call: CallbackQuery, membership: Membership | None, shop: Shop, db: Session):
    if _admin_gate(membership):
        await call.answer("⛔", show_alert=True)
        return
    from app.models.membership import Membership as Mb
    from app.models.user import User as Usr
    members = (
        db.query(Mb, Usr)
        .join(Usr, Mb.user_id == Usr.id)
        .filter(Mb.shop_id == shop.id)
        .all()
    )
    text = "👥 *Сотрудники:*\n\n"
    for mb, usr in members:
        name = usr.first_name or usr.username or f"ID:{usr.telegram_id}"
        role_icon = "👑" if mb.role == "admin" else "🔧"
        text += f"{role_icon} {name} — _{mb.role}_\n"

    bot_username = (await call.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start={shop.slug}"
    text += f"\n📎 Ссылка для приглашения:\n`{invite_link}`"

    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=admin_menu_kb())
    await call.answer()
