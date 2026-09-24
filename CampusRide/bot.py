import asyncio
import logging
from config import settings
from database.engine import init_db
from handlers import create_ride, manage_ride, start, view_rides
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO)


async def main():
    # Инициализация базы данных
    await init_db()

    # Создание бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Подключение роутеров
    dp.include_router(start.router)
    dp.include_router(create_ride.router)
    dp.include_router(view_rides.router)
    dp.include_router(manage_ride.router)

    logging.info("🚕 Бот CampusRide 4A успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())