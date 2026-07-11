import paramiko
import time

BOT_CODE = r"""
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

UPLOAD_DIR = "/root/catbox-clone-server/uploads"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text or ""
    
    # Check if there is a URL
    url_match = re.search(r"(https?://[^\s]+)", text)
    if url_match:
        target_url = url_match.group(1)
        is_mp3 = "mp3" in text.lower()
        is_youtube = "youtube.com" in target_url or "youtu.be" in target_url
        concurrent_frags = 16 if is_youtube else 1
        
        msg = "⏳ Downloading audio (MP3)..." if is_mp3 else "⏳ Downloading video..."
        bot.reply_to(message, msg)
        
        # Run in a separate thread so we don't block the bot
        def download():
            try:
                if is_mp3:
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
                        'postprocessor_args': ['-threads', '4']
                    }
                else:
                    ydl_opts = {
                        'format': 'bestvideo+bestaudio/best',
                        'merge_output_format': 'mp4',
                        'outtmpl': os.path.join(UPLOAD_DIR, '%(id)s.%(ext)s'),
                        'noplaylist': True,
                        'quiet': True,
                        'concurrent_fragment_downloads': concurrent_frags,
                        'postprocessor_args': ['-threads', '4']
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

"""

CLEANUP_CODE = """
import os
import time

UPLOAD_DIR = "/root/catbox-clone-server/uploads"
ONE_DAY = 24 * 60 * 60

now = time.time()
for f in os.listdir(UPLOAD_DIR):
    path = os.path.join(UPLOAD_DIR, f)
    if os.path.isfile(path):
        if os.stat(path).st_mtime < now - ONE_DAY:
            try:
                os.remove(path)
            except:
                pass
"""

def main():
    print("Connecting to VPS...")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('100.124.32.11', username='root', port=1988, key_filename='C:/Users/DENNIS/Downloads/95.217/minio_root_ed25519')

    print("Writing telegram_bot.py...")
    sftp = c.open_sftp()
    
    # Ensure directory exists on new VPS
    c.exec_command('mkdir -p /root/catbox-clone-server/uploads')
    
    with sftp.file('/root/catbox-clone-server/telegram_bot.py', 'w') as f:
        f.write(BOT_CODE.strip())
    
    print("Writing cleanup.py...")
    with sftp.file('/root/catbox-clone-server/cleanup.py', 'w') as f:
        f.write(CLEANUP_CODE.strip())
        
    sftp.close()

    commands = [
        "cd /root/catbox-clone-server && python3 -m venv venv && ./venv/bin/pip install pyTelegramBotAPI yt-dlp curl-cffi flask minio",
        "pkill -f 'python telegram_bot.py'",
        "sleep 1",
        "cd /root/catbox-clone-server && nohup ./venv/bin/python telegram_bot.py > bot.log 2>&1 &",
        "sleep 2",
        "ps aux | grep telegram_bot",
        "crontab -l 2>/dev/null | grep -v cleanup.py | crontab -",
        "(crontab -l 2>/dev/null; echo '0 0 * * * /root/catbox-clone-server/venv/bin/python /root/catbox-clone-server/cleanup.py') | crontab -"
    ]

    for cmd in commands:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = c.exec_command(cmd)
        try:
            print(stdout.read().decode('utf-8', errors='ignore').strip())
        except:
            pass
        err = stderr.read().decode('utf-8', errors='ignore').strip()
        if err:
            print("ERR:", err)

    c.close()
    print("Bot deployed successfully!")

if __name__ == "__main__":
    main()
