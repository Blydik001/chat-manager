import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, html, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

TOKEN = "8929522753:AAG4rb7zImXg2cfzQU9azjeMpRK7KTwnunE"

dp = Dispatcher()

class IPForm(StatesGroup):
    waiting_for_ip = State()

# --- КЛАВИАТУРЫ ---

def get_main_panel() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Технический раздел", callback_data="tech_section")],
        [InlineKeyboardButton(text="Настройки", callback_data="settings_section")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_tech_panel() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Аналитика IP", callback_data="tech_ip_analytics")],
        [InlineKeyboardButton(text="Создание моно-форм", callback_data="tech_mono_forms")],
        [InlineKeyboardButton(text="Сайт 71-75 отдела", callback_data="tech_site")],
        [InlineKeyboardButton(text="VPN 71-75 отдела", callback_data="tech_vpn")],
        [InlineKeyboardButton(text="Вернуться на главную", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_ip_input")]
    ])


# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_name = message.from_user.first_name
    text = (
        f"👋🏻 Привет, {html.bold(user_name)}!\n\n"
        f"Ты попал в официальный бот технического отдела 71-75. "
        f"Для открытия панели — /panel\n\n\n"
        f"Твоя роль: Зам. куратора тех. специалистов"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("panel"))
async def command_panel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        text="Тебе нужно выбрать нужный пункт:",
        reply_markup=get_main_panel()
    )


# --- ОБРАБОТЧИКИ НАЖАТИЙ НА КНОПКИ (CALLBACK QUERIES) ---

@dp.callback_query(F.data == "tech_section")
async def process_tech_section(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        text=" **Ты выбрал технический раздел**\nВыбери интересующий пункт:",
        reply_markup=get_tech_panel(),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        text="Тебе нужно выбрать нужный пункт:",
        reply_markup=get_main_panel()
    )
    await callback.answer()


@dp.callback_query(F.data == "settings_section")
async def process_settings(callback: CallbackQuery) -> None:
    await callback.answer("⚙️ Раздел 'Настройки' находится в разработке.", show_alert=True)


@dp.callback_query(F.data == "tech_ip_analytics")
async def process_ip_analytics(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(IPForm.waiting_for_ip)
    
    await callback.message.edit_text(
        text="Пожалуйста, введи IP-адрес или несколько через пробел.",
        reply_markup=get_cancel_keyboard()
    )


@dp.callback_query(F.data == "cancel_ip_input")
async def cancel_ip_input(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        text=" **Ты выбрал технический раздел**\nВыбери интересующий пункт:",
        reply_markup=get_tech_panel(),
        parse_mode="Markdown"
    )
    await callback.answer("Ввод IP отменен")


@dp.callback_query(F.data.startswith("tech_"))
async def process_tech_buttons(callback: CallbackQuery) -> None:
    actions = {
        "tech_mono_forms": "Открытие конструктора моно-форм...",
        "tech_site": "Переход на сайт 71-75...",
        "tech_vpn": "Подключение к VPN 71-75 отдела..."
    }
    action_text = actions.get(callback.data, "Раздел в разработке.")
    await callback.answer(action_text, show_alert=True)


# --- ОБРАБОТКА ВВЕДЕННЫХ IP-АДРЕСОВ ЧЕРЕЗ API 2IP ---

@dp.message(IPForm.waiting_for_ip)
async def analyze_ip_message(message: Message, state: FSMContext) -> None:
    ip_list = [ip.strip() for ip in message.text.split() if ip.strip()]
    
    if not ip_list:
        await message.answer("❌ Вы не ввели ни одного IP-адреса. Попробуйте еще раз.")
        return

    status_message = await message.answer("🔄 Запрос к базе данных 2ip.io, проверка IP...")
    final_report = " Информация о IP-адресах:\n\n"
    
    async with aiohttp.ClientSession() as session:
        for idx, ip_address in enumerate(ip_list, start=1):
            
            # Используем открытый эндпоинт API от 2ip для получения полной информации
            api_url = f"https://2ip.ua{ip_address}"
            
            try:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Если API ничего не вернуло или вернуло ошибку
                        if not data or data.get("country") is None:
                            final_report += f"**IP {idx}**: `{ip_address}`\n❌ Ошибка: Неверный формат или нет данных в базе 2ip\n\n"
                            continue
                        
                        # Парсим данные ответа от 2ip
                        country = data.get("country", "Не определено")
                        region = data.get("region", "Не определено")
                        city = data.get("city", "Не определено")
                        isp = data.get("isp", "Не определено")
                        
                        # Дополнительная техническая информация (ASN, маска)
                        asn = data.get("asn", "Не определено")
                        cidr = data.get("cidr", "Не определено")
                        as_info = f"ASN: {asn} | Подсеть: {cidr}"
                        
                        # Проверка на использование VPN/Прокси/Хостинга
                        # В структуре 2ip флаг "hosting" или "proxy" указывает на то то, что это сервер/прокси
                        is_hosting = data.get("hosting", False) or data.get("proxy", False)
                        
                        vpn_status = "VPN используется" if is_hosting else "VPN не обнаружен / Чистый residential"
                        internet_type = "Дата-центр / Хостинг / Прокси" if is_hosting else "Мобильный / Домашний интернет"
                        
                        # Формируем отчет строго по вашему шаблону
                        final_report += (
                            f"**IP {idx}**: `{ip_address}`\n"
                            f"**Страна**: {country}\n"
                            f"**Регион**: {region}\n"
                            f"**Город**: {city}\n"
                            f"**VPN**: {vpn_status}\n\n"
                            f"Дополнительно:\n"
                            f"**Провайдер**: {isp}\n"
                            f"**Доп. инфа**: {as_info}\n"
                            f"**Интернет**: {internet_type}\n"
                            f"**VPN используется**: {'Да' if is_hosting else 'Нет'}\n\n"
                            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
                        )
                    else:
                        final_report += f"**IP {idx}**: `{ip_address}`\n❌ Ошибка сервера 2ip.io\n\n"
            except Exception as e:
                logging.error(f"Error checking IP {ip_address} via 2ip: {e}")
                final_report += f"**IP {idx}**: `{ip_address}`\n❌ Внутренняя ошибка сети\n\n"

    await status_message.edit_text(final_report, parse_mode="Markdown")
    await state.clear()


# --- ЗАПУСК БОТА ---

async def main() -> None:
    bot = Bot(token=TOKEN)
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
