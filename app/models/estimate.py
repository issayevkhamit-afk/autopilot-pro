from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, Text, DateTime, func
from app.database import Base


class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    car_make = Column(String(100), nullable=True)
    car_model = Column(String(100), nullable=True)
    car_year = Column(String(10), nullable=True)
    car_vin = Column(String(50), nullable=True)
    raw_input = Column(Text, nullable=True)          # original text/transcript
    total_labor = Column(Numeric(12, 2), default=0)
    total_parts = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), default=0)
    status = Column(String(30), default="draft")     # draft | confirmed | cancelled
    pdf_path = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class EstimateItem(Base):
    __tablename__ = "estimate_items"

    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(20), nullable=False)   # labor | part
    name = Column(String(255), nullable=False)
    qty = Column(Numeric(8, 2), default=1)
    unit_price = Column(Numeric(12, 2), default=0)
    total_price = Column(Numeric(12, 2), default=0)
    is_manual = Column(String(5), default="false")   # true if price not found in DB
