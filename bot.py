import asyncio
import logging
from aiogram import Bot, Dispatcher, html
from aiogram.filters import CommandStart
from aiogram.types import Message

# Вставьте сюда токен вашего бота, полученный от @BotFather
TOKEN = "8929522753:AAG4rb7zImXg2cfzQU9azjeMpRK7KTwnunE"

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Получаем имя пользователя (выбираем имя, если есть фамилия — добавляем, либо берем username)
    user_name = message.from_user.first_name
    
    # Формируем текст ответа по вашему шаблону
    text = (
        f"👋🏻 Привет, {html.bold(user_name)}!\n\n"
        f"Ты попал в официальный бот технического отдела 71-75. "
        f"Для получения более подробной информации введи /help.\n"
        f"Для открытия панели — /panel\n\n\n"
        f"Твоя роль: Зам. куратора тех. специалистов"
    )
    
    # Отправляем сообщение с поддержкой HTML-разметки (для жирного шрифта)
    await message.answer(text, parse_mode="HTML")

async def main() -> None:
    bot = Bot(token=TOKEN)
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
