import os
import logging
import threading
from urllib.parse import quote
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Flask Web Server (২৪ ঘণ্টা সচল রাখার জন্য) ---
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

# /start হ্যান্ডলার (ইউজার যখন অ্যাড দেখে ফিরে আসবে)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # যদি ইউজার কোনো ভিডিও আইডি সহ /start চাপ দিয়ে আসে
    if context.args:
        video_msg_id = context.args[0]
        try:
            await update.message.reply_text("⏳ আপনার ভিডিও ফাইলটি লোড হচ্ছে, দয়া করে ১ সেকেন্ড অপেক্ষা করুন...")
            
            # প্রাইভেট চ্যানেল থেকে হুবহু ফাইলটি ইউজারের ইনবক্সে সেন্ড করা (copy_message)
            await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=int(video_msg_id)
            )
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            await update.message.reply_text("❌ দুঃখিত! ফাইলটি পাওয়া যায়নি অথবা মুছে ফেলা হয়েছে।")
    else:
        await update.message.reply_text("স্বাগতম! ভিডিও দেখতে আমাদের চ্যানেলের লিংকে ক্লিক করে ৩টি অ্যাড শেষ করে আসুন।")

# /post কমান্ড (এডমিন যখন চ্যানেলে নতুন পোস্ট বানাবে)
async def create_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw_text = " ".join(context.args)
        if not raw_text or "|" not in raw_text:
            await update.message.reply_text(
                "❌ **ভুল ফরম্যাট!**\n\n"
                "সঠিক নিয়ম:\n"
                "`/post মেসেজ_আইডি | ভিডিও_টাইটেল | থাম্বনেইল_ছবি_লিঙ্ক`\n\n"
                "উদাহরণ:\n`/post 209 | নতুন গরম খবর | https://i.imgur.com/example.jpg`",
                parse_mode="Markdown"
            )
            return

        parts = [x.strip() for x in raw_text.split("|")]
        if len(parts) < 3:
            await update.message.reply_text("❌ ৩টি তথ্যই সঠিকভাবে দিন।")
            return

        msg_id, title, img_url = parts[0], parts[1], parts[2]

        encoded_v = quote(msg_id, safe='')
        encoded_t = quote(title, safe='')
        encoded_i = quote(img_url, safe='')

        # মিনি অ্যাপ লিঙ্ক
        final_mini_app_url = f"{WEB_APP_URL}?v={encoded_v}&t={encoded_t}&i={encoded_i}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Play Video 🔥", web_app=WebAppInfo(url=final_mini_app_url))]
        ])

        await update.message.reply_photo(
            photo=img_url,
            caption=f"🎬 **{title}**\n\nনিচের বাটনে ক্লিক করে পুরো ভিডিওটি দেখুন:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in create_post: {e}")
        await update.message.reply_text("❌ পোস্ট তৈরি করতে সমস্যা হয়েছে। ইনপুট চেক করুন।")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", create_post))

    logger.info("Bot is running 24/7...")
    app.run_polling()

if __name__ == '__main__':
    main()
