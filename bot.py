import os
import glob
import yt_dlp
import pickle
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# ================= CONFIG =================
BOT_TOKEN = "8670521053:AAG9hqMCoLGQza9P5OJ8MLqgmcOIYlKULYo"
MAX_SIZE = 50 * 1024 * 1024
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# ================= GOOGLE DRIVE (FIXED LOGIN) =================
def upload_to_drive(file_name):
    creds = None

    # 🔥 Load saved login
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # 🔥 Login only first time
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_name, resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    service.permissions().create(
        fileId=file.get('id'),
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    return f"https://drive.google.com/file/d/{file.get('id')}/view"

# ================= DOWNLOAD =================
async def process_download(query, url, mode):
    await query.message.reply_text("⚡ Downloading...")

    if mode == "video":
        ydl_opts = {
            'format': 'bv*+ba/best',
            'outtmpl': 'file_%(id)s.%(ext)s',
            'noplaylist': True,
            'concurrent_fragment_downloads': 5,
            'merge_output_format': 'mp4'
        }
    else:
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': 'file_%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3'
            }]
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        file = max(glob.glob("*.*"), key=os.path.getctime)
        size = os.path.getsize(file)

        await query.message.reply_text("🚀 Uploading...")

        if size <= MAX_SIZE:
            await query.message.reply_document(document=open(file, 'rb'))
        else:
            await query.message.reply_text("☁️ Uploading to Google Drive...")
            link = upload_to_drive(file)
            await query.message.reply_text(f"🔗 {link}")

        os.remove(file)

    except Exception as e:
        await query.message.reply_text(f"❌ Error: {e}")

# ================= BOT =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send video link 🎬")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['url'] = update.message.text

    keyboard = [
        [InlineKeyboardButton("🎬 Video", callback_data='video')],
        [InlineKeyboardButton("🎧 Audio", callback_data='audio')]
    ]

    await update.message.reply_text("Choose format:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get('url')

    asyncio.create_task(process_download(query, url, query.data))

# ================= MAIN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_handler))

print("🚀 FINAL BOT RUNNING")
app.run_polling()