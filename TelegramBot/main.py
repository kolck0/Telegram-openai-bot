import telebot
from config import TELEGRAM_TOKEN
import user_handlers
import admin_handlers

bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_handlers.register(bot)
admin_handlers.register(bot)

print("Bot started")
bot.infinity_polling()
