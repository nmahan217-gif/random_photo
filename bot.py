import os
import time
import random
import threading
import sqlite3
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = os.getenv("TOKEN")

# ---------- DB ----------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()
db_lock = threading.Lock()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id   TEXT,
    chat_id   TEXT,
    username  TEXT DEFAULT '',
    xp        INTEGER DEFAULT 0,
    last_time REAL DEFAULT 0,
    PRIMARY KEY (user_id, chat_id)
)
""")
conn.commit()

# ---------- تنظیمات ----------
XP_PER_PHOTO = 1
LEVEL_RATE   = 5    # هر 5 XP = 1 لول
COOLDOWN     = 10   # ثانیه — ضد فارم

TRIGGER_KEYWORD = "عکس رندوم"   # کپشنی که باید داشته باشه

# ---------- توابع دیتابیس ----------
def get_user(user_id: str, chat_id: str):
    with db_lock:
        cursor.execute(
            "SELECT xp, last_time FROM users WHERE user_id=? AND chat_id=?",
            (user_id, chat_id)
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "INSERT INTO users (user_id, chat_id, xp, last_time) VALUES (?,?,0,0)",
                (user_id, chat_id)
            )
            conn.commit()
            return 0, 0.0
        return row[0], row[1]

def update_user(user_id: str, chat_id: str, username: str, xp: int, last_time: float):
    with db_lock:
        cursor.execute("""
            INSERT INTO users (user_id, chat_id, username, xp, last_time)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, chat_id)
            DO UPDATE SET username=?, xp=?, last_time=?
        """, (user_id, chat_id, username, xp, last_time,
              username, xp, last_time))
        conn.commit()

def get_level(xp: int) -> int:
    return max(0, xp) // LEVEL_RATE

def xp_to_next_level(xp: int) -> int:
    return LEVEL_RATE - (xp % LEVEL_RATE)

# ---------- متن‌های رندوم ----------
CAPTIONS = [
    "🔥 عکس خفنی بود!",
    "😎 XP گرفتی!",
    "🎉 ادامه بده!",
    "✨ شانسی بود!",
    "💥 باحاله!",
    "🚀 پیش به سوی لول بعدی!",
    "👏 آفرین، ادامه بده!",
]

def random_caption() -> str:
    return random.choice(CAPTIONS)

# ---------- هندلر عکس ----------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg  = update.message
    user = msg.from_user

    # فقط اگه کپشن داشت و شامل کلمه کلیدی بود
    caption = (msg.caption or "").strip()
    if TRIGGER_KEYWORD not in caption:
        return

    chat_id   = str(msg.chat_id)
    user_id   = str(user.id)
    username  = user.username or user.first_name or str(user.id)

    xp, last_time = get_user(user_id, chat_id)
    now = time.time()

    # ضد فارم
    remaining = COOLDOWN - (now - last_time)
    if remaining > 0:
        await msg.reply_text(
            f"⏳ صبر کن! {int(remaining)} ثانیه دیگه می‌تونی XP بگیری."
        )
        return

    old_level = get_level(xp)
    xp       += XP_PER_PHOTO
    new_level = get_level(xp)

    update_user(user_id, chat_id, username, xp, now)

    text = random_caption()
    text += f"\n⭐ XP: {xp}  |  🏅 Level: {new_level}"
    text += f"\n📊 تا لول بعدی: {xp_to_next_level(xp)} XP"

    if new_level > old_level:
        text += f"\n\n🎊 لول آپ شدی! به Level {new_level} رسیدی! 🎉"

    await msg.reply_text(text)

# ---------- دستور /xp ----------
async def my_xp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.message.from_user
    chat_id = str(update.message.chat_id)
    user_id = str(user.id)

    xp, _ = get_user(user_id, chat_id)
    level   = get_level(xp)
    to_next = xp_to_next_level(xp)

    await update.message.reply_text(
        f"👤 {user.first_name}\n"
        f"⭐ XP: {xp}\n"
        f"🏅 Level: {level}\n"
        f"📊 تا لول بعدی: {to_next} XP"
    )

# ---------- دستور /top ----------
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)

    with db_lock:
        cursor.execute("""
            SELECT username, xp FROM users
            WHERE chat_id=?
            ORDER BY xp DESC
            LIMIT 10
        """, (chat_id,))
        rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("هنوز کسی XP نگرفته! 📸 عکس رندوم بفرست.")
        return

    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 لیدربورد گروه:\n\n"
    for i, (uname, xp) in enumerate(rows, start=1):
        icon  = medals[i - 1] if i <= 3 else f"{i}."
        level = get_level(xp)
        text += f"{icon} {uname} — XP: {xp} | Level: {level}\n"

    await update.message.reply_text(text)

# ---------- دستور /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 ربات عکس رندوم فعاله!\n\n"
        "📸 هر عکسی با کپشن «عکس رندوم» = XP\n"
        "⏱ کول‌داون: ۱۰ ثانیه بین هر XP\n\n"
        "📌 دستورات:\n"
        "/xp — XP و لول خودت\n"
        "/top — لیدربورد گروه"
    )

# ---------- main ----------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("xp",    my_xp))
    app.add_handler(CommandHandler("top",   leaderboard))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
