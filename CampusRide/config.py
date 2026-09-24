from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    DB_URL: str = "sqlite+aiosqlite:///campus_ride.db"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

# Пресеты для быстрого выбора в кампусе
PRESET_FROM = [
    "🏢 Кампус 4А (Бр. Кашириных 127)",
    "🎓 ЮУрГУ (Главный корпус / 3б)",
    "🚆 Ж/Д Вокзал (Челябинск-Главный)",
    "📍 Свой адрес",
]

PRESET_TO = [
    "🎓 ЮУрГУ (Главный / 3б корпус)",
    "🏢 Кампус 4А (Бр. Кашириных 127)",
    "🛍️ ТРК «Родник»",
    "🍕 Белый Рынок (ул. Тернопольская)",
    "🚆 Ж/Д Вокзал",
    "📍 Свой адрес",
]

PRESET_MEETING_POINTS = [
    "🚪 Главное крыльцо 4А",
    "🛋️ Холл 1 этажа (у диванов)",
    "🚧 Шлагбаум / парковка",
    "🚏 Остановка «8-й микрорайон»",
    "📍 Указать вручную",
]

PRESET_TIMES = [
    "⚡ Через 10 минут (Срочно)",
    "⏰ Через 20 минут",
    "🎓 К паре на 09:45 (выезд в 09:15)",
    "🎓 К паре на 11:30 (выезд в 11:00)",
    "🕒 Указать точное время",
]