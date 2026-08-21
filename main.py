import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from db.database import db
from handlers import start, menu, mp, webapp

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def main():
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN not set")
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(mp.router)
    dp.include_router(webapp.router)
    await db.connect()
    me = await bot.get_me()
    log.info("Bot @%s started", me.username)
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
