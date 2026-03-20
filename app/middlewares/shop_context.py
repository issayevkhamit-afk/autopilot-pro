"""
ShopContextMiddleware
Injects `db`, `user`, `shop`, `membership`, `subscription` into handler data.
Errors are caught and logged — handler always runs even if DB is unavailable.
"""
import logging
import traceback
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.models.shop import Shop
from app.models.membership import Membership
from app.models.subscription import Subscription

logger = logging.getLogger(__name__)


class ShopContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Defaults — handler always gets these keys even if DB fails
        data.setdefault("db", None)
        data.setdefault("user", None)
        data.setdefault("shop", None)
        data.setdefault("membership", None)
        data.setdefault("subscription", None)

        tg_user: TgUser | None = data.get("event_from_user")
        logger.info(f"Middleware: update from user={tg_user.id if tg_user else 'unknown'}")

        db: Session | None = None
        try:
            db = SessionLocal()
            data["db"] = db

            if tg_user:
                user = self._get_or_create_user(db, tg_user)
                data["user"] = user

                membership = (
                    db.query(Membership)
                    .filter(Membership.user_id == user.id)
                    .order_by(Membership.created_at.desc())
                    .first()
                )
                data["membership"] = membership

                if membership:
                    shop = db.query(Shop).filter(Shop.id == membership.shop_id).first()
                    data["shop"] = shop
                    if shop:
                        data["subscription"] = (
                            db.query(Subscription)
                            .filter(Subscription.shop_id == shop.id)
                            .first()
                        )

        except Exception as e:
            logger.error(f"ShopContextMiddleware DB error: {e}\n{traceback.format_exc()}")
            # Continue with defaults — do not crash the handler

        try:
            return await handler(event, data)
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

    @staticmethod
    def _get_or_create_user(db: Session, tg_user: TgUser) -> User:
        user = db.query(User).filter(User.telegram_id == tg_user.id).first()
        if not user:
            user = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                language=tg_user.language_code or "ru",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New user created: tg_id={tg_user.id}")
        return user
