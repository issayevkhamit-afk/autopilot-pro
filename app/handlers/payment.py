"""
Subscription gate + Kaspi payment flow.

Flow:
  1. Worker sends any message → subscription check
  2. Expired/inactive → show "pay" button
  3. User clicks "💳 Оплатить" → Kaspi instructions + "Я оплатил" button
  4. User clicks "Я оплатил" → notify superadmin with confirm button
  5. Superadmin clicks "✅ Подтвердить" → subscription +30 days, notify user
"""
import logging
import traceback
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session

from app.config import settings
from app.i18n import t
from app.models.shop import Shop
from app.models.subscription import Subscription
from app.models.user import User
from app.keyboards.worker_kb import payment_kb, paid_kb, main_menu_kb

router = Router()
logger = logging.getLogger(__name__)


def is_subscription_active(subscription: Subscription | None) -> bool:
    """Returns True if shop has an active subscription or trial."""
    if subscription is None:
        return False
    if subscription.status != "active":
        return False
    now = datetime.utcnow()
    if subscription.plan == "trial" and subscription.trial_ends_at:
        return now < subscription.trial_ends_at
    if subscription.expires_at:
        return now < subscription.expires_at
    return False


async def send_subscription_expired(message, shop: Shop, lang: str = "ru"):
    """Send payment prompt to user."""
    key = "trial_expired" if True else "subscription_inactive"
    await message.answer(t(key, lang), parse_mode="Markdown", reply_markup=payment_kb(lang))


# ── User clicks "Оплатить" ─────────────────────────────────────────────────

@router.callback_query(F.data == "pay:start")
async def cb_pay_start(
    call: CallbackQuery,
    shop: Shop | None = None,
    user: User | None = None,
):
    lang = user.language if user else "ru"
    slug = shop.slug if shop else "unknown"
    await call.message.edit_text(
        t("payment_instructions", lang, phone=settings.KASPI_PHONE, slug=slug),
        parse_mode="Markdown",
        reply_markup=paid_kb(lang),
    )
    await call.answer()


# ── User clicks "Я оплатил" ────────────────────────────────────────────────

@router.callback_query(F.data == "pay:confirm_user")
async def cb_paid_user(
    call: CallbackQuery,
    bot: Bot,
    shop: Shop | None = None,
    user: User | None = None,
):
    lang = user.language if user else "ru"
    await call.message.edit_text(t("payment_pending", lang), parse_mode="Markdown")
    await call.answer()

    if not shop:
        return

    # Notify superadmin
    shop_id = shop.id
    shop_name = shop.name
    slug = shop.slug
    user_name = user.first_name or f"id:{user.telegram_id}" if user else "unknown"

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Подтвердить оплату",
            callback_data=f"sadmin:pay_ok:{shop_id}:{call.from_user.id}",
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"sadmin:pay_no:{shop_id}:{call.from_user.id}",
        ),
    ]])
    try:
        await bot.send_message(
            settings.SUPERADMIN_ID,
            f"💰 *Новый платёж*\n\n"
            f"🏪 Сервис: *{shop_name}* (`{slug}`)\n"
            f"👤 Пользователь: {user_name} (tg: `{call.from_user.id}`)\n"
            f"💵 Сумма: *{settings.SUBSCRIPTION_PRICE} ₸*\n\n"
            f"Подтвердите получение платежа:",
            parse_mode="Markdown",
            reply_markup=admin_kb,
        )
    except Exception as e:
        logger.error(f"Failed to notify superadmin: {e}")


# ── Superadmin confirms/rejects payment ────────────────────────────────────

@router.callback_query(F.data.startswith("sadmin:pay_ok:"))
async def cb_superadmin_pay_ok(
    call: CallbackQuery,
    bot: Bot,
    db: Session | None = None,
):
    if call.from_user.id != settings.SUPERADMIN_ID:
        await call.answer("Нет доступа", show_alert=True)
        return

    parts = call.data.split(":")  # sadmin:pay_ok:{shop_id}:{user_tg_id}
    shop_id = int(parts[2])
    user_tg_id = int(parts[3])

    if db:
        try:
            sub = db.query(Subscription).filter(Subscription.shop_id == shop_id).first()
            if sub:
                sub.plan = "paid"
                sub.status = "active"
                sub.expires_at = datetime.utcnow() + timedelta(days=30)
                db.commit()
                logger.info(f"Subscription confirmed: shop={shop_id}")
        except Exception as e:
            logger.error(f"pay_ok DB error: {e}\n{traceback.format_exc()}")

    await call.message.edit_text(
        f"✅ Оплата подтверждена для shop_id={shop_id}. Подписка активирована на 30 дней."
    )
    await call.answer()

    # Notify the user
    try:
        user_lang = "ru"
        if db:
            from app.models.user import User as UserModel
            u = db.query(UserModel).filter(UserModel.telegram_id == user_tg_id).first()
            if u:
                user_lang = u.language or "ru"
                shop = db.query(Shop).filter(Shop.id == shop_id).first()
                is_admin = False
                from app.models.membership import Membership
                mem = db.query(Membership).filter(
                    Membership.user_id == u.id,
                    Membership.shop_id == shop_id,
                ).first()
                if mem:
                    is_admin = mem.role == "admin"
        await bot.send_message(
            user_tg_id,
            t("payment_confirmed", user_lang),
            parse_mode="Markdown",
            reply_markup=main_menu_kb(is_admin=is_admin, lang=user_lang),
        )
    except Exception as e:
        logger.error(f"Failed to notify user after pay_ok: {e}")


@router.callback_query(F.data.startswith("sadmin:pay_no:"))
async def cb_superadmin_pay_no(
    call: CallbackQuery,
    bot: Bot,
):
    if call.from_user.id != settings.SUPERADMIN_ID:
        await call.answer("Нет доступа", show_alert=True)
        return

    parts = call.data.split(":")
    user_tg_id = int(parts[3])

    await call.message.edit_text("❌ Платёж отклонён.")
    await call.answer()

    try:
        await bot.send_message(
            user_tg_id,
            "❌ Платёж не найден. Обратитесь в поддержку или повторите оплату.",
        )
    except Exception as e:
        logger.error(f"Failed to notify user pay_no: {e}")
