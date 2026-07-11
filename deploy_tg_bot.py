import paramiko
import time

BOT_CODE = """
import telebot
import yt_dlp
import os
import threading
import re

TOKEN = "8576316266:AAETjdNiKJ_xsv2cvjUdfnAMHv6fzeG7WoI"
bot = telebot.TeleBot(TOKEN)

UPLOAD_DIR = "/home/admin/catbox-clone-server/uploads"
PUBLIC_URL_PREFIX = "http://92.113.151.24:5001/f/"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text or ""
    
    # Check if there is a URL
    url_match = re.search(r"(https?://[^\s]+)", text)
    if url_match and ("youtube.com" in text or "youtu.be" in text):
        target_url = url_match.group(1)
        bot.reply_to(message, "⏳ Downloading video to server... (No file size limits!)")
        
        # Run in a separate thread so we don't block the bot
        def download():
            try:
                ydl_opts = {
                    'format': 'bestvideo+bestaudio/best', # Switched to DASH formats to allow 16x fragment parallel downloads
                    'outtmpl': os.path.join(UPLOAD_DIR, '%(id)s.%(ext)s'),
                    'noplaylist': True,
                    'quiet': True,
                    'concurrent_fragment_downloads': 16,
                    'postprocessor_args': ['-threads', '4'] # VPS has 4 cores
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(target_url, download=True)
                    filename = ydl.prepare_filename(info)
                    basename = os.path.basename(filename)
                    
                    public_url = PUBLIC_URL_PREFIX + basename
                    
                    bot.reply_to(message, f"✅ Download Complete!\\n\\nHere is your permanent streaming link:\\n\\n{public_url}")
            except Exception as e:
                bot.reply_to(message, f"❌ Failed to download:\\n{str(e)}")
                
        threading.Thread(target=download).start()
    else:
        bot.reply_to(message, "Send me a YouTube link and I'll download it straight to your Catbox-clone server without any size limits!")

if __name__ == "__main__":
    print("Bot is polling...")
    bot.infinity_polling()
"""

CLEANUP_CODE = """
import os
import time

UPLOAD_DIR = "/home/admin/catbox-clone-server/uploads"
SIX_DAYS = 6 * 24 * 60 * 60

now = time.time()
for f in os.listdir(UPLOAD_DIR):
    path = os.path.join(UPLOAD_DIR, f)
    if os.path.isfile(path):
        if os.stat(path).st_mtime < now - SIX_DAYS:
            try:
                os.remove(path)
            except:
                pass
"""

def main():
    print("Connecting to VPS...")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('92.113.151.24', username='admin', password='Denskie123')

    print("Writing telegram_bot.py...")
    sftp = c.open_sftp()
    with sftp.file('/home/admin/catbox-clone-server/telegram_bot.py', 'w') as f:
        f.write(BOT_CODE.strip())
    
    print("Writing cleanup.py...")
    with sftp.file('/home/admin/catbox-clone-server/cleanup.py', 'w') as f:
        f.write(CLEANUP_CODE.strip())
        
    sftp.close()

    commands = [
        "cd /home/admin/catbox-clone-server && ./venv/bin/pip install pyTelegramBotAPI yt-dlp",
        "pkill -f 'python telegram_bot.py'",
        "sleep 1",
        "cd /home/admin/catbox-clone-server && nohup ./venv/bin/python telegram_bot.py > bot.log 2>&1 &",
        "sleep 2",
        "ps aux | grep telegram_bot",
        "crontab -l 2>/dev/null | grep -v cleanup.py | crontab -",
        "(crontab -l 2>/dev/null; echo '0 0 * * * /home/admin/catbox-clone-server/venv/bin/python /home/admin/catbox-clone-server/cleanup.py') | crontab -"
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
