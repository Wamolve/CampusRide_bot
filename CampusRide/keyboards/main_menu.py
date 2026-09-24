from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def get_main_reply_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🚕 Создать поездку"),
                KeyboardButton(text="🚗 Найти поездку"),
            ],
            [
                KeyboardButton(text="👤 Мой профиль"),
                KeyboardButton(text="ℹ️ О сервисе"),
            ],
        ],
        resize_keyboard=True,
    )