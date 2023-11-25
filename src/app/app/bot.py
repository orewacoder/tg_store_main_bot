import os

from aiogram import Dispatcher, Bot
from app.routes.router import router
from aiogram.fsm.storage.redis import RedisStorage
from app.db.redisdb import redis
import os
import backoff
from aiogram.types import BotCommand


bot = Bot(os.getenv('TELEGRAM_BOT_TOKEN'), parse_mode="HTML")
dp = Dispatcher(storage=RedisStorage(redis))
dp.include_router(router)


@backoff.on_exception(backoff.expo, Exception, max_tries=5, max_time=30)
async def setup(bot_instance):
    print("Setting up webhook...")
    webhook_path = f"{os.getenv('SERVER_HOST')}/api/events/telegram-webhook"
    await bot_instance.set_my_commands([
        BotCommand(command="start", description="Start using this bot"),
        BotCommand(command="catalog", description="Discover products"),
        BotCommand(command="search", description="Search products"),
        BotCommand(command="support", description="Get help from support team"),
        BotCommand(command="help", description="How to use this bot"),
    ])

    await bot_instance.set_webhook(url=webhook_path, drop_pending_updates=True)
    print("Webhook set up successfully")
