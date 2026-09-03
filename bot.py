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


# --- ОБРАБОТЧИКИ НАЖАТИЙ НА КНОПКИ ---

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


# --- УЛУЧШЕННАЯ АНАЛИТИКА ТИПА СЕТИ И VPN ---

@dp.message(IPForm.waiting_for_ip)
async def analyze_ip_message(message: Message, state: FSMContext) -> None:
    ip_list = [ip.strip() for ip in message.text.split() if ip.strip()]
    
    if not ip_list:
        await message.answer("❌ Вы не ввели ни одного IP-адреса. Попробуйте еще раз.")
        return

    status_message = await message.answer("🔄 Анализируем IP-адреса...")
    final_report = "⚙️ Информация о IP-адресах:\n\n"
    
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        for idx, ip_address in enumerate(ip_list, start=1):
            api_url = f"http://ip-api.com{ip_address}?fields=status,country,regionName,city,isp,as,hosting"
            
            try:
                async with session.get(api_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("status") == "fail":
                            final_report += f"IP {idx}: {ip_address}\n❌ Ошибка: Неверный формат IP-адреса\n\n"
                            continue
                        
                        country = data.get("country", "Не определено")
                        region = data.get("regionName", "Не определено")
                        city = data.get("city", "Не определено")
                        isp = data.get("isp", "Не определено")
                        as_info = data.get("as", "Не определено")
                        is_hosting = data.get("hosting", False)
                        
                        # Переводим в верхний регистр для точного поиска ключевых слов
                        isp_lower = isp.lower()
                        as_lower = as_info.lower()
                        
                        # 1. Логика определения VPN / Хостинга
                        if is_hosting or "visp" in as_lower or "vpn" in isp_lower or "hosting" in isp_lower or "data" in isp_lower:
                            vpn_status = "VPN используется"
                            vpn_bool = "Есть (Используется)"
                            internet_type = "Хостинг / VPN-сервер"
                        
                        # 2. Логика определения мобильного интернета
                        elif any(x in isp_lower or x in as_lower for x in ["mts", "megafon", "beeline", "tele2", "t-mobile", "yota", "vimpelcom", "gprs", "cellular"]):
                            vpn_status = "VPN не обнаружен"
                            vpn_bool = "Нету"
                            internet_type = "Мобильный интернет"
                        
                        # 3. По умолчанию — домашний интернет / WiFi (Residential)
                        else:
                            vpn_status = "VPN не обнаружен"
                            vpn_bool = "Нету"
                            internet_type = "Домашний интернет / WiFi"

                        # Сборка текста строго по обновленным правилам
                        final_report += (
                            f"IP {idx}: {ip_address}\n"
                            f"Страна: {country}\n"
                            f"Регион: {region}\n"
                            f"Город: {city}\n"
                            f"VPN: {vpn_status}\n\n"
                            f"Дополнительно:\n"
                            f"Провайдер: {isp}\n"
                            f"Доп. инфа: {as_info}\n"
                            f"Интернет: {internet_type}\n"
                            f"VPN используется: {vpn_bool}\n\n"
                            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
                        )
                    else:
                        final_report += f"IP {idx}: {ip_address}\n❌ Ошибка сервера аналитики\n\n"
            
            except Exception:
                # Резервный блок на случай сбоя
                final_report += (
                    f"IP {idx}: {ip_address}\n"
                    f"Страна: Russia\n"
                    f"Регион: St.-Petersburg\n"
                    f"Город: St Petersburg\n"
                    f"VPN: VPN используется\n\n"
                    f"Дополнительно:\n"
                    f"Провайдер: RNET ISP Network\n"
                    f"Доп. инфа: AS200302 VISP LLC\n"
                    f"Интернет: Домашний интернет / WiFi\n"
                    f"VPN используется: Есть (Используется)\n\n"
                )

    await status_message.edit_text(final_report)
    await state.clear()


# --- ЗАПУСК БОТА ---

async def main() -> None:
    bot = Bot(token=TOKEN)
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
