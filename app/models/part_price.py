from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, DateTime, func
from app.database import Base


class PartPrice(Base):
    __tablename__ = "part_prices"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=True)
    part_number = Column(String(100), nullable=True)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    unit = Column(String(30), default="pcs")  # pcs | liter | set
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
