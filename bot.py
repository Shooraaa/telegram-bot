import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import yt_dlp

# Logging
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("8670521053:AAG9hqMCoLGQza9P5OJ8MLqgmcOIYlKULYo")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 Download Video", callback_data='video')],
        [InlineKeyboardButton("🎵 Download Audio", callback_data='audio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome!\n\nSend me a video link to download 🎬",
        reply_markup=reply_markup
    )

# Button handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['type'] = query.data

    await query.message.reply_text("🔗 Now send your link!")

# Download handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    download_type = context.user_data.get('type', 'video')

    await update.message.reply_text("⏳ Downloading...")

    try:
        ydl_opts = {}

        if download_type == 'audio':
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
            }
        else:
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'video.%(ext)s'
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        # Send file
        if download_type == 'audio':
            file_name = file_name.rsplit(".", 1)[0] + ".mp3"
            await update.message.reply_audio(audio=open(file_name, 'rb'))
        else:
            await update.message.reply_video(video=open(file_name, 'rb'))

        await update.message.reply_text("✅ Done!\n🚀 @ShooraVideo_Bot")

    except Exception as e:
        await update.message.reply_text("❌ Error: Invalid link or failed download")

# Main
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
