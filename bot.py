import asyncio
import logging
from datetime import datetime, time
import pytz
import random
import json
import re
from collections import defaultdict
import math
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# 🔹 НАСТРОЙКИ
BOT_TOKEN = "8953075279:AAFgJ7Zb8Na1ovlbh4KHKWc9Kpft9BeorFM"
GROUP_CHAT_ID = -1003723783593
BOT_NAME = "Кейл"

# Включаем логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Московский часовой пояс
MSK_TZ = pytz.timezone('Europe/Moscow')

# Список фраз для случайной отправки
PHRASES = [
    "Что делаете?",
    "Сколько у кого банов?",
    "Когда у нас собрание в отделе?",
    "Не важно кто лев, важно кто снёс владельца казино.",
    "Какая у вас любимая песня?",
    "Какое ваше любимое блюдо?",
    "Хотели бы повыситься до ЗКТС?",
    "Пора бы почистить форум..."
]

# 🔹 БАЗА ЗНАНИЙ БОТА
KNOWLEDGE_BASE = {
    # Приветствия
    r"\b(привет|здравствуй|хай|хелло|здарова|ку|прив|доброе утро|добрый день|добрый вечер)\b": [
        "Привет-привет! 👋",
        "Здарова! Как жизнь?",
        "Приветствую в чате! ✨",
        "Хай! Чё как?",
        "О, привет! Давно не виделись!",
        "Привет! Что расскажешь?",
        "Здравствуй! Как настрой?"
    ],
    
    # Как дела
    r"\b(как дела|как ты|как жизнь|как настроение|чё как|что как)\b": [
        "Да нормально, работаю помаленьку 💪",
        "Отлично! А у тебя?",
        "Как у модератора - баны раздаю, порядок навожу 😎",
        "Лучше всех! А ты как?",
        "Дела? Да как обычно - слежу за порядком в чате",
        "Нормально, только форум бы почистить не мешало..."
    ],
    
    # Кто такой бот
    r"\b(кто ты|ты кто|что ты такое|расскажи о себе|чей ты)\b": [
        f"Я {BOT_NAME}! Бот-модератор этого чата. Слежу за порядком, помогаю, общаюсь 🤖",
        f"Я {BOT_NAME}, местный помощник. Если что нужно - обращайся!",
        f"{BOT_NAME} к вашим услугам! Модерирую чат и развлекаю народ 😄"
    ],
    
    # Что делаешь
    r"\b(что делаешь|чем занят|что творишь)\b": [
        "Да вот, за порядком слежу 👀",
        "Баны считаю... Шучу, просто общаюсь с вами!",
        "Работаю! За вами присматриваю 😄",
        "Форум чищу... Шучу, отдыхаю пока!",
        "Жду, когда кто-нибудь правила нарушит 👮‍♂️"
    ],
    
    # Собрание
    r"\b(собрание|собрания|когда собрание|митинг|встреча)\b": [
        "Собрание? Я за любой кипиш! 📅",
        "Обычно по пятницам, но лучше уточнить у начальства",
        "Как будут новости - сразу сообщу!",
        "Пока не назначили, но я наготове 💪"
    ],
    
    # Баны
    r"\b(бан|баны|забанили|банхаммер)\b": [
        "Бан - это святое! 🔨",
        "Кому-то пора? 😏",
        "У меня сегодня без банов, скучно...",
        "Банхаммер всегда наготове!"
    ],
    
    # Песни
    r"\b(песня|песни|музыка|трек|музло)\b": [
        "Я меломан! От классики до рока 🎵",
        "Сейчас в топе - Ostin Powers!",
        "Что-нибудь бодрое, чтоб баны раздавать!",
        "Рок - наше всё! А у тебя какой любимый жанр?"
    ],
    
    # Еда
    r"\b(еда|покушать|пицца|бургер|суши|вкусняшки|блюдо|готовить)\b": [
        "Пицца - это классика! 🍕",
        "Я за шашлык! А ты?",
        "Суши? Уважаю!",
        "Пельмени - наше всё!",
        "Бургеры - это сила! 🍔"
    ],
    
    # Повышение
    r"\b(повышение|повыситься|ЗКТС|карьера|расти|должность)\b": [
        "ЗКТС? А почему бы и нет! 💼",
        "Я только за! Когда подаём заявление?",
        "Повышение - это всегда хорошо!",
        "Готовь документы! Я поддержу ✊"
    ],
    
    # Форум
    r"\b(форум|почистить|уборка|чистка)\b": [
        "Да, пора бы! Кто начнёт? 🧹",
        "Форум чистить - дело святое!",
        "Я уже морально готов!",
        "Только давайте без выходных..."
    ],
    
    # Лев/владелец казино
    r"\b(лев|казино|владелец)\b": [
        "Не важно кто лев, важно кто снёс владельца казино! 🦁",
        "Это легендарная фраза!",
        "Помню тот случай... Эпично было!",
        "Золотые слова!"
    ],
    
    # Погода
    r"\b(погода|дождь|солнце|холодно|жарко|снег)\b": [
        "Погода? Я в серверной сижу, мне норм 😄",
        "Главное - в чате погода хорошая!",
        "Не знаю, я на улицу не выхожу...",
        "У нас в дата-центре всегда +20°C!"
    ],
    
    # Прощание
    r"\b(пока|до свидания|увидимся|спокойной ночи|бай)\b": [
        "Пока! Береги себя! 👋",
        "До связи! Не нарушай правила 😉",
        "Увидимся в чате!",
        "Спокойной ночи! Я покараулю 🌙",
        "Бай-бай! Заходи ещё!"
    ],
    
    # Спасибо
    r"\b(спасибо|благодарю|спс|сяб)\b": [
        "Всегда пожалуйста! 😊",
        "Обращайся!",
        "Для вас - что угодно!",
        "Не за что! Я ж бот, мне не сложно 🤖"
    ],
    
    # Вопросы к боту
    r"\b(как ты работаешь|твой код|кто тебя сделал|твой создатель)\b": [
        "Работаю на чистом энтузиазме и Python!",
        "Мой код прост, но эффективен 💻",
        "Создан, чтобы помогать! А кто именно - секрет 🤫"
    ],
    
    # Шутки
    r"\b(шутка|анекдот|рассмеши|пошути|прикол)\b": [
        "Почему программисты не любят природу? Слишком много багов! 🐛",
        "Встретились два байта в баре... Один говорит: 'У меня бит не стоит!' 💾",
        "Колобок повесился... Сказки ложь, да в них намек! 🎭",
        "Почему боты не ходят в спортзал? У них и так есть сила интернета! 💪"
    ],
    
    # Default ответы
    "default": [
        "Хм, интересно! Расскажи подробнее 🤔",
        "Я понял, но давай уточним?",
        "Вот это поворот! Продолжай...",
        "Честно говоря, я не совсем понял. Можешь перефразировать?",
        "🤔 Задумался... А что ты имеешь в виду?",
        "Ммм, что-то я не догоняю. Объяснишь?",
        "Давай по-русски, а то я бот всё-таки 😄",
        "Интересная мысль! А что дальше?",
        "Подожди, я записываю... ✍️ Шучу, у меня память хорошая",
        "Знаешь, я тут подумал... Нет, показалось"
    ]
}

