"""
ShopContextMiddleware
Injects `db`, `user`, `shop`, `membership` into handler data for every update.
"""
import logging
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
        db: Session = SessionLocal()
        try:
            tg_user: TgUser | None = data.get("event_from_user")
            if tg_user:
                user = self._get_or_create_user(db, tg_user)
                membership = (
                    db.query(Membership)
                    .filter(Membership.user_id == user.id)
                    .order_by(Membership.created_at.desc())
                    .first()
                )
                shop = db.query(Shop).filter(Shop.id == membership.shop_id).first() if membership else None
                subscription = (
                    db.query(Subscription).filter(Subscription.shop_id == shop.id).first()
                    if shop else None
                )
                data["db"]           = db
                data["user"]         = user
                data["shop"]         = shop
                data["membership"]   = membership
                data["subscription"] = subscription
            else:
                data["db"] = db

            return await handler(event, data)
        finally:
            db.close()

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
        return user
