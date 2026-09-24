from database import crud
from keyboards.main_menu import get_main_reply_kb
from states.ride_states import ProfileStates
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await crud.get_user(message.from_user.id)
    if not user:
        await message.answer(
            "👋 Привет! Добро пожаловать в **CampusRide 4A** — сервис совместных поездок на такси для жителей кампуса.\n\n"
            "Давай настроим твой профиль для быстрых расчетов по СБП.\n"
            "Введи номер твоей комнаты в кампусе (например: `906` или `312`):",
            parse_mode="Markdown",
        )
        await state.set_state(ProfileStates.room_number)
    else:
        await message.answer(
            f"🚕 Рад видеть тебя снова, {user.full_name}!\n"
            f"Твоя комната: **{user.room_number}**\n"
            f"СБП: `{user.sbp_phone}` ({user.sbp_bank})",
            reply_markup=get_main_reply_kb(),
            parse_mode="Markdown",
        )


@router.message(ProfileStates.room_number)
async def process_room(message: Message, state: FSMContext):
    await state.update_data(room_number=message.text.strip())
    await message.answer(
        "📱 Укажи твой номер телефона для переводов по СБП (например, `+79991234567`):",
        parse_mode="Markdown",
    )
    await state.set_state(ProfileStates.sbp_phone)


@router.message(ProfileStates.sbp_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(sbp_phone=message.text.strip())
    await message.answer(
        "🏦 Укажи банк для переводов по СБП (например: `Т-Банк`, `Сбер`, `Альфа`):",
        parse_mode="Markdown",
    )
    await state.set_state(ProfileStates.sbp_bank)


@router.message(ProfileStates.sbp_bank)
async def process_bank(message: Message, state: FSMContext):
    data = await state.get_data()
    full_name = message.from_user.full_name
    username = message.from_user.username

    await crud.create_or_update_user(
        user_id=message.from_user.id,
        username=username,
        full_name=full_name,
        room_number=data["room_number"],
        sbp_phone=data["sbp_phone"],
        sbp_bank=message.text.strip(),
    )
    await state.clear()
    await message.answer(
        "✅ Профиль успешно настроен! Теперь ты можешь создавать поездки или присоединяться к попутчикам.",
        reply_markup=get_main_reply_kb(),
    )


@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message, state: FSMContext):
    user = await crud.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return

    await message.answer(
        f"👤 **Твой профиль CampusRide:**\n\n"
        f"• Имя: {user.full_name} (@{user.username or 'нет'})\n"
        f"• Комната в 4А: **{user.room_number}**\n"
        f"• Телефон СБП: `{user.sbp_phone}`\n"
        f"• Банк СБП: {user.sbp_bank}\n"
        f"• Рейтинг надежности: ⭐ {user.rating:.1f}\n\n"
        f"Для изменения данных отправь /start заново.",
        parse_mode="Markdown",
    )


@router.message(F.text == "ℹ️ О сервисе")
async def show_info(message: Message):
    await message.answer(
        "🚕 **CampusRide 4A — Как это работает:**\n\n"
        "1. **Организатор** создает поездку, выбирает маршрут, время и точку встречи.\n"
        "2. **Попутчики** бронируют свободные места (до 3 человек).\n"
        "3. Вы встречаетесь на крыльце/в холле 4А и едете вместе.\n"
        "4. В конце поездки Организатор вводит сумму чека из Яндекс Go — бот автоматически делит счет поровну и присылает всем реквизиты СБП.",
        parse_mode="Markdown",
    )