import datetime
from enum import Enum

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, KeyboardButton

from app.dto import (
    WarehouseShort,
    RightDate,
)

class KeyboardType(Enum):
    REPLY = "reply"
    INLINE = "inline"

ButtonType = KeyboardType

class Button:
    def __init__(self,
        text: str,
        callback_data: str | None = None,
        type: KeyboardType = KeyboardType.REPLY,
        regex: str = None
    ):
        self.text = text
        self.callback_data = callback_data
        self.type = type
        self.regex = regex

class Buttons(Enum):
    QUESTION = Button("💌 Задать вопрос")
    SHOP = Button("📍 Наш магазин")
    BONUS = Button("🎁 Бонус за отзыв")
    START = Button("🌐 Вернуться в главное меню")
    SCREENSHOT = Button("✅ Я оставил(-а) отзыв")
    ACCEPT_BONUS = Button("✅ Принять", "accept_bonus", ButtonType.INLINE)
    DECLINE_BONUS = Button("❌ Отклонить", "decline_bonus", ButtonType.INLINE)
    DELETE_POST = Button("❌ Удалить пост", "delete_post", ButtonType.INLINE)
    SUBSCRIBE = Button("📬 Подписаться")
    UNSUBSCRIBE = Button("🔕 Отписаться")
    BONUS_ACCEPTED = Button("👍 Принято", "placeholder", ButtonType.INLINE)
    BONUS_DECLINED = Button("👎 Отклонено", "placeholder", ButtonType.INLINE)
    POST_DELETED = Button("👎 Пост удален", "delete_post", ButtonType.INLINE)

    ADD_WAREHOUSE_REPLY = Button("🏫 Добавить склад для отслеживания")
    ADD_BOX_TYPE_REPLY = Button("📦 Добавить тип поставки")
    ADD_DATE_REPLY = Button("🗓️ Добавить даты")

    COEFFICIENT_F_REPLY = Button(
        text="💵 Установить коэффициент (сейчас {})",
        regex=r"^💵 Установить коэффициент \(сейчас [\d\.]+\)$"
    )

class KeyboardConfig:
    def __init__(self, button_keys: list[Button | Buttons], adjust: tuple[int, ...] | bool = False):
        self.button_keys = button_keys
        self.adjust = adjust


class BaseKeyboard:
    def __init__(self, config: KeyboardConfig):
        self.config = config

    def _process_button(self, button: Button | Buttons) -> Button:
        if isinstance(button, Enum):
            return button.value
        return button

    def build(self) -> ReplyKeyboardBuilder | InlineKeyboardBuilder:
        reply_buttons = []
        inline_buttons = []

        for button in self.config.button_keys:
            processed_button = self._process_button(button)
            if processed_button.type == ButtonType.REPLY:
                reply_buttons.append(KeyboardButton(text=processed_button.text))
            else:
                inline_buttons.append(InlineKeyboardButton(
                    text=processed_button.text, 
                    callback_data=processed_button.callback_data or processed_button.text[:64]
                ))

        if reply_buttons:
            builder = ReplyKeyboardBuilder()
            for button in reply_buttons:
                builder.add(button)
            keyboard_type = KeyboardType.REPLY
        else:
            builder = InlineKeyboardBuilder()
            for button in inline_buttons:
                builder.add(button)
            keyboard_type = KeyboardType.INLINE

        if self.config.adjust:
            builder.adjust(*self.config.adjust if isinstance(self.config.adjust, tuple) else self.config.adjust)

        return builder.as_markup(resize_keyboard=keyboard_type == KeyboardType.REPLY)


class GreetingsKeyboard(BaseKeyboard):
    def __init__(self, is_subscribed: bool):
        button_keys = [
            Buttons.QUESTION,
            Buttons.SHOP,
            Buttons.BONUS,
            Buttons.UNSUBSCRIBE if is_subscribed else Buttons.SUBSCRIBE
        ]
        super().__init__(KeyboardConfig(button_keys=button_keys, adjust=(2, 2)))


