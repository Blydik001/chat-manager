import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

# НАСТРОЙКА: Вставьте сюда свои данные
TOKEN = "vk1.a.1_vaGTlTSVYzOPCjOLr9RTimJfzW7NfEntNrR8cng38hICHY8UI3weotFtkx2DTHMS_JnCQwgv4dmp1zjx9SUqWu_s08AYuuBgIXl3gfH-0H6TEdA-QI54jlBN82FikmQ5SRkRQcBOuD0OmvCUWozIj4XPrN_P7FAkxo8krfGxFogq7yk2waqyfiAlMzy1flcZCMCNlqIkvwqjtZ-0Enww"
GROUP_ID = 2000000179  # Числовой ID группы (без минуса)

# Текст для команды /help
HELP_TEXT = (
    "Команды пользователей:\n"
    "/info — официальные ресурсы форбса\n"
    "/id — узнать оригинальный ID пользователя в ВК\n"
    "/stats — информация о пользователе"
)

def main():
    # Авторизация группы
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    
    # Инициализация Long Poll для сообщества
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    print("Бот успешно запущен через vk_api...")

    for event in longpoll.listen():
        # Проверяем, что пришло новое сообщение
        if event.type == VkBotEventType.MESSAGE_NEW:
            message_text = event.obj.message['text'].strip()
            peer_id = event.obj.message['peer_id']
            
            # Обработка команды /help
            if message_text.lower() == "/help":
                try:
                    vk.messages.send(
                        peer_id=peer_id,
                        message=HELP_TEXT,
                        random_id=vk_api.utils.get_random_id()
                    )
                except Exception as e:
                    print(f"Ошибка отправки сообщения: {e}")

if __name__ == "__main__":
    main()
