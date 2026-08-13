import os
import logging
import threading
from urllib.parse import quote
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Flask Web Server ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
BOT_TOKEN = "8952565156:AAHubKRCMzY6D6_hLcLwvta-3M5Pd_DoF-E"
STORAGE_CHANNEL_ID = -1004499292164
WEB_APP_URL = "https://ji0771295-ctrl.github.io/mybot"
MAIN_CHANNEL_USERNAME = "@MYxxxxx9"  # আপনার পাবলিক চ্যানেল

# /start হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if context.args:
        video_msg_id = context.args[0]
        try:
            await update.message.reply_text("⏳ আপনার ভিডিও ফাইলটি পাঠানো হচ্ছে, ১ সেকেন্ড অপেক্ষা করুন...")
            
            # প্রাইভেট চ্যানেল থেকে হুবহু ফাইলটি ইউজারের ইনবক্সে পাঠানো
            await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=int(video_msg_id)
            )
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            await update.message.reply_text("❌ দুঃখিত! ফাইলটি পাওয়া যায়নি অথবা প্রাইভেট চ্যানেল থেকে মুছে ফেলা হয়েছে।")
    else:
        await update.message.reply_text("স্বাগতম! ভিডিও দেখতে আমাদের চ্যানেলের লিংকে ক্লিক করে ৩টি অ্যাড শেষ করে আসুন।")

# /post কমান্ড (সরাসরি পাবলিক চ্যানেলে বাটনসহ পোস্ট যাবে)
async def create_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw_text = " ".join(context.args)
        if not raw_text or "|" not in raw_text:
            await update.message.reply_text(
                "❌ **ভুল ফরম্যাট!**\n\n"
                "সঠিক নিয়ম:\n"
                "`/post ভিডিও_আইডি | টাইটেল | থাম্বনেইল_ছবি_লিঙ্ক`\n\n"
                "উদাহরণ:\n`/post 25 | ভাইরাল ভিডিও | https://i.imgur.com/example.jpg`",
                parse_mode="Markdown"
            )
            return

        parts = [x.strip() for x in raw_text.split("|")]
        if len(parts) < 3:
            await update.message.reply_text("❌ সব তথ্য সঠিকভাবে দিন।")
            return

        msg_id, title, img_url = parts[0], parts[1], parts[2]

        encoded_v = quote(msg_id, safe='')
        encoded_t = quote(title, safe='')
        encoded_i = quote(img_url, safe='')

        final_mini_app_url = f"{WEB_APP_URL}?v={encoded_v}&t={encoded_t}&i={encoded_i}"

        # চ্যানেলে লিংক সঠিকভাবে কাজ করার জন্য URL button ব্যবহার করা হয়েছে
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Play Video 🔥", url=final_mini_app_url)]
        ])

        # সরাসরি পাবলিক চ্যানেল @MYxxxxx9 এ ছবি ও বাটন পাঠানো
        await context.bot.send_photo(
            chat_id=MAIN_CHANNEL_USERNAME,
            photo=img_url,
            caption=f"🎬 **{title}**\n\nনিচের বাটনে ক্লিক করে পুরো ভিডিওটি দেখুন:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        await update.message.reply_text(
            f"✅ পোস্টটি সফলভাবে **{MAIN_CHANNEL_USERNAME}** চ্যানেলে বাটনসহ পোস্ট করা হয়েছে!",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in create_post: {e}")
        await update.message.reply_text(f"❌ পোস্ট তৈরি করতে সমস্যা হয়েছে: `{str(e)}`", parse_mode="Markdown")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", create_post))

    logger.info("Bot is running 24/7...")
    app.run_polling()

if __name__ == '__main__':
    main()
