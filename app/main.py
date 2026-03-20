import asyncio
import logging
import os

from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from app.config import settings
from app.database import engine, Base
import app.models  # noqa: F401 — register all models

from app.middlewares.shop_context import ShopContextMiddleware
from app.handlers.start import router as start_router
from app.handlers.admin import router as admin_router
from app.handlers.worker import router as worker_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create tables ──────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Bot & Dispatcher ────────────────────────────────────────────────────────
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

dp.update.middleware(ShopContextMiddleware())
dp.include_router(start_router)
dp.include_router(admin_router)
dp.include_router(worker_router)

# ── FastAPI ─────────────────────────────────────────────────────────────────
app = FastAPI(title="AutoPilot Pro", docs_url=None, redoc_url=None)

WEBHOOK_PATH = f"/webhook/{settings.BOT_TOKEN}"


@app.on_event("startup")
async def on_startup():
    if settings.WEBHOOK_URL:
        webhook_url = f"{settings.WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}"
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.SECRET_TOKEN,
            drop_pending_updates=True,
        )
        logger.info(f"Webhook set: {webhook_url}")
    else:
        logger.warning("WEBHOOK_URL not set — bot will not receive updates via webhook")


@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()


@app.post(WEBHOOK_PATH)
async def webhook_handler(request: Request):
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if token != settings.SECRET_TOKEN:
        return Response(status_code=403)
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return Response(status_code=200)


@app.get("/")
def health():
    return {"status": "AutoPilot Pro is running 🚀"}


@app.get("/health")
def health_check():
    return {"status": "OK"}
