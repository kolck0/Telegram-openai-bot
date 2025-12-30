from datetime import datetime, timedelta

from TelegramBot.logger import log_message
from config import *
from database import cursor, db
from ai import ask_ai
import re

def sanitize_html(text: str) -> str:
    allowed_tags = ["b", "i", "u", "s", "code", "pre", "a", "tg-spoiler"]
    # удаляем все теги кроме разрешённых
    text = re.sub(r"</?(?!{})(\w+).*?>".format("|".join(allowed_tags)), "", text)
    # заменяем <br> на перенос строки
    text = text.replace("<br>", "\n")
    # экранируем все угловые скобки, которые остались
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    # теперь разрешённые теги возвращаем обратно
    for tag in allowed_tags:
        text = text.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        text = text.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    return text


def check_flood(user_id):
    now = datetime.now()

    cursor.execute(
        "DELETE FROM flood WHERE user_id=? AND timestamp < ?",
        (user_id, (now - timedelta(seconds=FLOOD_INTERVAL)).isoformat())
    )

    cursor.execute(
        "SELECT COUNT(*) FROM flood WHERE user_id=?",
        (user_id,)
    )
    if cursor.fetchone()[0] >= FLOOD_LIMIT:
        return False

    cursor.execute(
        "INSERT INTO flood VALUES (?, ?)",
        (user_id, now.isoformat())
    )
    db.commit()
    return True

def check_limits(user_id):
    now = datetime.now()
    today = now.date().isoformat()

    cursor.execute(
        "SELECT last_question, count, date FROM users WHERE user_id=?",
        (user_id,)
    )
    row = cursor.fetchone()

    if not row:
        # Новый пользователь
        cursor.execute(
            "INSERT INTO users (user_id, last_question, count, date) VALUES (?, ?, ?, ?)",
            (user_id, now.isoformat(), 1, today)
        )
        db.commit()
        return True, None

    last, count, date = row

    # Если last_question пустой или некорректный
    try:
        last = datetime.fromisoformat(last)
    except (TypeError, ValueError):
        last = datetime.min  # позволяем сразу задать вопрос

    # Если день сменился — сбрасываем счётчик
    if date != today:
        count = 0
        cursor.execute(
            "UPDATE users SET count=?, date=? WHERE user_id=?",
            (0, today, user_id)
        )

    # Проверка дневного лимита
    if count >= MAX_QUESTIONS_PER_DAY:
        return False, f"❌ Лимит {MAX_QUESTIONS_PER_DAY} вопросов в день."

    # Обновляем запись в базе
    cursor.execute(
        "UPDATE users SET last_question=?, count=count+1 WHERE user_id=?",
        (now.isoformat(), user_id)
    )
    db.commit()
    return True, None


def register(bot):

    @bot.message_handler(commands=["start"])
    def start(message):
        bot.send_message(
            message.chat.id,
            "Привет 👋\nЗадай вопрос."
        )

    @bot.message_handler(func=lambda m: True)
    def handle(message):
        uid = message.from_user.id
        log_message(message)

        # Проверка флуда
        if not check_flood(uid):
            bot.send_message(message.chat.id, "🚫 Флуд.")
            return

        # Проверка лимитов
        ok, err = check_limits(uid)
        if not ok:
            bot.send_message(message.chat.id, err)
            return

        # Получаем ответ от AI
        answer = ask_ai(message.text)  # AI возвращает HTML

        # Сначала санитайзим ответ
        safe_answer = sanitize_html(answer)

        # Отправляем пользователю безопасный HTML
        bot.send_message(
            message.chat.id,
            safe_answer,
            parse_mode="HTML"
        )

