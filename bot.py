import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import psycopg2
import re
from datetime import datetime

# --- НАСТРОЙКИ ---
VK_TOKEN = "vk1.a.OX5vIFs9AC5Dw4yzYNAlmlQREdzf2lxjcJtkFNko8zumVErB7cINuuOrOy6Ovc4m5S1fSmb9hUGhD_-Rn-hki2tLZnBRYQdUBXjfcGkylfs_oX88fKm4CpWZE7grqoovih4goZfwkFYi7F0cbtRIhDAuqlCLK2GqdIIfnb5ws_a2z-kPKk-BB1YpeSy8FSiQzdswTn4795mA1VR5-EALVA"
GROUP_ID = 2000000170

# --- ПОДКЛЮЧЕНИЕ К БД ---
conn = psycopg2.connect(
    host="node1.pghost.ru",
    port=15803,
    database="bothost_db_2893e90ebf4a",
    user="bothost_db_2893e90ebf4a",
    password="F05XIGyAztuZnfCJGqquSDFWDXdBAZ-mPr_ShsSfB74"
)
cursor = conn.cursor()

# --- СОЗДАНИЕ ТАБЛИЦ ---
def init_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            access_level INTEGER DEFAULT 0,
            registered_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banned_words (
            id SERIAL PRIMARY KEY,
            word VARCHAR(100) NOT NULL
        )
    """)
    
    conn.commit()

init_db()

# --- АВТОРИЗАЦИЯ ВК ---
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

# --- ФУНКЦИИ ---
def get_user_level(user_id):
    cursor.execute("SELECT access_level FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def set_user_level(user_id, level):
    cursor.execute("""
        INSERT INTO users (user_id, access_level) 
        VALUES (%s, %s) 
        ON CONFLICT (user_id) DO UPDATE SET access_level = %s
    """, (user_id, level, level))
    conn.commit()

def check_access(required_level):
    def decorator(func):
        def wrapper(event, *args, **kwargs):
            user_level = get_user_level(event.user_id)
            if user_level >= required_level:
                return func(event, *args, **kwargs)
            else:
                send_message(event.user_id, "⛔ Недостаточно прав!")
        return wrapper
    return decorator

def send_message(user_id, message):
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=get_random_id()
    )

# --- КОМАНДЫ 6 LVL ---

@check_access(6)
def cmd_sync(event):
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM banned_words")
        words_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """)
        columns = [col[0] for col in cursor.fetchall()]
        
        message = f"Синхронизация выполнена. Пользователей: {users_count}, запрещённых слов: {words_count}"
        send_message(event.user_id, message)
        
    except Exception as e:
        send_message(event.user_id, f"Ошибка: {str(e)}")

@check_access(6)
def cmd_addzkts(event, text):
    try:
        user_ids = re.findall(r'\d+', text)
        if not user_ids:
            send_message(event.user_id, "Укажите ID пользователя: /addzkts 123456789")
            return
            
        target_id = int(user_ids[0])
        current_level = get_user_level(target_id)
        
        if current_level >= 6:
            send_message(event.user_id, "Невозможно изменить права куратора")
            return
            
        set_user_level(target_id, 5)
        
        send_message(target_id, "Вам выданы права зам. куратора технических специалистов (5 LVL)")
        send_message(event.user_id, f"Права ЗКТС выданы пользователю {target_id}")
        
    except Exception as e:
        send_message(event.user_id, f"Ошибка: {str(e)}")

@check_access(6)
def cmd_pin(event, text):
    try:
        ids = re.findall(r'\d+', text)
        if len(ids) < 2:
            send_message(event.user_id, "Укажите ID беседы и сообщения: /pin 123 456")
            return
            
        peer_id = int(ids[0])
        message_id = int(ids[1])
        
        if peer_id < 2000000000:
            peer_id += 2000000000
            
        vk.messages.pin(
            peer_id=peer_id,
            message_id=message_id
        )
        
        send_message(event.user_id, "Сообщение закреплено")
        
    except Exception as e:
        send_message(event.user_id, f"Ошибка: {str(e)}")

@check_access(6)
def cmd_filter(event, text):
    try:
        parts = text.split()
        if len(parts) < 2:
            send_message(event.user_id, "/filter add слово | /filter remove слово | /filter list | /filter clear")
            return
            
        action = parts[1].lower()
        
        if action == "add" and len(parts) >= 3:
            word = ' '.join(parts[2:]).lower()
            cursor.execute("INSERT INTO banned_words (word) VALUES (%s)", (word,))
            conn.commit()
            send_message(event.user_id, f"Слово '{word}' добавлено")
            
        elif action == "remove" and len(parts) >= 3:
            word = ' '.join(parts[2:]).lower()
            cursor.execute("DELETE FROM banned_words WHERE word = %s", (word,))
            conn.commit()
            send_message(event.user_id, f"Слово '{word}' удалено")
            
        elif action == "list":
            cursor.execute("SELECT word FROM banned_words")
            words = cursor.fetchall()
            if words:
                word_list = "\n".join([f"- {w[0]}" for w in words])
                send_message(event.user_id, f"Запрещённые слова:\n{word_list}")
            else:
                send_message(event.user_id, "Список пуст")
                
        elif action == "clear":
            cursor.execute("DELETE FROM banned_words")
            conn.commit()
            send_message(event.user_id, "Список очищен")
            
    except Exception as e:
        send_message(event.user_id, f"Ошибка: {str(e)}")

def check_banned_words(text):
    cursor.execute("SELECT word FROM banned_words")
    banned_words = [word[0] for word in cursor.fetchall()]
    
    text_lower = text.lower()
    for word in banned_words:
        if word in text_lower:
            return True, word
    return False, None

# --- ОСНОВНОЙ ЦИКЛ ---
print("Бот запущен")

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        if event.from_user:
            has_banned, word = check_banned_words(event.text)
            if has_banned:
                send_message(event.user_id, "Сообщение содержит запрещённое слово")
                continue
        
        text = event.text.strip()
        
        if text == "/sync":
            cmd_sync(event)
        elif text.startswith("/addzkts"):
            cmd_addzkts(event, text)
        elif text.startswith("/pin"):
            cmd_pin(event, text)
        elif text.startswith("/filter"):
            cmd_filter(event, text)
        elif text == "/mylevel":
            send_message(event.user_id, f"Ваш уровень: {get_user_level(event.user_id)}")
        elif text == "/help":
            send_message(event.user_id, "/sync /addzkts /pin /filter /mylevel")
