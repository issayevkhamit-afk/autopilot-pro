"""
Super-admin panel — only accessible to SUPERADMIN_ID.

Commands:
  /sa — open main menu

Features:
  • View all shops + subscription status
  • Create invite link for a new shop
  • Upload global parts price CSV
  • View/edit AI prompt
  • Manual subscription activate/deactivate
"""
import io
import logging
import traceback
from datetime import datetime, timedelta

import pandas as pd
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    BufferedInputFile,
)
from sqlalchemy.orm import Session

from app.config import settings
from app.models.shop import Shop
from app.models.subscription import Subscription
from app.models.membership import Membership
from app.models.global_part_price import GlobalPartPrice
from app.models.ai_prompt import AiPrompt
from app.states.superadmin_states import SuperAdminStates

router = Router()
logger = logging.getLogger(__name__)

DEFAULT_PROMPT = (
    "Ты — ИИ-ассистент автосервиса. Из текста описания ремонта извлеки структурированные данные.\n"
    "Верни JSON с полями:\n"
    "- car: {make, model, year, vin (если есть)}\n"
    "- labor: [{name, qty}] — список работ\n"
    "- parts: [{name, qty, brand (если есть)}] — список запчастей\n"
    "- notes: строка с дополнительными замечаниями\n"
    "Язык ответа: русский. Если информация не упомянута — оставь поле пустым."
)


def _is_superadmin(user_id: int) -> bool:
    return user_id == settings.SUPERADMIN_ID


def _sa_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏪 Все сервисы", callback_data="sa:shops")],
        [InlineKeyboardButton(text="🔗 Создать приглашение", callback_data="sa:create_invite")],
        [InlineKeyboardButton(text="📦 Загрузить прайс запчастей (CSV)", callback_data="sa:upload_parts")],
        [InlineKeyboardButton(text="🤖 Редактировать AI промпт", callback_data="sa:edit_prompt")],
    ])


# ── Entry point ───────────────────────────────────────────────────────────────

@router.message(Command("sa"))
async def cmd_superadmin(message: Message):
    if not _is_superadmin(message.from_user.id):
        return
    await message.answer("🔐 *Суперадмин панель*", parse_mode="Markdown", reply_markup=_sa_main_kb())


# ── All shops list ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa:shops")
async def cb_sa_shops(call: CallbackQuery, db: Session | None = None):
    if not _is_superadmin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    if not db:
        await call.answer("DB недоступна", show_alert=True)
        return

    shops = db.query(Shop).order_by(Shop.created_at.desc()).limit(50).all()
    if not shops:
        await call.message.edit_text("Сервисов пока нет.", reply_markup=_sa_main_kb())
        await call.answer()
        return

    now = datetime.utcnow()
    lines = ["🏪 *Все сервисы:*\n"]
    buttons = []
    for s in shops:
        sub = db.query(Subscription).filter(Subscription.shop_id == s.id).first()
        if sub is None:
            status = "❓ нет подписки"
        elif sub.status != "active":
            status = "🔴 неактивна"
        elif sub.plan == "trial":
            if sub.trial_ends_at and now < sub.trial_ends_at:
                left = sub.trial_ends_at - now
                h = int(left.total_seconds() // 3600)
                status = f"🟡 триал ({h}ч)"
            else:
                status = "🔴 триал истёк"
        elif sub.expires_at and now < sub.expires_at:
            days = (sub.expires_at - now).days
            status = f"🟢 активна ({days}д)"
        else:
            status = "🔴 истекла"

        mem_count = db.query(Membership).filter(Membership.shop_id == s.id).count()
        lines.append(f"• *{s.name}* `{s.slug}` — {status} | 👥 {mem_count}")
        buttons.append([
            InlineKeyboardButton(
                text=f"⚙️ {s.name[:20]}",
                callback_data=f"sa:shop:{s.id}",
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="sa:back")])
    await call.message.edit_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await call.answer()


@router.callback_query(F.data.startswith("sa:shop:"))
async def cb_sa_shop_detail(call: CallbackQuery, db: Session | None = None):
    if not _is_superadmin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    shop_id = int(call.data.split(":")[2])
    if not db:
        await call.answer()
        return

    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        await call.answer("Сервис не найден", show_alert=True)
        return

    sub = db.query(Subscription).filter(Subscription.shop_id == shop_id).first()
    members = db.query(Membership).filter(Membership.shop_id == shop_id).all()

    text = (
        f"🏪 *{shop.name}*\n"
        f"🔑 Slug: `{shop.slug}`\n"
        f"👥 Участников: {len(members)}\n"
        f"📅 Создан: {shop.created_at.strftime('%d.%m.%Y') if shop.created_at else '—'}\n\n"
    )
    if sub:
        text += f"📋 Тариф: `{sub.plan}` | Статус: `{sub.status}`\n"
        if sub.trial_ends_at:
            text += f"⏰ Триал до: {sub.trial_ends_at.strftime('%d.%m.%Y %H:%M')} UTC\n"
        if sub.expires_at:
            text += f"📆 Оплачено до: {sub.expires_at.strftime('%d.%m.%Y')}\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Активировать +30д", callback_data=f"sa:activate:{shop_id}"),
            InlineKeyboardButton(text="🚫 Деактивировать", callback_data=f"sa:deactivate:{shop_id}"),
        ],
        [InlineKeyboardButton(text="◀️ К списку", callback_data="sa:shops")],
    ])
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("sa:activate:"))
async def cb_sa_activate(call: CallbackQuery, db: Session | None = None):
    if not _is_superadmin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    shop_id = int(call.data.split(":")[2])
    if db:
        try:
            sub = db.query(Subscription).filter(Subscription.shop_id == shop_id).first()
            if not sub:
                sub = Subscription(shop_id=shop_id)
                db.add(sub)
            sub.plan = "paid"
            sub.status = "active"
            sub.expires_at = datetime.utcnow() + timedelta(days=30)
            db.commit()
        except Exception as e:
            logger.error(f"activate error: {e}")
    await call.answer("✅ Активировано на 30 дней", show_alert=True)


