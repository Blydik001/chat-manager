import sqlite3
from typing import List, Optional, Tuple

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
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            banned_by INTEGER,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    # Таблица для связывания бесед (чатов) в одну группу
    c.execute('''
        CREATE TABLE IF NOT EXISTS linked_chats (
            group_id INTEGER,
            chat_id INTEGER,
            PRIMARY KEY (group_id, chat_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Роли (без изменений)
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

# Глобальные баны (внутри связанных бесед)
def add_global_ban(user_id: int, reason: str, banned_by: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO global_bans (user_id, reason, banned_by) VALUES (?, ?, ?)', 
              (user_id, reason, banned_by))
    conn.commit()
    conn.close()

def remove_global_ban(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM global_bans WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def is_globally_banned(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM global_bans WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row is not None

def get_global_bans() -> List[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id, reason, banned_by, banned_at FROM global_bans')
    rows = c.fetchall()
    conn.close()
    return rows

# Ники
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

# Приветствия
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

# Фильтр слов
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

# Связывание бесед (вместо кластеров)
def create_chat_group(group_id: int):
    """Создаёт новую группу бесед (очищает)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM linked_chats WHERE group_id = ?', (group_id,))
    conn.commit()
    conn.close()

def add_chat_to_group(group_id: int, chat_id: int):
    """Добавляет беседу в группу"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO linked_chats (group_id, chat_id) VALUES (?, ?)', (group_id, chat_id))
    conn.commit()
    conn.close()

def remove_chat_from_group(group_id: int, chat_id: int):
    """Удаляет беседу из группы"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM linked_chats WHERE group_id = ? AND chat_id = ?', (group_id, chat_id))
    conn.commit()
    conn.close()

def get_group_chats(group_id: int) -> List[int]:
    """Получает все беседы в группе"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT chat_id FROM linked_chats WHERE group_id = ?', (group_id,))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def list_groups() -> List[int]:
    """Список всех групп"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT DISTINCT group_id FROM linked_chats')
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_chat_group(chat_id: int) -> Optional[int]:
    """Возвращает ID группы для беседы"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT group_id FROM linked_chats WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
