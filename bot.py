import asyncio
import sqlite3
import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "8975105830:AAHSsz6kETM1gD-x2JnOlfVTeLOWMRp_8I4"  # ЗАМЕНИТЕ НА СВОЙ ТОКЕН!

# ID владельцев (кто имеет права администратора по умолчанию)
OWNER_IDS = [8881305868]  # ЗАМЕНИТЕ НА СВОЙ ID!

# ФИКСИРОВАННЫЕ БЕСЕДЫ (группы чатов)
# Формат: ID_ГРУППЫ: [список ID чатов]
FIXED_CHAT_GROUPS = {
    1: [-1003739741915, -1003641912264],  # Группа 1: два чата
}

# Все разрешённые чаты (автоматически собираются из FIXED_CHAT_GROUPS)
ALLOWED_CHATS = []
for chats in FIXED_CHAT_GROUPS.values():
    ALLOWED_CHATS.extend(chats)

BOT_NAME = "BR | Chat Manager"

def get_group_by_chat(chat_id: int):
    """Возвращает ID группы для чата"""
    for group_id, chats in FIXED_CHAT_GROUPS.items():
        if chat_id in chats:
            return group_id
    return None

def get_chats_by_group(group_id: int):
    """Возвращает список чатов в группе"""
    return FIXED_CHAT_GROUPS.get(group_id, [])

