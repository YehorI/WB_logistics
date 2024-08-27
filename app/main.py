import asyncio
import logging
import os

from dotenv import load_dotenv
from app.api_monitor import WildberriesSupplyAPIMonitor
from app.bot import TelegramBot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Service:
    def __init__(self):
        load_dotenv()
        self.monitor = None
        self.bot = None

    async def start_monitor(self):
        token = os.getenv("WB_SUPPLY_API_TOKEN")
        api_url = os.getenv("WB_SUPPLY_API_URL")
        requests_per_minute = 5
        self.monitor = WildberriesSupplyAPIMonitor(token, api_url, requests_per_minute)
        await self.monitor.run()

    async def start_bot(self):
        BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        DB_PATH = 'cache.db'
        CHAT_IDS = [364633558]  # Replace with actual chat IDs

        if not BOT_TOKEN:
            logger.error("Bot token not found in environment variables")
            return

        self.bot = TelegramBot(BOT_TOKEN, DB_PATH, CHAT_IDS)
        await self.bot.run()

    async def run_all(self):
        logger.info("Starting Wildberries Supply Monitoring and Notification System")
        monitor_task = asyncio.create_task(self.start_monitor())
        bot_task = asyncio.create_task(self.start_bot())

        try:
            await asyncio.gather(monitor_task, bot_task)
        except asyncio.CancelledError:
            logger.info("Shutting down...")
        finally:
            for task in [monitor_task, bot_task]:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            logger.info("Shutdown complete")

async def test_monitor():
    service = Service()
    await service.start_monitor()

async def test_bot():
    service = Service()
    await service.start_bot()

if __name__ == "__main__":
    service = Service()
    asyncio.run(service.run_all())
