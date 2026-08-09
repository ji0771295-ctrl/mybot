import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ChatJoinRequestHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))

BKASH_NUMBER = "01346133685"
NAGAD_NUMBER = "01346133685"

# Flask web server setup for keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- TELEGRAM BOT HANDLERS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("• Weekly — ৳50 (7 days)", callback_data='plan_weekly_50')],
        [InlineKeyboardButton("• Monthly — ৳150 (30 days)", callback_data='plan_monthly_150')],
        [InlineKeyboardButton("• Quarterly — ৳350 (90 days)", callback_data='plan_quarterly_350')],
        [InlineKeyboardButton("• Live Chat — ৳550 (30 days)", callback_data='plan_livechat_550')],
        [InlineKeyboardButton("• ভিডিও কলে মেয়েদের সাথে কথা বলতে চাইলে — ৳550", callback_data='plan_videocall_550')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "আমাদের প্রাইভেট চ্যানেল ও লাইভ চ্যাটের সাবস্ক্রিপশন নিতে নিচের প্ল্যানগুলো নির্বাচন করুন:"
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    payment_text = (
        f"যেকোনো প্ল্যান চালু করতে নিচের **bKash** অথবা **Nagad** Personal নম্বরে টাকা সেন্ড মানি (Send Money) করুন:\n\n"
        f"📱 **bKash Personal:** `{BKASH_NUMBER}`\n"
        f"📱 **Nagad Personal:** `{NAGAD_NUMBER}`\n\n"
        f"টাকা পাঠানোর পর আপনার লাস্ট ৪ ডিজিট বা ট্রানজেকশন আইডি (TrxID) আমাদের এডমিনকে মেসেজ দিন।"
    )
    
    await query.message.reply_text(payment_text, parse_mode='Markdown')

async def auto_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_join_request = update.chat_join_request
        user_id = chat_join_request.from_user.id
        chat_id = chat_join_request.chat.id

        await context.bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )
        logger.info(f"Approved join request for user {user_id} in chat {chat_id}")
    except Exception as e:
        logger.error(f"Error approving request: {e}")

def main():
    if not BOT_TOKEN:
        logger.error("No BOT_TOKEN provided!")
        return

    threading.Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(ChatJoinRequestHandler(auto_approve))

    logger.info("Bot is polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
