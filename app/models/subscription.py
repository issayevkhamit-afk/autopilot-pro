from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, func
from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, unique=True)
    plan = Column(String(30), default="trial")   # trial | basic | pro
    status = Column(String(20), default="active")  # active | inactive | expired
    trial_ends_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
