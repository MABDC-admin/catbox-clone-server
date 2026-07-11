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
                    
                    bot.reply_to(message, f"✅ **Download Complete!**\n\nHere is your permanent streaming link:\n\n{public_url}", parse_mode="Markdown")
            except Exception as e:
                bot.reply_to(message, f"❌ Failed to download:\n`{str(e)}`", parse_mode="Markdown")
                
        threading.Thread(target=download).start()
    else:
        bot.reply_to(message, "Send me a YouTube link and I'll download it straight to your Catbox-clone server without any size limits!")

if __name__ == "__main__":
    print("Bot is polling...")
    bot.infinity_polling()
