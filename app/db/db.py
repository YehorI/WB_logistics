import aiosqlite
import json
from typing import Any, List

from pathlib import Path

from app.config import Config
from app.dto import WarehouseShort, Warehouse

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        raise NotImplementedError

    async def execute(self, query: str, parameters: tuple = ()):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, parameters)
            await db.commit()

    async def fetch_one(self, query: str, parameters: tuple = ()):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, parameters) as cursor:
                return await cursor.fetchone()

    async def fetch_all(self, query: str, parameters: tuple = ()):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, parameters) as cursor:
                return await cursor.fetchall()

    async def clear_table(self, table_name: str):
        await self.execute(f'DELETE FROM {table_name}')


class WildberriesCacheManager(DatabaseManager):
    """Manages cache of Wildberries API call"""
    async def initialize(self):
        await self.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

    async def set(self, key: str, value: Any):
        serialized_value = json.dumps(value)
        await self.execute('''
            INSERT OR REPLACE INTO cache (key, value)
            VALUES (?, ?)
        ''', (key, serialized_value))

    async def get(self, key: str) -> Any:
        result = await self.fetch_one('SELECT value FROM cache WHERE key = ?', (key,))
        
        if result is None:
            return None
        
        return json.loads(result[0])

    async def clear(self):
        await self.clear_table('cache')


class TrackedWarehouseManager(DatabaseManager):
    """Controls set of warehouses in db. warehouse_name and id should be unique"""
    async def initialize(self):
        await self.execute('''
            CREATE TABLE IF NOT EXISTS warehouses (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        ''')

    async def get_all(self) -> list[WarehouseShort]:
        results = await self.fetch_all('SELECT id, name FROM warehouses')
        return [
            WarehouseShort(id=result[0], name=result[1])
            for result in results
        ]

    async def add(self, warehouse: WarehouseShort):
        try:
            await self.execute('INSERT INTO warehouses (id, name) VALUES (?, ?)', (warehouse.id, warehouse.name))
        except aiosqlite.IntegrityError:
            raise ValueError(f"Warehouse with id '{warehouse_id}' or name '{warehouse_name}' already exists")

    async def drop(self, warehouse_id: int):
        result = await self.fetch_one('SELECT id FROM warehouses WHERE id = ?', (warehouse_id,))
        if result is None:
            raise ValueError(f"Warehouse with id '{warehouse_id}' not found")
        
        await self.execute('DELETE FROM warehouses WHERE id = ?', (warehouse_id,))

    async def get(self, warehouse_id: int) -> dict:
        result = await self.fetch_one('SELECT id, name FROM warehouses WHERE id = ?', (warehouse_id,))
        if result is None:
            raise ValueError(f"Warehouse with id '{warehouse_id}' not found")
        return {"id": result[0], "name": result[1]}

    async def clear(self):
        await self.clear_table('warehouses')


class BoxTypeManager(DatabaseManager):
    """Controls set of box types in db. box_type_name should be unique"""
    async def initialize(self):
        await self.execute('''
            CREATE TABLE IF NOT EXISTS box_types (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        ''')

    async def get_all(self) -> list[str]:
        results = await self.fetch_all('SELECT name FROM box_types')
        return [result[0] for result in results]

    async def add(self, name: str):
        try:
            await self.execute('INSERT INTO box_types (name) VALUES (?)', (name,))
        except aiosqlite.IntegrityError:
            raise ValueError(f"Box type '{name}' already exists")

    async def drop(self, name: str):
        result = await self.fetch_one('SELECT name FROM box_types WHERE name = ?', (name,))
        if result is None:
            raise ValueError(f"Box type '{name}' not found")
        
        await self.execute('DELETE FROM box_types WHERE name = ?', (name,))

    async def clear(self):
        await self.clear_table('box_types')


class DateManager(DatabaseManager):
    """Controls set of dates in db. date should be unique"""
    async def initialize(self):
        await self.execute('''
            CREATE TABLE IF NOT EXISTS dates (
                id INTEGER PRIMARY KEY,
                date TEXT UNIQUE NOT NULL
            )
        ''')

    async def get_all(self) -> list[str]:
        results = await self.fetch_all('SELECT date FROM dates')
        return [result[0] for result in results]

    async def add(self, date: str) -> None:
        try:
            await self.execute('INSERT INTO dates (date) VALUES (?)', (date,))
        except aiosqlite.IntegrityError:
            raise ValueError(f"Date '{date}' already exists")

    async def drop(self, date: str) -> None:
        result = await self.fetch_one('SELECT date FROM dates WHERE date = ?', (date,))
        if result is None:
            raise ValueError(f"Date '{date}' not found")
        
        await self.execute('DELETE FROM dates WHERE date = ?', (date,))

    async def clear(self) -> None:
        await self.clear_table('dates')
