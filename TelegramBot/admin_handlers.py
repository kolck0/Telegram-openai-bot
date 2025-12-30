from config import ADMINS
from database import cursor

def register(bot):

    def is_admin(uid):
        return uid in ADMINS

    @bot.message_handler(commands=["stats"])
    def stats(message):
        if not is_admin(message.from_user.id):
            return

        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]

        bot.send_message(
            message.chat.id,
            f"👤 Пользователей: {users}"
        )