# 🔹 ПРОСТОЙ ПОИСКОВЫЙ ДВИЖОК (TF-IDF)
class SimpleAI:
    def __init__(self):
        self.word_freq = defaultdict(lambda: defaultdict(int))  # {category: {word: count}}
        self.category_count = defaultdict(int)  # {category: total_words}
        self.total_docs = 0
        self._train()
    
    def _tokenize(self, text: str) -> list:
        """Разбивает текст на слова"""
        # Приводим к нижнему регистру и убираем знаки препинания
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.split()
    
    def _train(self):
        """Обучается на базе знаний"""
        for pattern, responses in KNOWLEDGE_BASE.items():
            if pattern == "default":
                continue
            
            # Создаём категорию на основе паттерна
            category = pattern
            words = self._tokenize(pattern)
            
            for word in words:
                self.word_freq[category][word] += 1
                self.category_count[category] += 1
            
            self.total_docs += 1
    
    def _cosine_similarity(self, text1: str, text2: str) -> float:
        """Вычисляет косинусное сходство между двумя текстами"""
        words1 = set(self._tokenize(text1))
        words2 = set(self._tokenize(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / math.sqrt(len(words1) * len(words2))
    
    def find_best_response(self, message: str) -> str:
        """Находит лучший ответ на сообщение"""
        message_lower = message.lower()
        
        best_score = -1
        best_responses = None
        
        # Проверяем все паттерны
        for pattern, responses in KNOWLEDGE_BASE.items():
            if pattern == "default":
                continue
            
            # Сначала проверяем точное совпадение по регулярке
            if re.search(pattern, message_lower):
                return random.choice(responses)
            
            # Если нет точного совпадения, используем косинусное сходство
            score = self._cosine_similarity(pattern, message_lower)
            
            if score > best_score:
                best_score = score
                best_responses = responses
        
        # Если нашли что-то похожее (порог 0.1)
        if best_score > 0.1 and best_responses:
            return random.choice(best_responses)
        
        # Иначе возвращаем default ответ
        return random.choice(KNOWLEDGE_BASE["default"])

# Создаём экземпляр ИИ
ai = SimpleAI()

# Хранилище контекста диалога (последние темы)
dialog_context = defaultdict(list)

def get_time_based_greeting():
    """Возвращает приветствие в зависимости от времени суток МСК"""
    msk_time = datetime.now(MSK_TZ)
    hour = msk_time.hour
    
    if 7 <= hour < 12:
        return "Доброе утро!"
    elif 12 <= hour < 18:
        return "Добрый день!"
    elif 21 <= hour < 24:
        return "Спокойной ночи!"
    return None

def is_bot_mentioned(text: str) -> bool:
    """Проверяет, обращаются ли к боту по имени"""
    bot_names = [BOT_NAME.lower(), BOT_NAME.capitalize(), f"@{BOT_NAME.lower()}"]
    text_lower = text.lower()
    
    for name in bot_names:
        if name in text_lower:
            return True
    return False

def clean_mention(text: str) -> str:
    """Очищает текст от упоминания бота"""
    cleaned = text
    for name in [f"@{BOT_NAME}", BOT_NAME, BOT_NAME.lower()]:
        cleaned = cleaned.replace(name, "").strip()
    return cleaned

def add_knowledge(question: str, answers: list):
    """Добавляет новые знания в базу"""
    pattern = re.escape(question.lower())
    KNOWLEDGE_BASE[pattern] = answers
    # Переобучаем ИИ
    global ai
    ai = SimpleAI()

async def send_scheduled_messages():
    """Отправка сообщений каждые 2 часа с 12:00 до 22:00 МСК"""
    while True:
        msk_time = datetime.now(MSK_TZ)
        hour = msk_time.hour
        
        if 12 <= hour < 22:
            try:
                phrase = random.choice(PHRASES)
                
                greeting = get_time_based_greeting()
                if greeting:
                    phrase = f"{greeting}\n{phrase}"
                
                await bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=phrase
                )
                logging.info(f"Отправлено сообщение по расписанию: {phrase}")
            except Exception as e:
                logging.error(f"Ошибка отправки по расписанию: {e}")
        
        await asyncio.sleep(7200)

async def get_ai_response(user_id: int, user_message: str) -> str:
    """Получение ответа от своего ИИ"""
    try:
        # Добавляем контекст
        context = " ".join(dialog_context[user_id][-3:])  # Последние 3 сообщения
        full_message = f"{context} {user_message}" if context else user_message
        
        # Получаем ответ
        response = ai.find_best_response(full_message)
        
        # Сохраняем в контекст
        dialog_context[user_id].append(user_message)
        if len(dialog_context[user_id]) > 5:
            dialog_context[user_id] = dialog_context[user_id][-5:]
        
        return response
        
    except Exception as e:
        logging.error(f"Ошибка AI: {e}")
        return "🤖 Хм, что-то я запутался. Давай ещё раз?"

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start в ЛС"""
    if message.chat.type != "private":
        return
    
    user_name = message.from_user.first_name
    greeting = get_time_based_greeting() or "Привет"
    
    await message.reply(
        f"{greeting}, {user_name}! Я {BOT_NAME} 🤖\n\n"
        "Я работаю на собственной базе знаний!\n"
        "Можешь общаться со мной здесь или в общем чате.\n"
        "В чате обращайся ко мне по имени: **Кейл** или **@Кейл**\n\n"
        "📚 Команды:\n"
        "/clear - очистить историю\n"
        "/learn вопрос | ответ1 | ответ2 - научить меня\n"
        "/topic ID текст - отправить в топик\n"
        "/base - посмотреть размер базы знаний",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    """Очистка истории диалога"""
    user_id = message.from_user.id
    if user_id in dialog_context:
        del dialog_context[user_id]
    
    await message.reply("🧹 Окей, всё забыл!")

@dp.message(Command("base"))
async def cmd_base(message: Message):
    """Показывает размер базы знаний"""
    patterns_count = len(KNOWLEDGE_BASE) - 1  # Минус default
    total_responses = sum(len(v) for k, v in KNOWLEDGE_BASE.items() if k != "default")
    
    await message.reply(
        f"📚 Моя база знаний:\n"
        f"• Тем: {patterns_count}\n"
        f"• Вариантов ответов: {total_responses}\n"
        f"• Контекстная память: 5 сообщений\n\n"
        f"Работаю на своём движке! 🧠"
    )

@dp.message(Command("learn"))
async def cmd_learn(message: Message):
    """Обучение бота новым фразам"""
    if message.chat.type != "private":
        await message.reply("Обучение доступно только в личных сообщениях!")
        return
    
    # Формат: /learn вопрос | ответ1 | ответ2 | ответ3
    text = message.text.replace("/learn", "").strip()
    
    if "|" not in text:
        await message.reply(
            "❌ Неверный формат!\n"
            "Используй: `/learn вопрос | ответ1 | ответ2`\n"
            "Например: `/learn как жизнь | Отлично! | Нормально | Бывало и лучше`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    parts = text.split("|")
    question = parts[0].strip()
    answers = [p.strip() for p in parts[1:] if p.strip()]
    
    if not question or not answers:
        await message.reply("Нужен вопрос и хотя бы один ответ!")
        return
    
    add_knowledge(question, answers)
    
    await message.reply(
        f"✅ Научился!\n"
        f"Вопрос: {question}\n"
        f"Ответов: {len(answers)}"
    )

@dp.message(Command("topic"))
async def send_to_topic(message: Message):
    """Отправка сообщения в конкретный топик"""
    args = message.text.split(maxsplit=2)
    
    if len(args) < 3:
        await message.reply(
            "❌ Неверный формат.\n"
            "Используй: `/topic ID_топика текст`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        topic_id = int(args[1])
        user_text = args[2]
    except ValueError:
        await message.reply("❌ ID топика должен быть числом.")
        return

    try:
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=user_text,
            message_thread_id=topic_id
        )
        await message.reply(f"✅ Отправил в топик {topic_id}!")
    
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        await message.reply("❌ Не вышло. Проверь права и ID.")

@dp.message()
async def handle_messages(message: Message):
    """Основной обработчик сообщений"""
    if message.from_user.id == bot.id:
        return
    
    text = message.text
    if not text:
        return
    
    chat_type = message.chat.type
    
    if chat_type == "private":
        await bot.send_chat_action(message.chat.id, "typing")
        response = await get_ai_response(message.from_user.id, text)
        
        try:
            await message.reply(response)
        except Exception:
            for x in range(0, len(response), 4096):
                await message.reply(response[x:x+4096])
        return
    
    if chat_type in ["group", "supergroup"]:
        if is_bot_mentioned(text):
            clean_text = clean_mention(text)
            
            if not clean_text:
                greeting = get_time_based_greeting()
                await message.reply(f"{greeting or 'Привет'}! Я {BOT_NAME}, слушаю 👂")
                return
            
            await bot.send_chat_action(message.chat.id, "typing")
            response = await get_ai_response(message.from_user.id, clean_text)
            
            try:
                reply_kwargs = {}
                if message.message_thread_id:
                    reply_kwargs['message_thread_id'] = message.message_thread_id
                
                await message.reply(response, **reply_kwargs)
            except Exception:
                for x in range(0, len(response), 4096):
                    await message.reply(response[x:x+4096], **reply_kwargs)

async def on_startup():
    """Действия при запуске бота"""
    logging.info(f"Бот {BOT_NAME} запущен со своей базой знаний!")
    logging.info(f"Загружено тем: {len(KNOWLEDGE_BASE) - 1}")
    asyncio.create_task(send_scheduled_messages())

async def main():
    dp.startup.register(on_startup)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
