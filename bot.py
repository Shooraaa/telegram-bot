import os
import glob
import yt_dlp
import pickle

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# ================= CONFIG =================

BOT_TOKEN = os.environ.get("8670521053:AAG9hqMCoLGQza9P5OJ8MLqgmcOIYlKULYo")
MAX_SIZE = 50 * 1024 * 1024
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# ================= GOOGLE DRIVE =================

def upload_to_drive(file_name):
creds = None

# create credentials.json from env
if not os.path.exists("credentials.json"):
    with open("credentials.json", "w") as f:
        f.write(os.environ.get("GOOGLE_CREDENTIALS"))

if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

if not creds:
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

def process_download(update, context, mode):
url = context.user_data.get("url")
update.callback_query.message.reply_text("⚡ Downloading...")

if mode == "video":
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'file_%(id)s.%(ext)s',
        'noplaylist': True
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
        ydl.download([url])

    file = max(glob.glob("*.*"), key=os.path.getctime)
    size = os.path.getsize(file)

    update.callback_query.message.reply_text("🚀 Uploading...")

    if size <= MAX_SIZE:
        update.callback_query.message.reply_document(open(file, 'rb'))
    else:
        update.callback_query.message.reply_text("☁️ Uploading to Google Drive...")
        link = upload_to_drive(file)
        update.callback_query.message.reply_text(f"🔗 {link}")

    os.remove(file)

except Exception as e:
    update.callback_query.message.reply_text(f"❌ Error: {e}")

# ================= HANDLERS =================

def start(update, context):
update.message.reply_text("Send video link 🎬")

def handle_link(update, context):
context.user_data['url'] = update.message.text

keyboard = [
    [InlineKeyboardButton("🎬 Video", callback_data='video')],
    [InlineKeyboardButton("🎧 Audio", callback_data='audio')]
]

update.message.reply_text("Choose format:", reply_markup=InlineKeyboardMarkup(keyboard))

def button(update, context):
query = update.callback_query
query.answer()

process_download(update, context, query.data)

# ================= MAIN =================

updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_link))
dp.add_handler(CallbackQueryHandler(button))

print("🚀 FINAL BOT RUNNING")
updater.start_polling()
updater.idle()
