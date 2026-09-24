import math
from database import crud
from database.models import RideStatus
from keyboards.ride_keyboards import (
    get_host_confirm_payment_kb,
    get_payment_passenger_kb,
)
from states.ride_states import SplitPaymentStates
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

router = Router()


@router.callback_query(F.data.startswith("cancel_ride:"))
async def cancel_ride_by_host(callback: CallbackQuery):
    lobby_id = int(callback.data.split(":")[1])
    lobby = await crud.get_lobby_by_id(lobby_id)
    if not lobby or lobby.host_id != callback.from_user.id:
        await callback.answer("Вы не организатор этой поездки.", show_alert=True)
        return

    await crud.update_lobby_status(lobby_id, RideStatus.CANCELLED)

    # Оповещаем всех пассажиров
    for p in lobby.passengers:
        try:
            await callback.bot.send_message(
                p.user_id,
                f"🚫 Организатор отменил поездку #{lobby.id} ({lobby.from_location} ➔ {lobby.to_location}).",
            )
        except Exception:
            pass

    await callback.message.edit_text(
        f"❌ Поездка #{lobby.id} успешно отменена."
    )
    await callback.answer("Поездка отменена.")


@router.callback_query(F.data.startswith("finish_ride:"))
async def request_total_cost(callback: CallbackQuery, state: FSMContext):
    lobby_id = int(callback.data.split(":")[1])
    lobby = await crud.get_lobby_by_id(lobby_id)
    if not lobby or lobby.host_id != callback.from_user.id:
        await callback.answer("Вы не организатор этой поездки.", show_alert=True)
        return

    if not lobby.passengers:
        await crud.update_lobby_status(lobby_id, RideStatus.FINISHED, cost=0)
        await callback.message.edit_text(
            f"✅ Поездка #{lobby.id} завершена без попутчиков."
        )
        return

    await state.set_state(SplitPaymentStates.total_cost)
    await state.update_data(lobby_id=lobby_id)
    await callback.message.answer(
        f"🚕 **Завершение поездки #{lobby.id}**\n\n"
        f"Попутчиков в машине: {len(lobby.passengers)}\n"
        f"Введите итоговую сумму чека из приложения такси в рублях (например: `320` или `450`):",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(SplitPaymentStates.total_cost)
async def process_split_cost(message: Message, state: FSMContext):
    try:
        cost = float(message.text.strip().replace(",", "."))
        if cost <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректную сумму числом (например `340`):"
        )
        return

    data = await state.get_data()
    lobby_id = data["lobby_id"]
    await state.clear()

    lobby = await crud.get_lobby_by_id(lobby_id)
    if not lobby:
        await message.answer("Поездка не найдена.")
        return

    total_people = len(lobby.passengers) + 1  # Пассажиры + Хост
    per_person = math.ceil(cost / total_people)

    await crud.update_lobby_status(
        lobby_id, RideStatus.FINISHED, cost=per_person
    )
    host = lobby.host

    await message.answer(
        f"✅ **Расчёт произведён!**\n\n"
        f"• Общий чек: {cost:.0f} ₽\n"
        f"• Всего участников: {total_people} чел.\n"
        f"• К оплате с каждого попутчика: **{per_person} ₽**\n\n"
        f"Бот автоматически отправил квитанции и твои реквизиты СБП всем попутчикам!",
        parse_mode="Markdown",
    )

    # Рассылаем квитанции попутчикам
    for p in lobby.passengers:
        try:
            await message.bot.send_message(
                p.user_id,
                f"🧾 **Чек по поездке #{lobby.id}**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Маршрут: {lobby.from_location} ➔ {lobby.to_location}\n"
                f"К оплате: **{per_person} ₽**\n\n"
                f"💳 **Реквизиты для перевода по СБП:**\n"
                f"• Номер: `{host.sbp_phone}`\n"
                f"• Банк: {host.sbp_bank}\n"
                f"• Получатель: {host.full_name}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"После перевода нажмите кнопку ниже 👇",
                reply_markup=get_payment_passenger_kb(lobby.id),
                parse_mode="Markdown",
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("paid_sent:"))
async def passenger_sent_payment(callback: CallbackQuery):
    lobby_id = int(callback.data.split(":")[1])
    lobby = await crud.get_lobby_by_id(lobby_id)
    user = await crud.get_user(callback.from_user.id)

    if lobby and user:
        await crud.set_passenger_paid_status(
            lobby_id, callback.from_user.id, status=1
        )
        await callback.message.edit_text(
            "✅ Вы уведомили организатора о переводе. Ожидайте подтверждения!"
        )
        try:
            await callback.bot.send_message(
                lobby.host_id,
                f"💸 Попутчик {user.full_name} (@{user.username or 'нет'}, комн. {user.room_number}) нажал «Я перевёл деньги». Проверьте поступление на счет СБП:",
                reply_markup=get_host_confirm_payment_kb(lobby.id, user.id),
            )
        except Exception:
            pass
    await callback.answer("Уведомление отправлено!")


@router.callback_query(F.data.startswith("confirm_pay:"))
async def host_confirmed_payment(callback: CallbackQuery):
    parts = callback.data.split(":")
    lobby_id = int(parts[1])
    passenger_id = int(parts[2])

    await crud.set_passenger_paid_status(lobby_id, passenger_id, status=2)
    await callback.message.edit_text("✅ Оплата успешно подтверждена!")

    try:
        await callback.bot.send_message(
            passenger_id,
            f"🎉 Организатор подтвердил получение вашей оплаты за поездку #{lobby_id}. Спасибо!",
        )
    except Exception:
        pass
    await callback.answer("Подтверждено!")