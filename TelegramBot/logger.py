# logger.py
from datetime import datetime

LOG_FILE = "messages.log"

def log_message(message):
    user = message.from_user

    user_id = user.id
    username = user.username if user.username else "no_username"
    first_name = user.first_name if user.first_name else ""
    last_name = user.last_name if user.last_name else ""
    text = message.text if message.text else "<no text>"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_line = (
        f"[{timestamp}] "
        f"id={user_id} "
        f"username=@{username} "
        f"name={first_name} {last_name} "
        f"text={text}\n"
    )

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)
