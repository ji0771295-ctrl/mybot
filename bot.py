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
BOT_USERNAME = "MySongPremium2026Bot"  # আপনার বটের ইউজারনেম

# /start হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if context.args:
        video_id = context.args[0]
        
        # ইউজারের জন্য ১-ক্লিকে মিনি অ্যাপ ওপেন করার বাটন (পপ-আপ ছাড়া)
        final_mini_app_url = f"{WEB_APP_URL}?v={video_id}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 এখনই ভিডিও দেখুন (Play Video)", web_app=WebAppInfo(url=final_mini_app_url))]
        ])
        
        await update.message.reply_text(
            "👇 **ভিডিওটি প্লে করতে নিচের বাটনে চাপ দিন:**",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("স্বাগতম! ভিডিও দেখতে চ্যানেলের পোস্টে থাকা লিংকে ক্লিক করুন।")

# /post কমান্ড (পাবলিক চ্যানেলে t.me বটের লিংক পাঠাবে)
async def create_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw_text = " ".join(context.args)
        if not raw_text or "|" not in raw_text:
            await update.message.reply_text(
                "❌ **ভুল ফরম্যাট!**\n\n"
                "সঠিক নিয়ম:\n"
                "`/post ভিডিও_আইডি | টাইটেল | থাম্বনেইল_ছবি_লিঙ্ক`",
                parse_mode="Markdown"
            )
            return

        parts = [x.strip() for x in raw_text.split("|")]
        if len(parts) < 3:
            await update.message.reply_text("❌ সব তথ্য সঠিকভাবে দিন।")
            return

        msg_id, title, img_url = parts[0], parts[1], parts[2]

        # চ্যানেলে পপ-আপ না আসার জন্য বটের t.me লিংক ব্যবহার করা হয়েছে
        bot_deep_link = f"https://t.me/{BOT_USERNAME}?start={msg_id}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Play Video 🔥", url=bot_deep_link)]
        ])

        # সরাসরি পাবলিক চ্যানেলে পোস্ট পাঠানো
        await context.bot.send_photo(
            chat_id=MAIN_CHANNEL_USERNAME,
            photo=img_url,
            caption=f"🎬 **{title}**\n\nনিচের বাটনে ক্লিক করে ভিডিওটি দেখুন:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        await update.message.reply_text(
            f"✅ পোস্টটি সফলভাবে **{MAIN_CHANNEL_USERNAME}** চ্যানেলে পপ-আপ মুক্ত বাটনসহ পোস্ট করা হয়েছে!",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in create_post: {e}")
        await update.message.reply_text(f"❌ সমস্যা হয়েছে: `{str(e)}`", parse_mode="Markdown")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", create_post))

    logger.info("Bot is running 24/7...")
    app.run_polling()

if __name__ == '__main__':
    main()
