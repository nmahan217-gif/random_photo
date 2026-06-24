import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# گرفتن توکن از محیط (Railway / Render / Local)
TOKEN = os.getenv("8828158985:AAGVLBXpKshC1f2NtbICPBhdvVoGb1kf9g0")

if not TOKEN:
    raise ValueError("TOKEN پیدا نشد! تو Railway Variables اضافه‌اش کن")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات روشنه 🔥")

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستورات: /start")

def main():
    # ساخت اپلیکیشن درست (مهم‌ترین بخش)
    app = Application.builder().token(TOKEN).build()

    # هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # اجرا
    print("Bot is running...")
    app.run_polling()

if name == "main":
    main()