class BonusResponseKeyboard(BaseKeyboard):
    def __init__(self, is_accepted: bool):
        button_key = Buttons.BONUS_ACCEPTED if is_accepted else Buttons.BONUS_DECLINED
        super().__init__(KeyboardConfig(button_keys=[button_key]))


class DeletePostKeyboard(BaseKeyboard):
    def __init__(self, is_deleted: bool):
        button_key = Buttons.POST_DELETED if is_deleted else Buttons.DELETE_POST
        super().__init__(KeyboardConfig(button_keys=[button_key]))


class WarehousesKeyboard(BaseKeyboard):
    def __init__(self,
        warehouses: list[WarehouseShort]
    ):
        buttons = [
            Button(wh.name, f"wh:{wh.id}", ButtonType.INLINE)
            for wh in warehouses
        ]
        super().__init__(KeyboardConfig(button_keys=buttons, adjust=(1, 2)))


class BoxTypesKeyboard(BaseKeyboard):
    def __init__(self,
        box_types: list[str]
    ):
        buttons = [
            Button(box_type, f"bt:{box_type}", ButtonType.INLINE)
            for box_type in box_types
        ]
        super().__init__(KeyboardConfig(button_keys=buttons))


class DateKeyboard(BaseKeyboard):
    def __init__(self, dates: list[tuple[str, RightDate]]):
        buttons = [
            Button(date[0], f"dt:{date[1].to_string()}", ButtonType.INLINE)
            for date in dates
        ]
        super().__init__(KeyboardConfig(button_keys=buttons, adjust=(3,)))


class AddTrackingItemsMenuKeyboard(BaseKeyboard):
    def __init__(self,
        coefficient: int | None,
    ):
        coefficient = coefficient if coefficient is not None else 0

        coef_button = Button(
            Buttons.COEFFICIENT_F_REPLY.value.text.format(coefficient)
        )

        buttons = [
            Buttons.ADD_WAREHOUSE_REPLY,
            Buttons.ADD_BOX_TYPE_REPLY,
            Buttons.ADD_DATE_REPLY,
            coef_button,
        ]
        super().__init__(KeyboardConfig(button_keys=buttons, adjust=(2, 1)))


class PredefinedKeyboard(BaseKeyboard):
    GREETINGS = KeyboardConfig([Buttons.QUESTION, Buttons.SHOP, Buttons.BONUS], adjust=(2, 1))
    BONUS = KeyboardConfig([Buttons.SCREENSHOT, Buttons.START])
    BONUS_RESPONSE = KeyboardConfig([Buttons.ACCEPT_BONUS, Buttons.DECLINE_BONUS])
    DELETE_POST = KeyboardConfig([Buttons.DELETE_POST])

    def __init__(self, config: KeyboardConfig):
        super().__init__(config)

# Usage examples:
# async def start_command(message: types.Message):
#     user = await get_user(message.from_user.id)
#     keyboard = GreetingsKeyboard(user.is_subscribed).build()
#     await message.answer("Welcome!", reply_markup=keyboard)

# async def bonus_response_callback(callback_query: types.CallbackQuery):
#     is_accepted = callback_query.data == "accept_bonus"
#     keyboard = BonusResponseKeyboard(is_accepted).build()
#     await callback_query.message.edit_reply_markup(reply_markup=keyboard)

# async def delete_post_callback(callback_query: types.CallbackQuery):
#     is_deleted = await delete_post(callback_query.data)
#     keyboard = DeletePostKeyboard(is_deleted).build()
#     await callback_query.message.edit_reply_markup(reply_markup=keyboard)

# async def greetings_command(message: types.Message):
#     keyboard = PredefinedKeyboard(PredefinedKeyboard.GREETINGS).build()
#     await message.answer("Greetings!", reply_markup=keyboard)