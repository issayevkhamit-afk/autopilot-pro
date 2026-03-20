"""
/start handler — supports deep links: /start SHOP_SLUG
First user to join a slug becomes admin, rest become workers.
"""
import logging
import secrets
import traceback
from aiogram import Router
from aiogram.filters import CommandStart, CommandObject, Command
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
    db: Session | None = None,
    user: User | None = None,
    shop: Shop | None = None,
    membership: Membership | None = None,
):
    logger.info(f"/start from user={message.from_user.id} args={command.args!r}")

    # ── Minimal guaranteed response (works even if DB is down) ────────────
    if db is None:
        logger.error("/start: db is None — DB connection failed")
        await message.answer(
            "⚠️ Сервис временно недоступен. Попробуйте позже.",
            reply_markup=main_menu_kb(is_admin=False),
        )
        return

    slug = (command.args or "").strip() or None

    try:
        # ── Deep link flow ────────────────────────────────────────────────────
        if slug:
            target_shop = db.query(Shop).filter(Shop.slug == slug).first()

            if not target_shop:
                target_shop = Shop(slug=slug, name="Мой автосервис")
                db.add(target_shop)
                db.flush()

                sub = Subscription(
                    shop_id=target_shop.id,
                    plan="trial",
                    status="active",
                    trial_ends_at=datetime.utcnow() + timedelta(days=1),
                )
                db.add(sub)
                db.commit()
                db.refresh(target_shop)
                logger.info(f"New shop created: slug={slug} id={target_shop.id}")

            existing = (
                db.query(Membership)
                .filter(Membership.user_id == user.id, Membership.shop_id == target_shop.id)
                .first()
            )
            if not existing:
                member_count = db.query(Membership).filter(Membership.shop_id == target_shop.id).count()
                role = "admin" if member_count == 0 else "worker"
                existing = Membership(user_id=user.id, shop_id=target_shop.id, role=role)
                db.add(existing)
                db.commit()
                logger.info(f"New membership: user={user.id} shop={target_shop.id} role={role}")

            shop = target_shop
            membership = existing

    except Exception as e:
        logger.error(f"/start DB error: {e}\n{traceback.format_exc()}")
        await message.answer(
            "⚠️ Ошибка при подключении к сервису. Попробуйте ещё раз.",
            reply_markup=main_menu_kb(is_admin=False),
        )
        return

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
    logger.info(f"/start: sent greeting to user={message.from_user.id} is_admin={is_admin}")

    if is_admin and not shop.logo_path:
        await message.answer(
            "💡 *Совет:* Настройте ваш сервис:\n"
            "• Загрузите логотип\n"
            "• Укажите цены на работы\n"
            "• Загрузите прайс запчастей\n\n"
            "➡️ Нажмите «⚙️ Админ панель»",
            parse_mode="Markdown",
        )


@router.message(Command("newshop"))
async def cmd_new_shop(
    message: Message,
    db: Session | None = None,
    user: User | None = None,
):
    logger.info(f"/newshop from user={message.from_user.id}")

    if db is None or user is None:
        await message.answer("⚠️ Сервис временно недоступен. Попробуйте позже.")
        return

    try:
        slug = secrets.token_hex(4).upper()
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

        mem = Membership(user_id=user.id, shop_id=shop.id, role="admin")
        db.add(mem)
        db.commit()
        logger.info(f"New shop via /newshop: slug={slug} user={user.id}")

    except Exception as e:
        logger.error(f"/newshop DB error: {e}\n{traceback.format_exc()}")
        await message.answer("⚠️ Не удалось создать сервис. Попробуйте ещё раз.")
        return

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
