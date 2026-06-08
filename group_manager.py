from config import get_group_by_chat, get_chats_by_group
from database import add_global_ban, is_globally_banned
import asyncio

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
    from database import remove_global_ban
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
