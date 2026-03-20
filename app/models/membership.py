from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, UniqueConstraint, func
from app.database import Base


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "shop_id", name="uq_user_shop"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default="worker")  # admin | worker
    created_at = Column(DateTime, server_default=func.now())
