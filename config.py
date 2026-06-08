# ===== НАСТРОЙКИ БОТА =====
BOT_TOKEN = "8975105830:AAHSsz6kETM1gD-x2JnOlfVTeLOWMRp_8I4"  # ВСТАВЬТЕ СВОЙ ТОКЕН

# ID владельцев (кто имеет права администратора по умолчанию)
OWNER_IDS = [8881305868, 7993669578]  # ВСТАВЬТЕ СВОИ ID

# ===== ФИКСИРОВАННЫЕ БЕСЕДЫ =====
# Формат: ID_ГРУППЫ: [список ID чатов]
# ID чата можно получить командой /id в группе (обычно отрицательные числа)
FIXED_CHAT_GROUPS = {
    1: [-1003739741915, -1002987654321], # Группа 1: беседа 1, беседа 2
}

# Все разрешённые чаты (автоматически собираются из FIXED_CHAT_GROUPS)
ALLOWED_CHATS = []
for chats in FIXED_CHAT_GROUPS.values():
    ALLOWED_CHATS.extend(chats)

# ===== НАСТРОЙКИ БОТА =====
BOT_NAME = "Cromulent RP| Chat Manager"
BOT_VERSION = "1.0"

# Функции для работы с конфигом
def get_group_by_chat(chat_id: int):
    """Возвращает ID группы для чата"""
    for group_id, chats in FIXED_CHAT_GROUPS.items():
        if chat_id in chats:
            return group_id
    return None

def get_chats_by_group(group_id: int):
    """Возвращает список чатов в группе"""
    return FIXED_CHAT_GROUPS.get(group_id, [])

def get_all_groups():
    """Возвращает все группы"""
    return list(FIXED_CHAT_GROUPS.keys())