@router.callback_query(F.data.startswith("sa:deactivate:"))
async def cb_sa_deactivate(call: CallbackQuery, db: Session | None = None):
    if not _is_superadmin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    shop_id = int(call.data.split(":")[2])
    if db:
        try:
            sub = db.query(Subscription).filter(Subscription.shop_id == shop_id).first()
            if sub:
                sub.status = "inactive"
                db.commit()
        except Exception as e:
            logger.error(f"deactivate error: {e}")
    await call.answer("🚫 Деактивировано", show_alert=True)


# ── Create invite ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa:create_invite")
async def cb_sa_create_invite(call: CallbackQuery, state: FSMContext):
    if not _is_superadmin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    await call.message.edit_text("✏️ Введите название нового автосервиса:")
    await state.set_state(SuperAdminStates.enter_shop_name)
    await call.answer()


@router.message(SuperAdminStates.enter_shop_name)
async def sa_shop_name_received(
    message: Message,
    state: FSMContext,
    bot: Bot,
    db: Session | None = None,
):
    if not _is_superadmin(message.from_user.id):
        return
    await state.clear()
    shop_name = message.text.strip()

    import secrets as sec
    slug = sec.token_hex(4).upper()

    if db:
        try:
            shop = Shop(slug=slug, name=shop_name)
            db.add(shop)
            db.flush()
            sub = Subscription(
                shop_id=shop.id,
                plan="trial",
                status="active",
                trial_ends_at=datetime.utcnow() + timedelta(hours=settings.TRIAL_HOURS),
            )
            db.add(sub)
            db.commit()
        except Exception as e:
            logger.error(f"sa create shop error: {e}\n{traceback.format_exc()}")
            await message.answer("⚠️ Ошибка создания сервиса.")
            return

    bot_me = await bot.get_me()
    invite = f"https://t.me/{bot_me.username}?start={slug}"
    await message.answer(
        f"✅ Сервис создан!\n\n"
        f"🏪 *{shop_name}*\n"
        f"🔑 Код: `{slug}`\n\n"
        f"📎 Ссылка для отправки владельцу:\n`{invite}`",
        parse_mode="Markdown",
        reply_markup=_sa_main_kb(),
    )


# ── Upload global parts CSV ───────────────────────────────────────────────

