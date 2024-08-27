import aiosqlite
import json
from typing import Any

class WildberriesCacheManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            await db.commit()

    async def set(self, key: str, value: Any):
        serialized_value = json.dumps(value)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO cache (key, value)
                VALUES (?, ?)
            ''', (key, serialized_value))
            await db.commit()

    async def get(self, key: str) -> Any:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT value FROM cache WHERE key = ?', (key,)) as cursor:
                result = await cursor.fetchone()
            
            if result is None:
                return None
            
            return json.loads(result[0])

    async def delete(self, key: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM cache WHERE key = ?', (key,))
            await db.commit()

    async def clear(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM cache')
            await db.commit()

    async def get_all(self) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT key, value FROM cache') as cursor:
                results = await cursor.fetchall()
            
            return {key: json.loads(value) for key, value in results}
