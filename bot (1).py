import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ChatJoinRequestHandler,
    ContextTypes,
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8952565156:AAHkscHOeRFhwZqlyqYRLvBw7qyKSB-YrC0")
# আপনার প্রাইভেট চ্যানেলের আইডি (উদাহরণ: -100xxxxxxxxxx)
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002233445566")) 

# --- FLASK WEB SERVER (for UptimeRobot / Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is active and running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "স্বাগতম! চ্যানেল জয়েন রিকোয়েস্ট পাঠালে এই বট স্বয়ংক্রিয়ভাবে তা এক্সেপ্ট করবে।"
    )

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    user_id = request.from_user.id
    chat_id = request.chat.id

    try:
        # ১. জয়েন রিকোয়েস্ট এক্সেপ্ট করা
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
        
        # ২. ওয়ান-টাইম ইনভাইট লিংক তৈরি করা
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=chat_id,
            member_limit=1
        )
        
        # ৩. ইউজারকে প্রাইভেটে মেসেজ দিয়ে লিংক পাঠানো
        await context.bot.send_message(
            chat_id=user_id,
            text=f"আপনার জয়েন রিকোয়েস্ট এক্সেপ্ট করা হয়েছে! 🎉\n\nচ্যানেলে প্রবেশ করতে নিচের লিংকে ক্লিক করুন:\n{invite_link.invite_link}"
        )
        logger.info(f"Approved and sent link to user {user_id}")
    except Exception as e:
        logger.error(f"Error handling join request: {e}")

def main():
    # Flask Web Server ব্যাকগ্রাউন্ডে চালু করা
    threading.Thread(target=run_web, daemon=True).start()

    # Application তৈরি ও স্টার্ট করা
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(ChatJoinRequestHandler(handle_join_request))

    # Bot Polling
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
