import re
import datetime

from functools import wraps

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.db.db import (
    WildberriesCacheManager,
    TrackedWarehouseManager,
    BoxTypeManager,
    DateManager,
)
from app.config import Config
from app.keyboards.keyboards import (
    Buttons,
    WarehousesKeyboard,
    BoxTypesKeyboard,
    AddTrackingItemsMenuKeyboard,
    DateKeyboard,
)
from app.dto import (
    WarehouseShort,
    RightDate,
)
from app.utils.messages.messages import get_message_text_by_key


class CoefStates(StatesGroup):
    awaiting_coefficient = State()


router = Router()

cache_manager = WildberriesCacheManager(Config.db_path)
tracked_warehouse_manager = TrackedWarehouseManager(Config.db_path)
box_type_manager = BoxTypeManager(Config.db_path)
date_manager = DateManager(Config.db_path)


def delete_previous_message(menu_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(message: types.Message, *args, **kwargs):
            # Delete the previous menu message
            previous_message_id = await cache_manager.get(f"previous_{menu_type}_message_id")
            if previous_message_id:
                try:
                    await message.bot.delete_message(message.chat.id, previous_message_id)
                except Exception:
                    pass  # If message deletion fails, we simply continue
            
            # Send a loading message
            loading_message = await message.answer("⏳ Loading...")
            
            # Call the original function
            result = await func(message, *args, **kwargs)
            
            # Delete the loading message
            try:
                await loading_message.delete()
            except Exception:
                pass
            
            # Store the ID of the new menu message
            if isinstance(result, types.Message):
                await cache_manager.set(f"previous_{menu_type}_message_id", result.message_id)
            
            return result
        return wrapper
    return decorator


@router.message(F.text.regexp(Buttons.COEFFICIENT_F_REPLY.value.regex))
async def awaiting_coefficient(message: types.Message, state: FSMContext) -> None:
    text = get_message_text_by_key("enter_coefficient")
    await state.set_state(CoefStates.awaiting_coefficient)
    await message.answer(text=text)


@router.message(CoefStates.awaiting_coefficient)
async def set_coefficient(message: types.Message, state: FSMContext):
    try:
        coef = int(message.text)
        await cache_manager.set("coefficient", coef)
        await state.clear()
        text = get_message_text_by_key("coefficient_success")
        keyboard = AddTrackingItemsMenuKeyboard(
            coefficient=coef
        ).build()
        await message.answer(text=text, reply_markup=keyboard)
    except ValueError:
        text = get_message_text_by_key("coefficient_failure")
        await message.answer(text=text)
        await state.clear()


@router.message(Command(commands=["supply"]))
async def supply_command(message: types.Message) -> None:
    supply_data = await cache_manager.get('supply_data')
    if supply_data:
        await message.answer(f"Latest supply data: {str(supply_data[:11])}")
    else:
        await message.answer("No supply data available at the moment.")


@router.message(Command(commands=["clearall"]))
async def clear_warehouses(message: types.Message) -> None:
    await tracked_warehouse_manager.clear()
    await box_type_manager.clear()
    await date_manager.clear()


@router.message(F.text == Buttons.ADD_WAREHOUSE_REPLY.value.text)
@delete_previous_message("warehouse")
async def get_add_warehouse_menu(message: types.Message) -> None:
    warehouses_raw = await cache_manager.get("supply_data")

    warehouses: list[WarehouseShort] = [
        WarehouseShort(id=wh["warehouseID"], name=wh["warehouseName"])
        for wh in warehouses_raw
    ]
    warehouses = list(set(warehouses))
    warehouses.sort(
        key=lambda x: re.sub(r'^СЦ\s+', '', x.name)
    )

    tracked_warehouses: list[WarehouseShort] = await tracked_warehouse_manager.get_all()
    marked_warehouses = [
        WarehouseShort(
            id=wh.id,
            name=(
                f"🏫 {wh.name}" if wh in tracked_warehouses
                else wh.name
            )
        )
        for wh in warehouses
    ]

    keyboard = WarehousesKeyboard(
        marked_warehouses
    ).build()

    return await message.answer(
        "Список складов ниже",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("wh:"))
async def toggle_warehouse(clbck: types.CallbackQuery) -> None:
    warehouse_id: int = int(clbck.data.split(":")[1].replace("🏫 ", ""))
    tracked_warehouses: list[WarehouseShort] = await tracked_warehouse_manager.get_all()

    warehouses_raw = await cache_manager.get("supply_data")
    for wh in warehouses_raw:
        if wh["warehouseID"] == warehouse_id:
            warehouse_name = wh["warehouseName"]
            break

    if warehouse_id in [wh.id for wh in tracked_warehouses]:
        await tracked_warehouse_manager.drop(warehouse_id)
        action = "removed from"
    else:
        await tracked_warehouse_manager.add(
            WarehouseShort(id=warehouse_id, name=warehouse_name)
        )
        action = "added to"

    warehouses: list[WarehouseShort] = [
        WarehouseShort(id=wh["warehouseID"], name=wh["warehouseName"])
        for wh in warehouses_raw
    ]
    warehouses = list(set(warehouses))
    warehouses.sort(
        key=lambda x: re.sub(r'^СЦ\s+', '', x.name)
    )

    tracked_warehouses: list[WarehouseShort] = await tracked_warehouse_manager.get_all()
    marked_warehouses = [
        WarehouseShort(
            id=wh.id,
            name=(
                f"🏫 {wh.name}" if wh in tracked_warehouses
                else wh.name
            )
        )
        for wh in warehouses
    ]

    new_keyboard = WarehousesKeyboard(marked_warehouses).build()

    await clbck.message.edit_text(
        f"Warehouse {warehouse_name} {action} tracking list. Select more warehouses:",
        reply_markup=new_keyboard
    )

    await clbck.answer(f"Warehouse {warehouse_name} {action} tracking list")


@router.message(F.text == Buttons.ADD_BOX_TYPE_REPLY.value.text)
@delete_previous_message("box_type")
async def get_add_box_type_menu(message: types.Message) -> None:
    warehouses = await cache_manager.get("supply_data")

    box_type_names = [wh["boxTypeName"] for wh in warehouses]
    box_type_names = list(set(box_type_names))
    box_type_names.sort(
        key=lambda x: re.sub(r'^СЦ\s+', '', x)
    )

    tracked_box_types = await box_type_manager.get_all()
    box_type_names = [
        f"📦 {box_type_name}" if box_type_name in tracked_box_types
        else box_type_name
        for box_type_name in box_type_names
    ]

    keyboard = BoxTypesKeyboard(box_type_names).build()

    return await message.answer(
        str(tracked_box_types),
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("bt:"))
async def toggle_box_type(clbck: types.CallbackQuery) -> None:
    box_type_name = clbck.data.split(":")[1].replace("📦 ", "")
    tracked_box_types = await box_type_manager.get_all()

    if box_type_name in tracked_box_types:
        await box_type_manager.drop(box_type_name)
        action = "removed from"
    else:
        await box_type_manager.add(box_type_name)
        action = "added to"

    # Update the keyboard
    supply_data = await cache_manager.get("supply_data")
    box_type_names = list(set(bt["boxTypeName"] for bt in supply_data))
    box_type_names.sort(key=lambda x: re.sub(r'^СЦ\s+', '', x))

    tracked_box_types = await box_type_manager.get_all()
    box_type_names = [
        f"📦 {bt_name}" if bt_name in tracked_box_types else bt_name
        for bt_name in box_type_names
    ]

    new_keyboard = BoxTypesKeyboard(box_type_names).build()

    await clbck.message.edit_text(
        f"Box type {box_type_name} {action} tracking list. Select more box types:",
        reply_markup=new_keyboard
    )

    await clbck.answer(f"Box type {box_type_name} {action} tracking list")


@router.message(F.text == Buttons.ADD_DATE_REPLY.value.text)
@delete_previous_message("date")
async def get_add_date_menu(message: types.Message) -> None:
    tracked_dates = [RightDate.from_string(date) for date in await date_manager.get_all()]

    today = RightDate(datetime.datetime.today())
    actual_dates = [today + i for i in range(15)]
    
    marked_dates = [
        (f"🗓️ {date.display_date()}", date) if date in tracked_dates
        else (f"{date.display_date()}", date)
        for date in actual_dates
    ]

    keyboard = DateKeyboard(marked_dates).build()

    return await message.answer(
        "Select dates to track:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("dt:"))
async def toggle_date(clbck: types.CallbackQuery) -> None:
    date_str = ":".join(clbck.data.split(":")[1:])
    tracked_date = RightDate.from_string(date_str)
    
    tracked_dates = await date_manager.get_all()

    if tracked_date.to_string() in tracked_dates:
        await date_manager.drop(tracked_date.to_string())
        action = "removed from"
    else:
        await date_manager.add(tracked_date.to_string())
        action = "added to"

    # Update the keyboard
    today = RightDate(datetime.datetime.today())
    actual_dates = [today + i for i in range(15)]
    
    tracked_dates = [RightDate.from_string(date) for date in await date_manager.get_all()]

    marked_dates = [
        (f"🗓️ {date.display_date()}", date) if date in tracked_dates
        else (f"{date.display_date()}", date)
        for date in actual_dates
    ]

    new_keyboard = DateKeyboard(marked_dates).build()

    await clbck.message.edit_text(
        f"Date {tracked_date.display_date()} {action} tracking list. Select more dates:",
        reply_markup=new_keyboard
    )

    await clbck.answer(f"Date {tracked_date.display_date()} {action} tracking list")


__all__ = ['router']
