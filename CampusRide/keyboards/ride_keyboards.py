from config import PRESET_FROM, PRESET_MEETING_POINTS, PRESET_TIMES, PRESET_TO
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_preset_kb(items: list[str], prefix: str):
    buttons = [
        [InlineKeyboardButton(text=item, callback_data=f"{prefix}:{i}")]
        for i, item in enumerate(items)
    ]
    buttons.append(
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_seats_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 1 место", callback_data="seats:1"
                ),
                InlineKeyboardButton(
                    text="👥 2 места", callback_data="seats:2"
                ),
                InlineKeyboardButton(
                    text="👥 3 места", callback_data="seats:3"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена", callback_data="cancel_action"
                )
            ],
        ]
    )


def get_lobby_card_kb(
    lobby_id: int, is_host: bool, is_passenger: bool, is_full: bool
):
    buttons = []
    if is_host:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="💳 Завершить поездку и разделить счет",
                    callback_data=f"finish_ride:{lobby_id}",
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text="❌ Отменить поездку",
                    callback_data=f"cancel_ride:{lobby_id}",
                )
            ]
        )
    elif is_passenger:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🚪 Покинуть поездку",
                    callback_data=f"leave_ride:{lobby_id}",
                )
            ]
        )
    else:
        if not is_full:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="💺 Занять место",
                        callback_data=f"join_ride:{lobby_id}",
                    )
                ]
            )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔄 Обновить статус",
                callback_data=f"refresh_ride:{lobby_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_passenger_kb(lobby_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Я перевёл деньги хосту",
                    callback_data=f"paid_sent:{lobby_id}",
                )
            ]
        ]
    )


def get_host_confirm_payment_kb(lobby_id: int, passenger_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить получение",
                    callback_data=f"confirm_pay:{lobby_id}:{passenger_id}",
                )
            ]
        ]
    )