"""
/start handler — deep links, language picker, shop greeting.
/newshop — create new shop as admin.
"""
import logging
import secrets
import traceback
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.orm import Session

from app.config import settings
from app.i18n import t
from app.models.shop import Shop
from app.models.membership import Membership
from app.models.subscription import Subscription
from app.models.user import User
from app.keyboards.worker_kb import main_menu_kb, language_picker_kb

router = Router()
logger = logging.getLogger(__name__)


# ── Language picker ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("lang:"))
async def cb_set_language(
    call: CallbackQuery,
    db: Session | None = None,
    user: User | None = None,
):
    lang = call.data.split(":")[1]  # ru | kz
    if db and user:
        try:
            user.language = lang
            db.commit()
        except Exception as e:
            logger.error(f"set language error: {e}")

    key = "language_set_ru" if lang == "ru" else "language_set_kz"
    await call.message.edit_text(t(key, lang))
    await call.answer()

    # Re-show start greeting with chosen language
    await _send_greeting(call.message, db, user, lang, shop=None, membership=None)


# ── /start ────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    db: Session | None = None,
    user: User | None = None,
    shop: Shop | None = None,
    membership: Membership | None = None,
):
    logger.info(f"/start user={message.from_user.id} args={command.args!r}")
    lang = user.language if user else "ru"

    if db is None:
        await message.answer(t("service_unavailable", lang))
        return

    slug = (command.args or "").strip() or None

    # First ever start with no language set → show language picker
    if user and not user.language:
        await message.answer(t("choose_language", lang), reply_markup=language_picker_kb())
        return

    try:
        if slug:
            target_shop = db.query(Shop).filter(Shop.slug == slug).first()
            if not target_shop:
                target_shop = Shop(slug=slug, name="Мой автосервис", language=lang)
                db.add(target_shop)
                db.flush()
                sub = Subscription(
                    shop_id=target_shop.id,
                    plan="trial",
                    status="active",
                    trial_ends_at=datetime.utcnow() + timedelta(hours=settings.TRIAL_HOURS),
                )
                db.add(sub)
                db.commit()
                db.refresh(target_shop)
                logger.info(f"New shop slug={slug} id={target_shop.id}")

            existing = (
                db.query(Membership)
                .filter(Membership.user_id == user.id, Membership.shop_id == target_shop.id)
                .first()
            )
            if not existing:
                count = db.query(Membership).filter(Membership.shop_id == target_shop.id).count()
                role = "admin" if count == 0 else "worker"
                existing = Membership(user_id=user.id, shop_id=target_shop.id, role=role)
                db.add(existing)
                db.commit()
            shop = target_shop
            membership = existing

    except Exception as e:
        logger.error(f"/start DB error: {e}\n{traceback.format_exc()}")
        await message.answer(t("shop_error", lang))
        return

    if not shop:
        await message.answer(t("welcome_no_shop", lang), parse_mode="Markdown")
        return

    await _send_greeting(message, db, user, lang, shop, membership)


async def _send_greeting(message, db, user, lang, shop, membership):
    if not shop:
        await message.answer(t("welcome_no_shop", lang), parse_mode="Markdown")
        return

    is_admin = membership and membership.role == "admin"
    await message.answer(
        t("greeting", lang,
          name=message.from_user.first_name if hasattr(message, 'from_user') else "...",
          shop=shop.name,
          role=t("role_admin" if is_admin else "role_worker", lang),
          tip=t("tip_admin" if is_admin else "tip_worker", lang)),
        parse_mode="Markdown",
        reply_markup=main_menu_kb(is_admin=is_admin, lang=lang),
    )
    if is_admin and not shop.logo_path:
        await message.answer(t("setup_tip", lang), parse_mode="Markdown")


# ── /newshop ──────────────────────────────────────────────────────────────────

@router.message(Command("newshop"))
async def cmd_new_shop(
    message: Message,
    db: Session | None = None,
    user: User | None = None,
):
    logger.info(f"/newshop user={message.from_user.id}")
    lang = user.language if user else "ru"

    if db is None or user is None:
        await message.answer(t("service_unavailable", lang))
        return

    try:
        slug = secrets.token_hex(4).upper()
        shop = Shop(
            slug=slug,
            name=message.from_user.first_name or "AutoPilot Pro",
            language=lang,
        )
        db.add(shop)
        db.flush()
        sub = Subscription(
            shop_id=shop.id,
            plan="trial",
            status="active",
            trial_ends_at=datetime.utcnow() + timedelta(hours=settings.TRIAL_HOURS),
        )
        db.add(sub)
        mem = Membership(user_id=user.id, shop_id=shop.id, role="admin")
        db.add(mem)
        db.commit()
        logger.info(f"/newshop created slug={slug} user={user.id}")
    except Exception as e:
        logger.error(f"/newshop error: {e}\n{traceback.format_exc()}")
        await message.answer(t("shop_error", lang))
        return

    bot_username = (await message.bot.get_me()).username
    invite = f"https://t.me/{bot_username}?start={slug}"
    await message.answer(
        t("shop_created", lang, name=shop.name, slug=slug, link=invite),
        parse_mode="Markdown",
        reply_markup=main_menu_kb(is_admin=True, lang=lang),
    )
