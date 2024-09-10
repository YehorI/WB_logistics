import os
import asyncio
import aiohttp
import logging

from dotenv import load_dotenv

from aiolimiter import AsyncLimiter
from app.db.db import (
    WildberriesCacheManager,
    TrackedWarehouseManager,
    BoxTypeManager,
    DateManager,
)
from app.config import Config


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WildberriesSupplyAPIMonitor:
    def __init__(
        self,
        token: str,
        api_url: str,
        db_path: str,
        requests_per_minute: int = 6,
    ):
        self.token = token
        self.api_url = api_url
        self.requests_per_minute = requests_per_minute
        self.rate_limiter = AsyncLimiter(requests_per_minute, 60)

        self.cache_manager = WildberriesCacheManager(db_path)
        self.tracked_warehouse_manager = TrackedWarehouseManager(db_path)
        self.box_type_manager = BoxTypeManager(db_path)
        self.date_manager = DateManager(db_path)

        self.cache_refresh_interval = 60 // requests_per_minute  # Calculate refresh interval in seconds
        self.is_running = False

    async def initialize(self):
        await self.cache_manager.initialize()
        await self.tracked_warehouse_manager.initialize()
        await self.box_type_manager.initialize()
        await self.date_manager.initialize()

    async def make_request(self) -> list:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        async with self.rate_limiter:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()

    async def get_supply_data(self) -> list:
        cached_data = await self.cache_manager.get('supply_data')
        if cached_data is not None:
            return cached_data
        
        try:
            fresh_data = await self.make_request()
            await self.cache_manager.set('supply_data', fresh_data)
            return fresh_data
        except aiohttp.ClientError as e:
            logger.error(f"An error occurred while fetching supply data: {e}")
            return []

    async def start_cache_refresh(self):
        while self.is_running:
            try:
                await self.get_supply_data()
                logger.info("Cache refreshed successfully")
            except Exception as e:
                logger.error(f"Error refreshing cache: {e}")
            await asyncio.sleep(self.cache_refresh_interval)

    async def run(self):
        logger.info("Starting WildberriesSupplyAPIMonitor")
        await self.initialize()
        self.is_running = True
        refresh_task = asyncio.create_task(self.start_cache_refresh())
        try:
            # Keep the monitor running until stopped
            while self.is_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("WildberriesSupplyAPIMonitor stopping...")
        finally:
            self.is_running = False
            refresh_task.cancel()
            try:
                await refresh_task
            except asyncio.CancelledError:
                pass
            logger.info("WildberriesSupplyAPIMonitor stopped")

    def stop(self):
        self.is_running = False

async def main():
    load_dotenv()

    token = os.getenv("WB_SUPPLY_API_TOKEN")
    api_url = os.getenv("WB_SUPPLY_API_URL")
    db_path = Config.db_path
    requests_per_minute = 5

    monitor = WildberriesSupplyAPIMonitor(token, api_url, db_path, requests_per_minute)
    try:
        await monitor.run()
    except KeyboardInterrupt:
        monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())
