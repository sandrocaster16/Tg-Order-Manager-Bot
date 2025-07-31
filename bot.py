import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from database.engine import create_db, session_maker
from database.orm_query import orm_get_orders, orm_get_platforms
from google_sheets.sheets_api import sync_orders_to_sheet, sync_platforms_to_sheet

from handlers import user_commands, platform_management, order_processing
from middlewares.db import DataBaseSession
from middlewares.auth import AdminAuthMiddleware

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

ADMIN_IDS = {int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(',')}

async def main():
    await create_db()

    async with session_maker() as session:
        all_orders = await orm_get_orders(session)
        await sync_orders_to_sheet(all_orders)
        
        all_platforms = await orm_get_platforms(session)
        await sync_platforms_to_sheet(all_platforms)

    default_properties = DefaultBotProperties(parse_mode="HTML")
    bot = Bot(token=os.getenv("BOT_TOKEN"), default=default_properties)
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    dp.update.middleware(AdminAuthMiddleware(admin_ids=ADMIN_IDS))

    dp.include_router(user_commands.router)
    dp.include_router(platform_management.router)
    dp.include_router(order_processing.router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")