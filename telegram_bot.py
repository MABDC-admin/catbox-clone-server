import telebot
import yt_dlp
import os
import threading
import re
import json
import glob
from minio import Minio

TOKEN = "8576316266:AAETjdNiKJ_xsv2cvjUdfnAMHv6fzeG7WoI"
bot = telebot.TeleBot(TOKEN)

MINIO_ENDPOINT = "minio.web.mabdc.org"
BUCKET_NAME = "tg-bot-video"
PUBLIC_URL_PREFIX = f"https://{MINIO_ENDPOINT}/{BUCKET_NAME}/"

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key="admin",
    secret_key="Denskie123",
    secure=True
)

def ensure_bucket():
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
            policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*"]
                }]
            }
            minio_client.set_bucket_policy(BUCKET_NAME, json.dumps(policy))
    except Exception as e:
        print("MinIO Init Error:", e)

ensure_bucket()

UPLOAD_DIR = "/home/admin/catbox-clone-server/uploads"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text or ""
    
    # Check if there is a URL
    url_match = re.search(r"(https?://[^\s]+)", text)
    if url_match:
        target_url = url_match.group(1)
        audio_only = "mp3" in text.lower()
        is_youtube = "youtube.com" in target_url or "youtu.be" in target_url
        concurrent_frags = 16 if is_youtube else 1
        
        msg = "⏳ Downloading audio (MP3)..." if audio_only else "⏳ Downloading video..."
        bot.reply_to(message, msg)
        
        # Run in a separate thread so we don't block the bot
        def download():
            try:
                if "tiktok.com" in target_url:
                    # TikTok occasionally blocks yt-dlp if it tries to extract too many formats; keeping it simple
                    ydl_opts = {
                        'format': 'best',
                        'outtmpl': os.path.join(UPLOAD_DIR, '%(id)s.%(ext)s'),
                        'noplaylist': True,
                        'quiet': True,
                        'concurrent_fragment_downloads': concurrent_frags,
                        'postprocessor_args': ['-threads', '4', '-movflags', '+faststart']
                    }
                elif audio_only:
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(UPLOAD_DIR, '%(id)s.%(ext)s'),
                        'noplaylist': True,
                        'quiet': True,
                        'concurrent_fragment_downloads': concurrent_frags,
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'postprocessor_args': ['-threads', '4', '-movflags', '+faststart']
                    }
                else:
                    ydl_opts = {
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'merge_output_format': 'mp4',
                        'outtmpl': os.path.join(UPLOAD_DIR, '%(id)s.%(ext)s'),
                        'noplaylist': True,
                        'quiet': True,
                        'concurrent_fragment_downloads': concurrent_frags,
                        'postprocessors': [
                            {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'},
                            {'key': 'FFmpegMetadata', 'add_metadata': True}
                        ],
                        'postprocessor_args': {'video': ['-threads', '4', '-movflags', '+faststart']}
                    }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(target_url, download=True)
                    file_id = info['id']
                    
                    # Find the exact file yt-dlp created (it might have changed extension to mp4/mkv/mp3)
                    found_files = glob.glob(os.path.join(UPLOAD_DIR, f"{file_id}.*"))
                    found_files = [f for f in found_files if not f.endswith('.part')]
                    
                    if not found_files:
                        raise Exception("File was not saved correctly locally.")
                        
                    actual_file = found_files[0]
                    basename = os.path.basename(actual_file)
                    
                    ext = basename.split('.')[-1].lower()
                    content_type = 'application/octet-stream'
                    if ext == 'mp4': content_type = 'video/mp4'
                    elif ext == 'webm': content_type = 'video/webm'
                    elif ext == 'mkv': content_type = 'video/x-matroska'
                    elif ext == 'mp3': content_type = 'audio/mpeg'
                    
                    msg2 = bot.reply_to(message, "☁️ Uploading to MinIO storage...")
                    minio_client.fput_object(
                        BUCKET_NAME,
                        basename,
                        actual_file,
                        content_type=content_type
                    )
                    
                    public_url = PUBLIC_URL_PREFIX + basename
                    bot.edit_message_text(f"✅ Download & Upload Complete!\n\nHere is your permanent streaming link:\n\n{public_url}", chat_id=message.chat.id, message_id=msg2.message_id)
                    
                    try:
                        os.remove(actual_file)
                    except:
                        pass
            except Exception as e:
                bot.reply_to(message, f"❌ Failed to download:\n{str(e)}")
                
        threading.Thread(target=download).start()
    else:
        bot.reply_to(message, "Send me ANY video link (YouTube, Facebook, Dailymotion, Twitter, TikTok, etc) and I'll download it straight to your Catbox-clone server without any size limits!")

if __name__ == "__main__":
    print("Bot is polling...")
    bot.infinity_polling()
