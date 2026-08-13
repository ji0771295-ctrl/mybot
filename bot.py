import os
import logging
import threading
from urllib.parse import quote
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Flask Web Server (২৪ ঘণ্টা চালু রাখার জন্য) ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION (আপনার দেয়া তথ্য অনুযায়ী) ---
BOT_TOKEN = "8952565156:AAHubKRCMzY6D6_hLcLwvta-3M5Pd_DoF-E"
ADMIN_ID = 8672040646
PREMIUM_CHANNEL_ID = -1004499292164
WEB_APP_URL = "https://ji0771295-ctrl.github.io/mybot"  

# /start কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("স্বাগতম! ভিডিও দেখতে বা কনটেন্ট আনলক করতে সাথে থাকুন।")

# /post কমান্ড - নতুন ভিডিও পোস্ট তৈরি করার জন্য
async def create_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw_text = " ".join(context.args)
        if not raw_text or "|" not in raw_text:
            await update.message.reply_text(
                "❌ **ভুল ফরম্যাট!**\n\n"
                "সঠিক নিয়ম:\n"
                "`/post ভিডিও_লিঙ্ক | টাইটেল | থাম্বনেইল_ছবি_লিঙ্ক`",
                parse_mode="Markdown"
            )
            return

        parts = [x.strip() for x in raw_text.split("|")]
        if len(parts) < 3:
            await update.message.reply_text("❌ সব তথ্য সঠিকভাবে দিন (ভিডিও লিঙ্ক, টাইটেল, ছবি লিঙ্ক)।")
            return

        v_url, title, img_url = parts[0], parts[1], parts[2]

        # URL Encoding
        encoded_v = quote(v_url, safe='')
        encoded_t = quote(title, safe='')
        encoded_i = quote(img_url, safe='')

        final_mini_app_url = f"{WEB_APP_URL}?v={encoded_v}&t={encoded_t}&i={encoded_i}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 UNLOCK & WATCH VIDEO 🔥", web_app=WebAppInfo(url=final_mini_app_url))]
        ])

        await update.message.reply_text(
            f"🎬 **{title}**\n\nনিচের বাটনে ক্লিক করে ৩টি অ্যাড দেখে ভিডিওটি আনলক করুন:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in create_post: {e}")
        await update.message.reply_text("একটি সমস্যা হয়েছে। পোস্টের ফরম্যাটটি চেক করুন।")

def main():
    # Flask ওয়েব সার্ভার ব্যাকগ্রাউন্ডে চালু করা
    threading.Thread(target=run_flask, daemon=True).start()

    # Bot Application তৈরি
    app = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", create_post))

    logger.info("Bot is running 24/7...")
    app.run_polling()

if __name__ == '__main__':
    main()
