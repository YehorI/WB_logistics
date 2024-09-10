from aiogram import Router, types
from aiogram.filters import Command


from app.utils.messages.messages import get_message_text_by_key
from app.keyboards.keyboards import AddTrackingItemsMenuKeyboard
from app.config import Config
from app.db.db import (
    WildberriesCacheManager,
)


router = Router()

cache_manager = WildberriesCacheManager(Config.db_path)


@router.message(Command(commands=["start"]))
async def start_command(message: types.Message) -> None:
    text = get_message_text_by_key("start")

    coefficient_now: int | None = await cache_manager.get("coefficient")

    keyboard = AddTrackingItemsMenuKeyboard(
        coefficient=coefficient_now
    ).build()

    await message.answer(
        text=text,
        reply_markup=keyboard
    )


@router.message(Command(commands=["help"]))
async def help_command(message: types.Message) -> None:
    text = get_message_text_by_key("help")
    await message.answer(text)