@router.callback_query(F.data == "sa:upload_parts")
async def cb_sa_upload_parts(call: CallbackQuery, state: FSMContext):
    if not _is_superadmin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    await call.message.edit_text(
        "📎 Отправьте CSV файл с колонками:\n"
        "`name, brand, category, price`\n\n"
        "Пример:\nМасляный фильтр,Bosch,Фильтры,2500\n"
        "Тормозные колодки,,Тормозная система,8000"
    )
    await state.set_state(SuperAdminStates.upload_parts_csv)
    await call.answer()


@router.message(SuperAdminStates.upload_parts_csv, F.document)
async def sa_parts_csv_received(
    message: Message,
    state: FSMContext,
    bot: Bot,
    db: Session | None = None,
):
    if not _is_superadmin(message.from_user.id):
        return
    await state.clear()

    if not db:
        await message.answer("⚠️ DB недоступна.")
        return

    try:
        file = await bot.get_file(message.document.file_id)
        file_bytes = await bot.download_file(file.file_path)
        df = pd.read_csv(io.BytesIO(file_bytes.read()))
        df.columns = [c.strip().lower() for c in df.columns]

        required = {"name", "price"}
        if not required.issubset(set(df.columns)):
            await message.answer(f"❌ CSV должен содержать колонки: name, price\nНайдено: {list(df.columns)}")
            return

        count = 0
        for _, row in df.iterrows():
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            try:
                price = float(row.get("price", 0))
            except (ValueError, TypeError):
                continue

            existing = db.query(GlobalPartPrice).filter(GlobalPartPrice.name == name).first()
            if existing:
                existing.price = price
                existing.brand = str(row.get("brand", "")) or None
                existing.category = str(row.get("category", "")) or None
                existing.source = "csv"
            else:
                db.add(GlobalPartPrice(
                    name=name,
                    brand=str(row.get("brand", "")) or None,
                    category=str(row.get("category", "")) or None,
                    price=price,
                    source="csv",
                ))
            count += 1

        db.commit()
        await message.answer(
            f"✅ Загружено {count} позиций запчастей.",
            reply_markup=_sa_main_kb(),
        )
    except Exception as e:
        logger.error(f"parts csv error: {e}\n{traceback.format_exc()}")
        await message.answer(f"❌ Ошибка обработки CSV: {e}")


# ── Edit AI prompt ────────────────────────────────────────────────────────

@router.callback_query(F.data == "sa:edit_prompt")
async def cb_sa_edit_prompt(call: CallbackQuery, state: FSMContext, db: Session | None = None):
    if not _is_superadmin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    current = DEFAULT_PROMPT
    if db:
        row = db.query(AiPrompt).filter(AiPrompt.key == "extract_repair").first()
        if row:
            current = row.prompt

    await call.message.edit_text(
        f"🤖 *Текущий AI промпт:*\n\n`{current[:800]}`\n\n"
        f"Отправьте новый промпт (или /cancel для отмены):",
        parse_mode="Markdown",
    )
    await state.set_state(SuperAdminStates.edit_prompt)
    await call.answer()


@router.message(SuperAdminStates.edit_prompt)
async def sa_prompt_received(
    message: Message,
    state: FSMContext,
    db: Session | None = None,
):
    if not _is_superadmin(message.from_user.id):
        return
    await state.clear()

    if message.text == "/cancel":
        await message.answer("Отменено.", reply_markup=_sa_main_kb())
        return

    new_prompt = message.text.strip()
    if db:
        try:
            row = db.query(AiPrompt).filter(AiPrompt.key == "extract_repair").first()
            if row:
                row.prompt = new_prompt
            else:
                db.add(AiPrompt(key="extract_repair", prompt=new_prompt))
            db.commit()
            await message.answer("✅ Промпт обновлён!", reply_markup=_sa_main_kb())
        except Exception as e:
            logger.error(f"edit prompt error: {e}")
            await message.answer("⚠️ Ошибка сохранения промпта.")
    else:
        await message.answer("⚠️ DB недоступна.")


@router.callback_query(F.data == "sa:back")
async def cb_sa_back(call: CallbackQuery):
    if not _is_superadmin(call.from_user.id):
        await call.answer()
        return
    await call.message.edit_text("🔐 *Суперадмин панель*", parse_mode="Markdown", reply_markup=_sa_main_kb())
    await call.answer()
