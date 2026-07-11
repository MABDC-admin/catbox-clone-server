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
                        'outtmpl': os.path.join(UPLOAD_DIR, '%(id)s.%(ext)s'),
                        'noplaylist': True,
                        'quiet': True,
                        'concurrent_fragment_downloads': concurrent_frags,
                        'postprocessor_args': ['-threads', '4']
                    }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(target_url, download=True)
                    filename = ydl.prepare_filename(info)
                    basename = os.path.basename(filename)
                    if is_mp3:
                        basename = os.path.splitext(basename)[0] + ".mp3"
                    
                    public_url = PUBLIC_URL_PREFIX + basename
                    
                    bot.reply_to(message, f"✅ Download Complete!\n\nHere is your permanent streaming link:\n\n{public_url}")
            except Exception as e:
                bot.reply_to(message, f"❌ Failed to download:\n{str(e)}")
                
        threading.Thread(target=download).start()
    else:
        bot.reply_to(message, "Send me ANY video link (YouTube, Dailymotion, Twitter, etc) and I'll download it straight to your Catbox-clone server without any size limits!")

if __name__ == "__main__":
    print("Bot is polling...")
    bot.infinity_polling()
