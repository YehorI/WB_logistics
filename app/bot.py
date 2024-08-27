import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.utils.markdown import hbold
from dotenv import load_dotenv

from app.db import WildberriesCacheManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)





class TelegramBot:
    def __init__(self, token: str, db_path: str, chat_ids: list[int]):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.cache_manager = WildberriesCacheManager(db_path)
        self.chat_ids = chat_ids

    async def start_command(self, message: types.Message) -> None:
        logger.info(f"User {message.from_user.id} started the bot")
        await message.answer("Welcome to the Wildberries Supply Notification Bot!")

    async def help_command(self, message: types.Message) -> None:
        logger.info(f"User {message.from_user.id} requested help")
        help_text = "This bot sends notifications about Wildberries supply updates."
        await message.answer(help_text)

    async def get_supply_data(self) -> list:
        logger.debug("Fetching supply data from cache")
        data = await self.cache_manager.get('supply_data')
        return data if data else {}

    async def send_notifications(self) -> None:
        supply_data = await self.get_supply_data()
        if supply_data:

            notification = str(supply_data[:11])
            
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
            await asyncio.sleep(60 // 5)

    async def run(self):
        logger.info("Initializing cache manager")
        await self.cache_manager.initialize()
        logger.info("Registering handlers")
        self.dp.message.register(self.start_command, Command(commands=["start"]))
        self.dp.message.register(self.help_command, Command(commands=["help"]))
        
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
    DB_PATH = 'cache.db'  # Make sure this matches the path used by the monitor service
    CHAT_IDS = [364633558]  # Replace with actual chat IDs

    if not BOT_TOKEN:
        logger.error("Bot token not found in environment variables")
        return

    bot = TelegramBot(BOT_TOKEN, DB_PATH, CHAT_IDS)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