# ==================== БАЗА ДАННЫХ ====================
DB_PATH = "chat_manager.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER,
            chat_id INTEGER,
            role TEXT CHECK(role IN ('moderator', 'senior_moderator', 'administrator')),
            PRIMARY KEY (user_id, chat_id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS global_bans (
            user_id INTEGER,
            group_id INTEGER,
            reason TEXT,
            banned_by INTEGER,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, group_id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS nicknames (
            user_id INTEGER,
            chat_id INTEGER,
            nickname TEXT,
            PRIMARY KEY (user_id, chat_id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS welcome_settings (
            chat_id INTEGER PRIMARY KEY,
            welcome_text TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS banned_words (
            chat_id INTEGER,
            word TEXT,
            PRIMARY KEY (chat_id, word)
        )
    ''')
    
    conn.commit()
    conn.close()

# === РОЛИ ===
def set_role(user_id: int, chat_id: int, role: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO user_roles (user_id, chat_id, role) VALUES (?, ?, ?)', 
              (user_id, chat_id, role))
    conn.commit()
    conn.close()

def get_role(user_id: int, chat_id: int) -> Optional[str]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT role FROM user_roles WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def remove_role(user_id: int, chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM user_roles WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    conn.commit()
    conn.close()

def get_all_roles(chat_id: int) -> List[Tuple[int, str]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id, role FROM user_roles WHERE chat_id = ?', (chat_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# === ГЛОБАЛЬНЫЕ БАНЫ ===
def add_global_ban(user_id: int, group_id: int, reason: str, banned_by: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO global_bans (user_id, group_id, reason, banned_by) VALUES (?, ?, ?, ?)', 
              (user_id, group_id, reason, banned_by))
    conn.commit()
    conn.close()

def remove_global_ban(user_id: int, group_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM global_bans WHERE user_id = ? AND group_id = ?', (user_id, group_id))
    conn.commit()
    conn.close()

def is_globally_banned(user_id: int, group_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM global_bans WHERE user_id = ? AND group_id = ?', (user_id, group_id))
    row = c.fetchone()
    conn.close()
    return row is not None

def get_global_bans(group_id: int) -> List[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id, reason, banned_by, banned_at FROM global_bans WHERE group_id = ?', (group_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# === НИКИ ===
def set_nickname(user_id: int, chat_id: int, nickname: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO nicknames (user_id, chat_id, nickname) VALUES (?, ?, ?)', 
              (user_id, chat_id, nickname))
    conn.commit()
    conn.close()

def get_nickname(user_id: int, chat_id: int) -> Optional[str]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT nickname FROM nicknames WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def remove_nickname(user_id: int, chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM nicknames WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    conn.commit()
    conn.close()

def get_all_nicknames(chat_id: int) -> List[Tuple[int, str]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id, nickname FROM nicknames WHERE chat_id = ?', (chat_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# === ПРИВЕТСТВИЯ ===
def set_welcome(chat_id: int, text: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO welcome_settings (chat_id, welcome_text) VALUES (?, ?)', 
              (chat_id, text))
    conn.commit()
    conn.close()

def get_welcome(chat_id: int) -> Optional[str]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT welcome_text FROM welcome_settings WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def reset_welcome(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM welcome_settings WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()

# === ФИЛЬТР СЛОВ ===
def add_banned_word(chat_id: int, word: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO banned_words (chat_id, word) VALUES (?, ?)', (chat_id, word.lower()))
    conn.commit()
    conn.close()

def remove_banned_word(chat_id: int, word: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM banned_words WHERE chat_id = ? AND word = ?', (chat_id, word.lower()))
    conn.commit()
    conn.close()

def get_banned_words(chat_id: int) -> List[str]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT word FROM banned_words WHERE chat_id = ?', (chat_id,))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

# ==================== УПРАВЛЕНИЕ ГРУППАМИ ====================
async def kick_from_group(bot, user_id: int, chat_id: int):
    """Кик пользователя из всех бесед его группы"""
    group_id = get_group_by_chat(chat_id)
    if not group_id:
        return False
    
    chats = get_chats_by_group(group_id)
    success = False
    for cid in chats:
        try:
            await bot.ban_chat_member(cid, user_id)
            await bot.unban_chat_member(cid, user_id)
            success = True
        except Exception:
            pass
    return success

async def global_ban_in_group(bot, user_id: int, chat_id: int, reason: str, banned_by: int):
    """Глобальный бан пользователя во всей группе бесед"""
    group_id = get_group_by_chat(chat_id)
    if not group_id:
        return False
    
    add_global_ban(user_id, group_id, reason, banned_by)
    
    chats = get_chats_by_group(group_id)
    for cid in chats:
        try:
            await bot.ban_chat_member(cid, user_id)
        except Exception:
            pass
    return True

async def global_unban_in_group(bot, user_id: int, chat_id: int):
    """Снятие глобального бана"""
    group_id = get_group_by_chat(chat_id)
    if not group_id:
        return False
    
    remove_global_ban(user_id, group_id)
    
    chats = get_chats_by_group(group_id)
    for cid in chats:
        try:
            await bot.unban_chat_member(cid, user_id)
        except Exception:
            pass
    return True

async def send_news_to_group(bot, chat_id: int, news_text: str):
    """Отправка рассылки во все беседы группы"""
    group_id = get_group_by_chat(chat_id)
    if not group_id:
        return 0
    
    chats = get_chats_by_group(group_id)
    success_count = 0
    for cid in chats:
        try:
            await bot.send_message(cid, f"📢 <b>Рассылка:</b>\n{news_text}")
            success_count += 1
        except Exception:
            pass
    return success_count

# ==================== АДМИН РОЛИ ====================
ROLE_HIERARCHY = {
    "moderator": 1,
    "senior_moderator": 2,
    "administrator": 3
}

def get_user_role_level(user_id: int, chat_id: int) -> int:
    if user_id in OWNER_IDS:
        return 3
    role = get_role(user_id, chat_id)
    return ROLE_HIERARCHY.get(role, 0)

def is_admin(user_id: int, chat_id: int) -> bool:
    return get_user_role_level(user_id, chat_id) >= 3

def is_senior_moderator(user_id: int, chat_id: int) -> bool:
    return get_user_role_level(user_id, chat_id) >= 2

def is_moderator(user_id: int, chat_id: int) -> bool:
    return get_user_role_level(user_id, chat_id) >= 1

def check_global_ban(user_id: int, chat_id: int) -> bool:
    group_id = get_group_by_chat(chat_id)
    if group_id:
        return is_globally_banned(user_id, group_id)
    return False

# ==================== БОТ ====================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Временные муты
temp_mutes = {}

# Инициализация БД
init_db()

# === ФИЛЬТР РАЗРЕШЁННЫХ ЧАТОВ ===
# Разрешаем ЛИЧНЫЕ СООБЩЕНИЯ (chat.type == "private") и указанные группы
@dp.message(F.chat.type == "private")
async def private_chat_handler(message: Message):
    # В ЛС бот работает для всех
    pass  # Пропускаем дальше к обработчикам команд

@dp.message(F.chat.id.not_in(ALLOWED_CHATS))
async def chat_not_allowed(message: Message):
    # Этот обработчик сработает только для групп, которых нет в списке
    if message.chat.type != "private":
        await message.reply("❌ Этот чат не входит в список разрешённых бесед бота.")
        try:
            await message.leave()
        except:
            pass

# === ХЕЛПЕРЫ ===
async def check_permission(message: Message, required_level: int) -> bool:
    user_level = get_user_role_level(message.from_user.id, message.chat.id)
    if user_level >= required_level:
        return True
    await message.reply("❌ У вас недостаточно прав для этой команды.")
    return False

async def check_global_ban_for_user(message: Message) -> bool:
    if check_global_ban(message.from_user.id, message.chat.id):
        await message.reply("❌ Вы находитесь в глобальном бане этой группы бесед.")
        try:
            await bot.ban_chat_member(message.chat.id, message.from_user.id)
        except:
            pass
        return True
    return False

async def get_user_from_mention(chat_id: int, username: str):
    if username.startswith('@'):
        username = username[1:]
    try:
        member = await bot.get_chat_member(chat_id, f"@{username}")
        return member.user
    except:
        return None

# === ОБРАБОТЧИК НОВЫХ УЧАСТНИКОВ ===
@dp.chat_member()
async def on_user_join(update: ChatMemberUpdated):
    if update.new_chat_member.status == "member":
        welcome_text = get_welcome(update.chat.id)
        if welcome_text:
            user = update.new_chat_member.user
            user_mention = user.mention_html()
            text = welcome_text.replace("{mention}", user_mention).replace("{name}", user.full_name)
            await bot.send_message(update.chat.id, text, parse_mode=ParseMode.HTML)

# === ФИЛЬТР ПЛОХИХ СЛОВ (только в группах) ===
@dp.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def filter_bad_words(message: Message):
    if await check_global_ban_for_user(message):
        return
    
    banned_words = get_banned_words(message.chat.id)
    if banned_words:
        text_lower = message.text.lower()
        for word in banned_words:
            if word in text_lower:
                await message.delete()
                await message.reply(f"🚫 Обнаружено запрещённое слово: {word}")
                break

# === ПОЛЬЗОВАТЕЛЬСКИЕ КОМАНДЫ ===
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(f"🤖 {BOT_NAME} приветствует вас!\nИспользуйте /help для списка команд.")

@dp.message(Command("id"))
async def cmd_id(message: Message, command: CommandObject):
    if command.args:
        username = command.args.strip()
        user = await get_user_from_mention(message.chat.id, username)
        if not user:
            await message.reply("❌ Пользователь не найден.")
            return
        target = user
    else:
        target = message.from_user if not message.reply_to_message else message.reply_to_message.from_user
    await message.reply(f"🆔 ID пользователя <b>{target.full_name}</b>: <code>{target.id}</code>")

@dp.message(Command("staff"))
async def cmd_staff(message: Message):
    # В ЛС эта команда не работает
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /staff работает только в группах.")
        return
    
    text = "👥 <b>Сотрудники чата:</b>\n\n"
    admins = []
    senior_mods = []
    mods = []
    
    for owner_id in OWNER_IDS:
        try:
            member = await bot.get_chat_member(message.chat.id, owner_id)
            admins.append(member.user)
        except:
            pass
    
    roles = get_all_roles(message.chat.id)
    for user_id, role in roles:
        if user_id in OWNER_IDS:
            continue
        try:
            member = await bot.get_chat_member(message.chat.id, user_id)
            if role == "administrator":
                admins.append(member.user)
            elif role == "senior_moderator":
                senior_mods.append(member.user)
            elif role == "moderator":
                mods.append(member.user)
        except:
            pass
    
    if admins:
        text += "👑 <b>Администраторы:</b>\n" + "\n".join(f"• {u.full_name}" for u in admins) + "\n\n"
    if senior_mods:
        text += "🛡 <b>Старшие модераторы:</b>\n" + "\n".join(f"• {u.full_name}" for u in senior_mods) + "\n\n"
    if mods:
        text += "👮 <b>Модераторы:</b>\n" + "\n".join(f"• {u.full_name}" for u in mods)
    
    await message.reply(text)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = f"""
🤖 <b>{BOT_NAME}</b> — ваш помощник для управления чатами!

📜 <b>Команды пользователя:</b>
/id [@username] — Telegram ID
/staff — Список ролей
/help — Список команд

👮 <b>Модератор:</b>
/clear — Удалить сообщение
/gbynick [ник] — Найти по нику
/gnick @username — Показать ник
/kick @username — Кик
/mute @username [время] — Замутить
/unmute @username — Размутить
/snick @username [ник] — Установить ник
/rnick @username — Удалить ник
/ban @username — Заблокировать
/unban @username — Разбанить
/nlist — Список ников
/pin — Закрепить
/unpin — Открепить
/gkick @username — Глобальный кик (по всей группе бесед)

🛡 <b>Старший модератор:</b>
/gban @username [причина] — Глобальный бан
/gunban @username — Снять глобальный бан
/setrole — Выдать роль
/removerole — Убрать роль
/setwelcome — Настроить приветствие
/getwelcome — Показать приветствие
/resetwelcome — Сбросить приветствие

👑 <b>Администратор:</b>
/words — Фильтр слов
/news [текст] — Рассылка по группе бесед
"""
    await message.reply(help_text)

# === МОДЕРАТОР ===
@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /clear работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    if message.reply_to_message:
        await message.reply_to_message.delete()
        await message.delete()
    else:
        await message.reply("ℹ️ Ответьте на сообщение, чтобы удалить его.")

@dp.message(Command("gbynick"))
async def cmd_gbynick(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /gbynick работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    if not command.args:
        await message.reply("❌ Укажите ник для поиска.")
        return
    nickname = command.args.strip()
    found = []
    for user_id, nick in get_all_nicknames(message.chat.id):
        if nickname.lower() in nick.lower():
            found.append((user_id, nick))
    if found:
        text = "🔍 <b>Найдено:</b>\n" + "\n".join(f"• {nick} → <code>{uid}</code>" for uid, nick in found)
    else:
        text = "❌ Ник не найден."
    await message.reply(text)

@dp.message(Command("gnick"))
async def cmd_gnick(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /gnick работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif command.args:
        username = command.args.strip()
        target = await get_user_from_mention(message.chat.id, username)
    if not target:
        await message.reply("❌ Укажите пользователя (ответом или @username).")
        return
    nick = get_nickname(target.id, message.chat.id)
    if nick:
        await message.reply(f"📝 Ник {target.full_name}: {nick}")
    else:
        await message.reply(f"❌ У {target.full_name} нет установленного ника.")

@dp.message(Command("kick"))
async def cmd_kick(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /kick работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif command.args:
        username = command.args.strip()
        target = await get_user_from_mention(message.chat.id, username)
    if not target:
        await message.reply("❌ Укажите пользователя.")
        return
    if target.id == message.from_user.id:
        await message.reply("❌ Нельзя кикнуть самого себя.")
        return
    target_level = get_user_role_level(target.id, message.chat.id)
    if target_level >= get_user_role_level(message.from_user.id, message.chat.id):
        await message.reply("❌ Вы не можете кикнуть пользователя с равным или высшим уровнем.")
        return
    try:
        await bot.ban_chat_member(message.chat.id, target.id)
        await bot.unban_chat_member(message.chat.id, target.id)
        await message.reply(f"✅ {target.full_name} кикнут.")
    except:
        await message.reply("❌ Не удалось кикнуть пользователя.")

@dp.message(Command("mute"))
async def cmd_mute(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /mute работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    args = command.args.split() if command.args else []
    if len(args) < 1:
        await message.reply("❌ Использование: /mute @username [время] (1m, 1h, 1d)")
        return
    username = args[0]
    target = await get_user_from_mention(message.chat.id, username)
    if not target:
        await message.reply("❌ Пользователь не найден.")
        return
    
    duration = args[1] if len(args) > 1 else "10m"
    time_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    match = re.match(r'(\d+)([smhd])', duration)
    if not match:
        await message.reply("❌ Неверный формат времени. Пример: 30m, 2h, 1d")
        return
    value, unit = int(match[1]), match[2]
    seconds = value * time_map[unit]
    
    until_date = datetime.now() + timedelta(seconds=seconds)
    try:
        await bot.restrict_chat_member(message.chat.id, target.id, until_date=until_date, can_send_messages=False)
        temp_mutes[(message.chat.id, target.id)] = until_date
        await message.reply(f"🔇 {target.full_name} замучен на {duration}.")
    except:
        await message.reply("❌ Не удалось замутить пользователя.")

@dp.message(Command("unmute"))
async def cmd_unmute(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /unmute работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif command.args:
        username = command.args.strip()
        target = await get_user_from_mention(message.chat.id, username)
    if not target:
        await message.reply("❌ Укажите пользователя.")
        return
    try:
        await bot.restrict_chat_member(message.chat.id, target.id, can_send_messages=True)
        temp_mutes.pop((message.chat.id, target.id), None)
        await message.reply(f"✅ {target.full_name} размучен.")
    except:
        await message.reply("❌ Не удалось размутить.")

@dp.message(Command("snick"))
async def cmd_snick(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /snick работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    args = command.args.split(maxsplit=1) if command.args else []
    if len(args) < 2:
        await message.reply("❌ Использование: /snick @username [ник]")
        return
    username = args[0]
    nickname = args[1]
    target = await get_user_from_mention(message.chat.id, username)
    if not target:
        await message.reply("❌ Пользователь не найден.")
        return
    set_nickname(target.id, message.chat.id, nickname)
    await message.reply(f"✅ Установлен ник для {target.full_name}: {nickname}")

@dp.message(Command("rnick"))
async def cmd_rnick(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /rnick работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif command.args:
        username = command.args.strip()
        target = await get_user_from_mention(message.chat.id, username)
    if not target:
        await message.reply("❌ Укажите пользователя.")
        return
    remove_nickname(target.id, message.chat.id)
    await message.reply(f"✅ Ник {target.full_name} удалён.")

@dp.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /ban работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif command.args:
        username = command.args.strip()
        target = await get_user_from_mention(message.chat.id, username)
    if not target:
        await message.reply("❌ Укажите пользователя.")
        return
    target_level = get_user_role_level(target.id, message.chat.id)
    if target_level >= get_user_role_level(message.from_user.id, message.chat.id):
        await message.reply("❌ Вы не можете забанить пользователя с равным или высшим уровнем.")
        return
    try:
        await bot.ban_chat_member(message.chat.id, target.id)
        await message.reply(f"✅ {target.full_name} забанен.")
    except:
        await message.reply("❌ Не удалось забанить.")

@dp.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /unban работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    if not command.args:
        await message.reply("❌ Укажите username или ID.")
        return
    target_input = command.args.strip()
    try:
        if target_input.startswith('@'):
            user = await get_user_from_mention(message.chat.id, target_input)
            target_id = user.id if user else None
        else:
            target_id = int(target_input)
        if not target_id:
            await message.reply("❌ Пользователь не найден.")
            return
        await bot.unban_chat_member(message.chat.id, target_id)
        await message.reply(f"✅ Пользователь разбанен.")
    except:
        await message.reply("❌ Не удалось разбанить.")

@dp.message(Command("nlist"))
async def cmd_nlist(message: Message):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /nlist работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    nicks = get_all_nicknames(message.chat.id)
    if not nicks:
        await message.reply("📝 Список ников пуст.")
        return
    text = "📝 <b>Список ников:</b>\n" + "\n".join(f"• <code>{uid}</code> → {nick}" for uid, nick in nicks)
    await message.reply(text)

@dp.message(Command("pin"))
async def cmd_pin(message: Message):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /pin работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    if message.reply_to_message:
        await message.reply_to_message.pin()
        await message.reply("📌 Сообщение закреплено.")
    else:
        await message.reply("ℹ️ Ответьте на сообщение, чтобы закрепить.")

@dp.message(Command("unpin"))
async def cmd_unpin(message: Message):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /unpin работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    if message.reply_to_message:
        await message.reply_to_message.unpin()
        await message.reply("📍 Сообщение откреплено.")
    else:
        await message.reply("ℹ️ Ответьте на сообщение, чтобы открепить.")

@dp.message(Command("gkick"))
async def cmd_gkick(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /gkick работает только в группах.")
        return
    if not await check_permission(message, 1):
        return
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif command.args:
        username = command.args.strip()
        target = await get_user_from_mention(message.chat.id, username)
    if not target:
        await message.reply("❌ Укажите пользователя.")
        return
    success = await kick_from_group(bot, target.id, message.chat.id)
    if success:
        await message.reply(f"✅ {target.full_name} кикнут из всех бесед группы.")
    else:
        await message.reply("❌ Эта беседа не входит в группу.")

# === СТАРШИЙ МОДЕРАТОР ===
@dp.message(Command("gban"))
async def cmd_gban(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /gban работает только в группах.")
        return
    if not await check_permission(message, 2):
        return
    args = command.args.split(maxsplit=1) if command.args else []
    if len(args) < 1:
        await message.reply("❌ Использование: /gban @username [причина]")
        return
    username = args[0]
    reason = args[1] if len(args) > 1 else "Без причины"
    target = await get_user_from_mention(message.chat.id, username)
    if not target:
        await message.reply("❌ Пользователь не найден.")
        return
    success = await global_ban_in_group(bot, target.id, message.chat.id, reason, message.from_user.id)
    if success:
        await message.reply(f"🌍 {target.full_name} глобально забанен в группе бесед.\nПричина: {reason}")
    else:
        await message.reply("❌ Эта беседа не входит в группу.")

@dp.message(Command("gunban"))
async def cmd_gunban(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /gunban работает только в группах.")
        return
    if not await check_permission(message, 2):
        return
    if not command.args:
        await message.reply("❌ Укажите username или ID.")
        return
    target_input = command.args.strip()
    try:
        if target_input.startswith('@'):
            user = await get_user_from_mention(message.chat.id, target_input)
            target_id = user.id if user else None
        else:
            target_id = int(target_input)
        if not target_id:
            await message.reply("❌ Пользователь не найден.")
            return
        success = await global_unban_in_group(bot, target_id, message.chat.id)
        if success:
            await message.reply(f"✅ Глобальный бан снят.")
        else:
            await message.reply("❌ Эта беседа не входит в группу.")
    except:
        await message.reply("❌ Не удалось снять глобальный бан.")

@dp.message(Command("setrole"))
async def cmd_setrole(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /setrole работает только в группах.")
        return
    if not await check_permission(message, 2):
        return
    args = command.args.split() if command.args else []
    if len(args) < 2:
        await message.reply("❌ Использование: /setrole @username [moderator|senior_moderator|administrator]")
        return
    username = args[0]
    role = args[1]
    if role not in ['moderator', 'senior_moderator', 'administrator']:
        await message.reply("❌ Роль должна быть: moderator, senior_moderator, administrator")
        return
    target = await get_user_from_mention(message.chat.id, username)
    if not target:
        await message.reply("❌ Пользователь не найден.")
        return
    set_role(target.id, message.chat.id, role)
    await message.reply(f"✅ {target.full_name} назначен {role}.")

@dp.message(Command("removerole"))
async def cmd_removerole(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /removerole работает только в группах.")
        return
    if not await check_permission(message, 2):
        return
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif command.args:
        username = command.args.strip()
        target = await get_user_from_mention(message.chat.id, username)
    if not target:
        await message.reply("❌ Укажите пользователя.")
        return
    remove_role(target.id, message.chat.id)
    await message.reply(f"✅ Роль {target.full_name} удалена.")

@dp.message(Command("setwelcome"))
async def cmd_setwelcome(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /setwelcome работает только в группах.")
        return
    if not await check_permission(message, 2):
        return
    if not command.args:
        await message.reply("❌ Использование: /setwelcome текст\nПеременные: {{mention}}, {{name}}")
        return
    set_welcome(message.chat.id, command.args)
    await message.reply("✅ Приветствие установлено.")

@dp.message(Command("getwelcome"))
async def cmd_getwelcome(message: Message):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /getwelcome работает только в группах.")
        return
    if not await check_permission(message, 2):
        return
    text = get_welcome(message.chat.id)
    if text:
        await message.reply(f"📋 Текущее приветствие:\n{text}")
    else:
        await message.reply("ℹ️ Приветствие не установлено.")

@dp.message(Command("resetwelcome"))
async def cmd_resetwelcome(message: Message):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /resetwelcome работает только в группах.")
        return
    if not await check_permission(message, 2):
        return
    reset_welcome(message.chat.id)
    await message.reply("✅ Приветствие сброшено.")

# === АДМИНИСТРАТОР ===
@dp.message(Command("words"))
async def cmd_words(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /words работает только в группах.")
        return
    if not await check_permission(message, 3):
        return
    args = command.args.split() if command.args else []
    if len(args) == 0:
        words = get_banned_words(message.chat.id)
        if words:
            await message.reply("🚫 <b>Запрещённые слова:</b>\n" + "\n".join(f"• {w}" for w in words))
        else:
            await message.reply("ℹ️ Список запрещённых слов пуст.")
        return
    
    action = args[0].lower()
    if action == "add" and len(args) > 1:
        add_banned_word(message.chat.id, args[1])
        await message.reply(f"✅ Слово '{args[1]}' добавлено в фильтр.")
    elif action == "remove" and len(args) > 1:
        remove_banned_word(message.chat.id, args[1])
        await message.reply(f"✅ Слово '{args[1]}' удалено из фильтра.")
    elif action == "list":
        words = get_banned_words(message.chat.id)
        if words:
            await message.reply("🚫 <b>Запрещённые слова:</b>\n" + "\n".join(f"• {w}" for w in words))
        else:
            await message.reply("ℹ️ Список запрещённых слов пуст.")
    else:
        await message.reply("❌ Использование: /words [add|remove|list] [слово]")

@dp.message(Command("news"))
async def cmd_news(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("ℹ️ Команда /news работает только в группах.")
        return
    if not await check_permission(message, 3):
        return
    if not command.args:
        await message.reply("❌ Введите текст рассылки.")
        return
    news_text = command.args
    count = await send_news_to_group(bot, message.chat.id, news_text)
    if count > 0:
        await message.reply(f"✅ Рассылка отправлена в {count} бесед группы.")
    else:
        await message.reply("❌ Эта беседа не входит в группу или нет других бесед.")

# === ЗАПУСК ===
async def main():
    print(f"🤖 {BOT_NAME} запущен!")
    print(f"✅ Разрешённые беседы: {ALLOWED_CHATS}")
    print(f"📊 Группы бесед: {list(FIXED_CHAT_GROUPS.keys())}")
    
    # Проверка подключения к Telegram
    try:
        me = await bot.get_me()
        print(f"✅ Бот подключен: @{me.username} (ID: {me.id})")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("❌ Проверьте токен бота в config.py!")
        return
    
    print("🔄 Запускаем polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
