"""
/start handler — supports deep links: /start SHOP_SLUG
First user to join a slug becomes admin, rest become workers.
"""
import logging
import secrets
from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.shop import Shop
from app.models.membership import Membership
from app.models.subscription import Subscription
from app.models.user import User
from app.keyboards.worker_kb import main_menu_kb

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    db: Session,
    user: User,
    shop: Shop | None,
    membership: Membership | None,
):
    slug = (command.args or "").strip() or None

    # ── Deep link flow ────────────────────────────────────────────────────
    if slug:
        target_shop = db.query(Shop).filter(Shop.slug == slug).first()

        if not target_shop:
            # Create new shop for this slug
            target_shop = Shop(slug=slug, name="Мой автосервис")
            db.add(target_shop)
            db.flush()

            # Give it a 14-day trial
            sub = Subscription(
                shop_id=target_shop.id,
                plan="trial",
                status="active",
                trial_ends_at=datetime.utcnow() + timedelta(days=14),
            )
            db.add(sub)
            db.commit()
            db.refresh(target_shop)
            logger.info(f"New shop created: slug={slug} id={target_shop.id}")

        # Check if user already has membership in this shop
        existing = (
            db.query(Membership)
            .filter(Membership.user_id == user.id, Membership.shop_id == target_shop.id)
            .first()
        )
        if not existing:
            # First member = admin, rest = worker
            member_count = db.query(Membership).filter(Membership.shop_id == target_shop.id).count()
            role = "admin" if member_count == 0 else "worker"
            existing = Membership(user_id=user.id, shop_id=target_shop.id, role=role)
            db.add(existing)
            db.commit()

        shop = target_shop
        membership = existing

    # ── No shop context ───────────────────────────────────────────────────
    if not shop:
        await message.answer(
            "👋 Добро пожаловать в *AutoPilot Pro*!\n\n"
            "Для подключения к автосервису используйте пригласительную ссылку "
            "или создайте свой сервис командой /newshop",
            parse_mode="Markdown",
        )
        return

    # ── Greeting ──────────────────────────────────────────────────────────
    is_admin = membership and membership.role == "admin"
    role_label = "Администратор" if is_admin else "Механик"

    await message.answer(
        f"👋 Привет, *{message.from_user.first_name}*!\n\n"
        f"🏪 Сервис: *{shop.name}*\n"
        f"👤 Роль: _{role_label}_\n\n"
        f"{'Управляйте сервисом через ⚙️ Админ панель.' if is_admin else 'Отправьте описание ремонта — текстом или голосом.'}",
        parse_mode="Markdown",
        reply_markup=main_menu_kb(is_admin=is_admin),
    )

    # Nudge new admin to set up shop
    if is_admin and not shop.logo_path:
        await message.answer(
            "💡 *Совет:* Настройте ваш сервис:\n"
            "• Загрузите логотип\n"
            "• Укажите цены на работы\n"
            "• Загрузите прайс запчастей\n\n"
            "➡️ Нажмите «⚙️ Админ панель»",
            parse_mode="Markdown",
        )


@router.message(lambda m: m.text == "/newshop")
async def cmd_new_shop(message: Message, db: Session, user: User):
    """Create a new shop with a random slug and make sender admin."""
    slug = secrets.token_hex(4).upper()  # e.g. "A3F9C12B"
    shop = Shop(slug=slug, name=f"Сервис {message.from_user.first_name}")
    db.add(shop)
    db.flush()

    sub = Subscription(
        shop_id=shop.id,
        plan="trial",
        status="active",
        trial_ends_at=datetime.utcnow() + timedelta(days=14),
    )
    db.add(sub)

    membership = Membership(user_id=user.id, shop_id=shop.id, role="admin")
    db.add(membership)
    db.commit()

    bot_username = (await message.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start={slug}"

    await message.answer(
        f"✅ Сервис создан!\n\n"
        f"🏪 Название: *{shop.name}*\n"
        f"🔑 Код: `{slug}`\n\n"
        f"📎 Пригласительная ссылка:\n`{invite_link}`\n\n"
        f"Отправьте её механикам, чтобы они подключились.",
        parse_mode="Markdown",
        reply_markup=main_menu_kb(is_admin=True),
    )
