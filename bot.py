import asyncio
import logging
from aiogram import Bot, Dispatcher, html, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Токен вашего бота уже установлен
TOKEN = "8929522753:AAG4rb7zImXg2cfzQU9azjeMpRK7KTwnunE"

dp = Dispatcher()

# --- КЛАВИАТУРЫ ---

# Главное меню панели
def get_main_panel() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🛠 Технический раздел", callback_with_text="tech_section")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings_section")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Меню технического раздела
def get_tech_panel() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📊 Аналитика IP", callback_data="tech_ip_analytics")],
        [InlineKeyboardButton(text="📄 Создание моно-форм", callback_data="tech_mono_forms")],
        [InlineKeyboardButton(text="🌐 Сайт 71-75", callback_data="tech_site")],
        [InlineKeyboardButton(text="🔒 VPN 71-75 отдела", callback_data="tech_vpn")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_name = message.from_user.first_name
    text = (
        f"👋🏻 Привет, {html.bold(user_name)}!\n\n"
        f"Ты попал в официальный бот технического отдела 71-75. "
        f"Для получения более подробной информации введи /help.\n"
        f"Для открытия панели — /panel\n\n\n"
        f"Твоя роль: Зам. куратора тех. специалистов"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("panel"))
async def command_panel_handler(message: Message) -> None:
    await message.answer(
        text="💼 Вам нужно выбрать нужный пункт:",
        reply_markup=get_main_panel()
    )


# --- ОБРАБОТЧИКИ НАЖАТИЙ НА КНОПКИ (CALLBACK QUERIES) ---

# Переход в Технический раздел
@dp.callback_query(F.data == "tech_section")
async def process_tech_section(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        text="🛠 **Технический раздел**\nВыберите интересующий подраздел:",
        reply_markup=get_tech_panel(),
        parse_mode="Markdown"
    )
    await callback.answer()


# Возврат в главное меню панели из технического раздела
@dp.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        text="💼 Вам нужно выбрать нужный пункт:",
        reply_markup=get_main_panel()
    )
    await callback.answer()


# Заглушка для Настроек
@dp.callback_query(F.data == "settings_section")
async def process_settings(callback: CallbackQuery) -> None:
    await callback.answer("⚙️ Раздел 'Настройки' находится в разработке.", show_alert=True)


# Заглушки для внутренних кнопок Технического раздела
@dp.callback_query(F.data.startswith("tech_"))
async def process_tech_buttons(callback: CallbackQuery) -> None:
    # Определяем, какая именно кнопка была нажата, чтобы показать точечный ответ
    actions = {
        "tech_ip_analytics": "Запуск Аналитики IP...",
        "tech_mono_forms": "Открытие конструктора моно-форм...",
        "tech_site": "Переход на сайт 71-75...",
        "tech_vpn": "Подключение к VPN 71-75 отдела..."
    }
    action_text = actions.get(callback.data, "Раздел в разработке.")
    
    await callback.answer(action_text, show_alert=True)


# --- ЗАПУСК БОТА ---

async def main() -> None:
    bot = Bot(token=TOKEN)
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
