from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class AiPrompt(Base):
    __tablename__ = "ai_prompts"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)  # e.g. 'extract_repair'
    prompt = Column(Text, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
