import logging
import random
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import os
TOKEN = os.getenv("8828158985:AAGVLBXpKshC1f2NtbICPBhdvVoGb1kf9g0")

# دیتابیس ساده
conn = sqlite3.connect("game.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0
)
""")
conn.commit()

def add_xp(user_id, amount=10):
    cur.execute("SELECT level, xp FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    if not row:
        cur.execute("INSERT INTO users (user_id, level, xp) VALUES (?, 1, 0)", (user_id,))
        level, xp = 1, 0
    else:
        level, xp = row

    xp += amount

    # لول آپ ساده
    if xp >= 100:
        level += 1
        xp = 0

    cur.execute("UPDATE users SET level=?, xp=? WHERE user_id=?", (level, xp, user_id))
    conn.commit()

    return level, xp


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات فعال شد. عکس بفرست تا لول آپ بگیری")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    level, xp = add_xp(user.id, amount=random.randint(5, 20))

    captions = [
        "عکس رندوم ",
        "آپلود شد!",
        "سیستم ثبت کرد 📸",
        "عکس دریافت شد"
    ]

    text = random.choice(captions)

    await update.message.reply_photo(
        photo=update.message.photo[-1].file_id,
        caption=f"{text}\nLevel: {level} | XP: {xp}/100"
    )


def main():
    logging.basicConfig(level=logging.INFO)

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    app.run_polling()


if name == "main":
    main()