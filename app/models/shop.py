from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, default="Мой автосервис")
    slug = Column(String(50), unique=True, nullable=False, index=True)  # deep-link key
    logo_path = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    country = Column(String(5), default="kz")
    language = Column(String(5), default="ru")
    currency = Column(String(10), default="KZT")
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
