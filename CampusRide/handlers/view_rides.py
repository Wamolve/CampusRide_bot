from database import crud
from keyboards.ride_keyboards import get_lobby_card_kb
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

router = Router()


def format_lobby_card(lobby) -> str:
    passengers_text = ""
    passengers_count = len(lobby.passengers)
    for i, p in enumerate(lobby.passengers, 1):
        status_icon = (
            "✅ Оплачено"
            if p.is_paid == 2
            else ("⏳ Перевёл" if p.is_paid == 1 else "💳 Не оплачено")
        )
        passengers_text += f"  {i}. {p.user.full_name} (@{p.user.username or 'нет'}, комн. {p.user.room_number}) — {status_icon}\n"

    free_seats = lobby.max_seats - passengers_count
    free_seats_str = "🟢 " * free_seats if free_seats > 0 else "🔴 Мест нет"

    return (
        f"🚕 **ПОЕЗДКА #{lobby.id}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 **Откуда:** {lobby.from_location}\n"
        f"🎯 **Куда:** {lobby.to_location}\n"
        f"🚪 **Сбор:** {lobby.meeting_point}\n"
        f"⏰ **Время выезда:** {lobby.departure_time}\n"
        f"👤 **Организатор:** {lobby.host.full_name} (@{lobby.host.username or 'нет'}, комн. {lobby.host.room_number})\n\n"
        f"👥 **Экипаж ({passengers_count + 1}/{lobby.max_seats + 1}):**\n"
        f"  👑 Хост: {lobby.host.full_name}\n"
        f"{passengers_text}"
        f"Свободно слотов: {free_seats_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )


@router.message(F.text == "🚗 Найти поездку")
async def show_active_rides(message: Message):
    lobbies = await crud.get_active_lobbies()
    if not lobbies:
        await message.answer(
            "🚗 Сейчас нет активных поездок из кампуса.\n"
            "Будь первым — нажми «🚕 Создать поездку»!"
        )
        return

    await message.answer(f"🔎 Найдено активных поездок: **{len(lobbies)}**")
    for lobby in lobbies:
        is_host = lobby.host_id == message.from_user.id
        is_passenger = any(
            p.user_id == message.from_user.id for p in lobby.passengers
        )
        is_full = len(lobby.passengers) >= lobby.max_seats

        await message.answer(
            format_lobby_card(lobby),
            reply_markup=get_lobby_card_kb(
                lobby.id, is_host, is_passenger, is_full
            ),
            parse_mode="Markdown",
        )


@router.callback_query(F.data.startswith("join_ride:"))
async def handle_join_ride(callback: CallbackQuery):
    lobby_id = int(callback.data.split(":")[1])
    user = await crud.get_user(callback.from_user.id)
    if not user:
        await callback.answer(
            "Сначала настройте профиль через команду /start", show_alert=True
        )
        return

    success = await crud.add_passenger(lobby_id, callback.from_user.id)
    if success:
        await callback.answer("🎉 Вы успешно заняли место!", show_alert=True)
        lobby = await crud.get_lobby_by_id(lobby_id)
        # Оповещаем хоста
        try:
            await callback.bot.send_message(
                lobby.host_id,
                f"🔔 К вашей поездке #{lobby.id} присоединился попутчик: {user.full_name} (@{user.username or 'нет'}, комн. {user.room_number})!",
            )
        except Exception:
            pass

        # Обновляем сообщение
        is_host = lobby.host_id == callback.from_user.id
        is_passenger = any(
            p.user_id == callback.from_user.id for p in lobby.passengers
        )
        is_full = len(lobby.passengers) >= lobby.max_seats
        await callback.message.edit_text(
            format_lobby_card(lobby),
            reply_markup=get_lobby_card_kb(
                lobby.id, is_host, is_passenger, is_full
            ),
            parse_mode="Markdown",
        )
    else:
        await callback.answer(
            "Не удалось занять место (поездка заполнена или вы уже в ней).",
            show_alert=True,
        )


@router.callback_query(F.data.startswith("leave_ride:"))
async def handle_leave_ride(callback: CallbackQuery):
    lobby_id = int(callback.data.split(":")[1])
    success = await crud.remove_passenger(lobby_id, callback.from_user.id)
    if success:
        await callback.answer("Вы покинули поездку.", show_alert=True)
        lobby = await crud.get_lobby_by_id(lobby_id)
        if lobby:
            try:
                await callback.bot.send_message(
                    lobby.host_id,
                    f"⚠️ Попутчик {callback.from_user.full_name} отменил бронь в поездке #{lobby.id}. Освободилось 1 место!",
                )
            except Exception:
                pass
            is_host = lobby.host_id == callback.from_user.id
            is_passenger = any(
                p.user_id == callback.from_user.id for p in lobby.passengers
            )
            is_full = len(lobby.passengers) >= lobby.max_seats
            await callback.message.edit_text(
                format_lobby_card(lobby),
                reply_markup=get_lobby_card_kb(
                    lobby.id, is_host, is_passenger, is_full
                ),
                parse_mode="Markdown",
            )
    else:
        await callback.answer("Ошибка при отмене брони.", show_alert=True)


@router.callback_query(F.data.startswith("refresh_ride:"))
async def handle_refresh_ride(callback: CallbackQuery):
    lobby_id = int(callback.data.split(":")[1])
    lobby = await crud.get_lobby_by_id(lobby_id)
    if not lobby:
        await callback.message.edit_text("❌ Поездка завершена или отменена.")
        return

    is_host = lobby.host_id == callback.from_user.id
    is_passenger = any(
        p.user_id == callback.from_user.id for p in lobby.passengers
    )
    is_full = len(lobby.passengers) >= lobby.max_seats

    await callback.message.edit_text(
        format_lobby_card(lobby),
        reply_markup=get_lobby_card_kb(
            lobby.id, is_host, is_passenger, is_full
        ),
        parse_mode="Markdown",
    )
    await callback.answer("Обновлено!")