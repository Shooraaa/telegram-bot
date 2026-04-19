import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv(8670521053:AAG9hqMCoLGQza9P5OJ8MLqgmcOIYlKULYo)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working 🚀")

def main():
    if not TOKEN:
        print("❌ BOT_TOKEN missing")
        exit()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("✅ Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
