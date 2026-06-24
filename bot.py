from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import random
import os
import sqlite3

TOKEN = os.getenv("TOKEN")

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

    if xp >= 100:
        level += 1
        xp = 0

    cur.execute("UPDATE users SET level=?, xp=? WHERE user_id=?", (level, xp, user_id))
    conn.commit()

    return level, xp


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات فعال است")


# اینجا برای گروه و خصوصی هر دو کار می‌کند
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    level, xp = add_xp(user.id, random.randint(5, 20))

    captions = [
        "عکس ثبت شد",
        "آپلود گروهی",
        "سیستم دریافت کرد",
        "عکس رندوم"
    ]

    text = random.choice(captions)

    await update.message.reply_photo(
        photo=update.message.photo[-1].file_id,
        caption=f"{text}\nLevel: {level} | XP: {xp}/100"
    )


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

app.run_polling()