import asyncio
import logging
import traceback

from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update, BotCommand

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
try:
    Base.metadata.create_all(bind=engine)
    logger.info("DB tables created/verified OK")
except Exception as e:
    logger.error(f"DB create_all failed: {e}\n{traceback.format_exc()}")

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
    # Set bot commands menu
    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="Начать / подключиться к сервису"),
            BotCommand(command="newshop", description="Создать новый автосервис"),
            BotCommand(command="admin", description="Панель администратора"),
        ])
        logger.info("Bot commands set OK")
    except Exception as e:
        logger.error(f"set_my_commands failed: {e}")

    if settings.WEBHOOK_URL:
        webhook_url = f"{settings.WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}"
        try:
            await bot.set_webhook(
                url=webhook_url,
                secret_token=settings.SECRET_TOKEN,
                drop_pending_updates=True,
            )
            logger.info(f"Webhook set: {webhook_url}")
        except Exception as e:
            logger.error(f"set_webhook failed: {e}\n{traceback.format_exc()}")
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
        logger.warning(f"Webhook: bad secret token received")
        return Response(status_code=403)

    try:
        data = await request.json()
        logger.info(f"Incoming update: {data.get('update_id')} type={list(k for k in data if k != 'update_id')}")
        update = Update(**data)
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"webhook_handler error: {e}\n{traceback.format_exc()}")

    return Response(status_code=200)


@app.get("/")
def health():
    return {"status": "AutoPilot Pro is running 🚀"}


@app.get("/health")
def health_check():
    return {"status": "OK"}


@app.get("/debug-webhook-info")
async def debug_webhook_info():
    try:
        info = await bot.get_webhook_info()
        me = await bot.get_me()
        return {
            "bot_username": me.username,
            "bot_id": me.id,
            "webhook_url": info.url,
            "pending_updates": info.pending_update_count,
            "last_error": info.last_error_message,
            "last_error_date": str(info.last_error_date) if info.last_error_date else None,
            "configured_path": WEBHOOK_PATH,
            "secret_token_set": bool(settings.SECRET_TOKEN),
        }
    except Exception as e:
        return {"error": str(e)}
