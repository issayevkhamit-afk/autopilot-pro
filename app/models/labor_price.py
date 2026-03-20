from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, DateTime, func
from app.database import Base


class LaborPrice(Base):
    __tablename__ = "labor_prices"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    unit = Column(String(30), default="flat")  # flat | hour
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
