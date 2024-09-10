import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from app.db.db import (
    WildberriesCacheManager,
    TrackedWarehouseManager,
    BoxTypeManager,
    DateManager,
)
from app.handlers.base import router as base_router
from app.handlers.supply import router as supply_router
from app.config import Config
from app.dto import WarehouseShort

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str, db_path: str, chat_ids: list[int]):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()

        self.cache_manager = WildberriesCacheManager(db_path)
        self.tracked_warehouse_manager = TrackedWarehouseManager(db_path)
        self.box_type_manager = BoxTypeManager(db_path)
        self.date_manager = DateManager(db_path)

        self.chat_ids = chat_ids

    def setup_routers(self):
        self.dp.include_router(base_router)
        self.dp.include_router(supply_router)
        logger.debug("Routers have been set up")

    async def get_supply_data(self) -> list:
        logger.debug("Fetching supply data from cache")
        data = await self.cache_manager.get('supply_data')
        return data if data else {}

    async def send_notifications(self) -> None:
        supply_data = await self.get_supply_data()
        warehouses_to_track: list[WarehouseShort] = await self.tracked_warehouse_manager.get_all()
        box_types_to_track = await self.box_type_manager.get_all()
        dates_to_track = await self.date_manager.get_all()
        maximum_coefficient = await self.cache_manager.get("coefficient")
        if supply_data:
            notification = [
                f"{wh["warehouseName"]} {wh["boxTypeName"]} {wh["coefficient"]} {wh["date"][:10]}"
                for wh in supply_data
                if (
                    WarehouseShort(
                        id=wh["warehouseID"], name=wh["warehouseName"]
                    ) in warehouses_to_track
                    and wh["boxTypeName"] in box_types_to_track
                    and wh["date"] in dates_to_track
                    and int(wh["coefficient"]) != -1
                    and int(wh["coefficient"]) < maximum_coefficient
                )
            ]
            notification = "\n".join(notification)

            for chat_id in self.chat_ids:
                try:
                    await self.bot.send_message(chat_id, notification, parse_mode=ParseMode.HTML)
                    logger.info(f"Notification sent to chat {chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send notification to chat {chat_id}: {e}")
        else:
            logger.info("No new supply data available")

    async def schedule_notification(self) -> None:
        while True:
            logger.debug("Running periodic notification check")
            await self.send_notifications()
            await asyncio.sleep(60 // 6)

    async def run(self):
        logger.info("Initializing cache manager")
        await self.cache_manager.initialize()
        logger.info("Setting up routers")
        self.setup_routers()
        
        logger.info("Starting periodic notification task")
        notification_task = asyncio.create_task(self.schedule_notification())

        logger.info("Starting bot polling")
        try:
            await self.dp.start_polling(self.bot)
        finally:
            notification_task.cancel()
            await notification_task

async def main():
    logger.info("Starting Wildberries Notification Bot")
    load_dotenv()
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DB_PATH = Config.db_path
    CHAT_IDS = os.getenv("RECIEVER_IDS").split(",")

    if not BOT_TOKEN:
        logger.error("Bot token not found in environment variables")
        return

    bot = TelegramBot(BOT_TOKEN, DB_PATH, CHAT_IDS)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
