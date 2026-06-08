import sqlite3
from typing import List, Optional, Tuple

DB_PATH = "chat_manager.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Роли пользователей в чатах
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER,
            chat_id INTEGER,
            role TEXT CHECK(role IN ('moderator', 'senior_moderator', 'administrator')),
            PRIMARY KEY (user_id, chat_id)
        )
    ''')
    
    # Глобальные баны (по группам бесед)
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
    
    # Ники
    c.execute('''
        CREATE TABLE IF NOT EXISTS nicknames (
            user_id INTEGER,
            chat_id INTEGER,
            nickname TEXT,
            PRIMARY KEY (user_id, chat_id)
        )
    ''')
    
    # Приветствия
    c.execute('''
        CREATE TABLE IF NOT EXISTS welcome_settings (
            chat_id INTEGER PRIMARY KEY,
            welcome_text TEXT
        )
    ''')
    
    # Фильтр слов
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
