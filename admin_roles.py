from database import get_role
from config import OWNER_IDS, get_group_by_chat

ROLE_HIERARCHY = {
    "moderator": 1,
    "senior_moderator": 2,
    "administrator": 3
}

def get_user_role_level(user_id: int, chat_id: int) -> int:
    """Возвращает уровень роли пользователя в чате"""
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
    from database import is_globally_banned
    from config import get_group_by_chat
    group_id = get_group_by_chat(chat_id)
    if group_id:
        return is_globally_banned(user_id, group_id)
    return False
