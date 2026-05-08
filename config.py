import os
from dotenv import load_dotenv

# لود کردن متغیرهای محیطی از فایل .env
load_dotenv()

# ======= تلگرام =======
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")


AUTHORIZED_USERS = list(map(int, os.getenv("AUTHORIZED_USERS", "").split(",")))


GOOGLE_CREDENTIALS_FILE = "credentials.json"          
DRIVE_ROOT_FOLDER = "TelegramBot"                     
RECEIVED_FOLDER = os.path.join(DRIVE_ROOT_FOLDER, "Received")
YOUTUBE_FOLDER = os.path.join(DRIVE_ROOT_FOLDER, "YouTube")
SENT_FOLDER = os.path.join(DRIVE_ROOT_FOLDER, "Sent")


YT_DLP_OPTIONS_TEMPLATE = {
    'format': 'bestvideo[height<={height}]+bestaudio/best[height<={height}]',
    'merge_output_format': 'mp4',
    'outtmpl': '%(title)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
}
AUDIO_OPTIONS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': '%(title)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
}


SENT_POLL_INTERVAL = 30  