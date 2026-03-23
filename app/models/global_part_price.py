from sqlalchemy import Column, Integer, String, Numeric, DateTime, func
from app.database import Base


class GlobalPartPrice(Base):
    __tablename__ = "global_part_prices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False, index=True)
    brand = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    source = Column(String(50), default="manual")  # manual | csv | scraper
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
