from config import (
    PRESET_FROM,
    PRESET_MEETING_POINTS,
    PRESET_TIMES,
    PRESET_TO,
)
from database import crud
from keyboards.ride_keyboards import get_preset_kb, get_seats_kb
from states.ride_states import CreateRideStates, ProfileStates
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

router = Router()


@router.message(F.text == "🚕 Создать поездку")
async def start_create_ride(message: Message, state: FSMContext):
    user = await crud.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала заполни профиль через команду /start!")
        return

    await message.answer(
        "📍 **Шаг 1 из 5: Откуда выезжаем?**\nВыбери вариант или укажи свой адрес:",
        reply_markup=get_preset_kb(PRESET_FROM, "from"),
        parse_mode="Markdown",
    )
    await state.set_state(CreateRideStates.from_location)


@router.callback_query(
    F.data.startswith("from:"), CreateRideStates.from_location
)
async def process_from_preset(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])
    chosen = PRESET_FROM[index]
    if chosen == "📍 Свой адрес":
        await callback.message.edit_text(
            "Введи адрес отправления текстом в сообщении:"
        )
        await state.set_state(CreateRideStates.custom_from)
    else:
        await state.update_data(from_location=chosen)
        await ask_to_location(callback.message, state)


@router.message(CreateRideStates.custom_from)
async def process_custom_from(message: Message, state: FSMContext):
    await state.update_data(from_location=message.text.strip())
    await ask_to_location(message, state)


async def ask_to_location(target, state: FSMContext):
    text = "🎯 **Шаг 2 из 5: Куда едем?**\nВыбери пункт назначения:"
    kb = get_preset_kb(PRESET_TO, "to")
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await target.answer(text, reply_markup=kb, parse_mode="Markdown")
    await state.set_state(CreateRideStates.to_location)


@router.callback_query(F.data.startswith("to:"), CreateRideStates.to_location)
async def process_to_preset(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])
    chosen = PRESET_TO[index]
    if chosen == "📍 Свой адрес":
        await callback.message.edit_text(
            "Введи адрес назначения текстом в сообщении:"
        )
        await state.set_state(CreateRideStates.custom_to)
    else:
        await state.update_data(to_location=chosen)
        await ask_meeting_point(callback.message, state)


@router.message(CreateRideStates.custom_to)
async def process_custom_to(message: Message, state: FSMContext):
    await state.update_data(to_location=message.text.strip())
    await ask_meeting_point(message, state)


async def ask_meeting_point(target, state: FSMContext):
    text = "🚪 **Шаг 3 из 5: Где точка сбора попутчиков?**\nГде встречаемся перед посадкой:"
    kb = get_preset_kb(PRESET_MEETING_POINTS, "meeting")
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await target.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await state.set_state(CreateRideStates.meeting_point)


@router.callback_query(
    F.data.startswith("meeting:"), CreateRideStates.meeting_point
)
async def process_meeting_preset(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])
    chosen = PRESET_MEETING_POINTS[index]
    if chosen == "📍 Указать вручную":
        await callback.message.edit_text("Опиши место сбора сообщением:")
        await state.set_state(CreateRideStates.custom_meeting)
    else:
        await state.update_data(meeting_point=chosen)
        await ask_departure_time(callback.message, state)


@router.message(CreateRideStates.custom_meeting)
async def process_custom_meeting(message: Message, state: FSMContext):
    await state.update_data(meeting_point=message.text.strip())
    await ask_departure_time(message, state)


async def ask_departure_time(target, state: FSMContext):
    text = "⏰ **Шаг 4 из 5: Время выезда?**\nВыбери интервал или напиши точное время:"
    kb = get_preset_kb(PRESET_TIMES, "time")
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await target.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await state.set_state(CreateRideStates.departure_time)


@router.callback_query(
    F.data.startswith("time:"), CreateRideStates.departure_time
)
async def process_time_preset(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])
    chosen = PRESET_TIMES[index]
    if chosen == "🕒 Указать точное время":
        await callback.message.edit_text(
            "Введи точное время выезда (например, `09:15` или `21:40`):",
            parse_mode="Markdown",
        )
        await state.set_state(CreateRideStates.custom_time)
    else:
        await state.update_data(departure_time=chosen)
        await ask_seats(callback.message, state)


@router.message(CreateRideStates.custom_time)
async def process_custom_time(message: Message, state: FSMContext):
    await state.update_data(departure_time=message.text.strip())
    await ask_seats(message, state)


async def ask_seats(target, state: FSMContext):
    text = "👥 **Шаг 5 из 5: Сколько попутчиков ищешь?**\n(В машине кроме тебя свободно мест):"
    kb = get_seats_kb()
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await target.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await state.set_state(CreateRideStates.max_seats)


@router.callback_query(
    F.data.startswith("seats:"), CreateRideStates.max_seats
)
async def process_seats(callback: CallbackQuery, state: FSMContext):
    seats = int(callback.data.split(":")[1])
    data = await state.get_data()

    lobby = await crud.create_lobby(
        host_id=callback.from_user.id,
        from_loc=data["from_location"],
        to_loc=data["to_location"],
        meeting=data["meeting_point"],
        dep_time=data["departure_time"],
        seats=seats,
    )
    await state.clear()

    await callback.message.edit_text(
        f"🎉 **Поездка #{lobby.id} успешно создана!**\n\n"
        f"📍 Откуда: {lobby.from_location}\n"
        f"🎯 Куда: {lobby.to_location}\n"
        f"🚪 Сбор: {lobby.meeting_point}\n"
        f"⏰ Выезд: {lobby.departure_time}\n"
        f"👥 Свободно мест: {lobby.max_seats}\n\n"
        f"Попутчики увидят поездку во вкладке «🚗 Найти поездку». Когда будете на месте, нажми «Завершить поездку» для сплита счета.",
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "cancel_action")
async def cancel_flow(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено.")