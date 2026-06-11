import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# 🔹 НАСТРОЙКИ (замени на свои)
BOT_TOKEN = "8767884883:AAFozNT2_EMdMZxf1zE5SpznYt2V0FtiNcU"
GROUP_CHAT_ID = -1002010429964  # ID супергруппы (должен начинаться с -100)

# Включаем логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Проверка, что бот работает только в ЛС
def is_private(message: Message) -> bool:
    return message.chat.type == "private"

@dp.message(Command("text"))
async def send_to_topic(message: Message):
    # 1. Игнорируем, если пишут не в ЛС
    if not is_private(message):
        return

    # 2. Парсим сообщение
    # Убираем команду /text и разбиваем строку: сначала ID топика, потом текст
    args = message.text.split(maxsplit=2)  # ['/text', 'ID', 'текст']
    
    if len(args) < 3:
        await message.reply(
            "❌ Неверный формат.\n"
            "Используй: `/text ID_топика твой текст`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        topic_id = int(args[1])       # ID топика (число)
        user_text = args[2]           # Текст сообщения
    except ValueError:
        await message.reply("❌ ID топика должен быть числом.")
        return

    # 3. Отправляем сообщение в нужный топик супергруппы
    try:
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=user_text,
            message_thread_id=topic_id  # магия отправки в топик
        )
        await message.reply(f"✅ Сообщение отправлено в топик {topic_id}.")
    
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        await message.reply(
            "❌ Не удалось отправить сообщение.\n"
            "Проверь:\n"
            "- Бот добавлен в группу?\n"
            "- ID группы и топика верные?\n"
            "- Топики включены в группе?\n"
            "- У бота есть права на отправку сообщений?"
        )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
