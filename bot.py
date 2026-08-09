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
    MessageHandler,
    filters,
    ContextTypes,
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = "8952565156:AAHubKRCMzY6D6_hLcLwvta-3M5Pd_DoF-E"
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))

BKASH_NUMBER = "01346133685"
NAGAD_NUMBER = "01346133685"

# আপনার টেলিগ্রাম ইউজারনেম
ADMIN_USERNAME = "ji0771295" 

# আপনার টেলিগ্রাম Chat ID (আপনার স্ক্রিনশট থেকে নেওয়া)
ADMIN_CHAT_ID = 8672040646

# Flask web server setup for keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running perfectly!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
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

    keyboard = [
        [InlineKeyboardButton("💬 এডমিনকে মেসেজ দিন", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    payment_text = (
        f"যেকোনো প্ল্যান চালু করতে নিচের **bKash** অথবা **Nagad** Personal নম্বরে টাকা সেন্ড মানি (Send Money) করুন:\n\n"
        f"📱 **bKash Personal:** `{BKASH_NUMBER}`\n"
        f"📱 **Nagad Personal:** `{NAGAD_NUMBER}`\n\n"
        f"টাকা পাঠানোর পর আপনার লাস্ট ৪ ডিজিট বা ট্রানজেকশন আইডি (TrxID) এখানে মেসেজ দিন।"
    )
    
    await query.message.reply_text(payment_text, parse_mode='Markdown', reply_markup=reply_markup)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_text = update.message.text
    
    user_info = f"@{user.username}" if user.username else f"Name: {user.first_name} (ID: `{user.id}`)"

    # ১. কাস্টমারকে উত্তর দেওয়া (লিংক দেওয়া হবে না)
    response_text = (
        f"✅ ধন্যবাদ! আপনার পেমেন্ট তথ্য (`{user_text}`) গ্রহণ করা হয়েছে।\n\n"
        f"এডমিন আপনার পেমেন্ট ভেরিফাই করে খুব দ্রুত আপনাকে প্রিমিয়াম চ্যানেলে যুক্ত করে দেবে।\n"
        f"তাড়াতাড়ি রেসপন্স পেতে নিচের বাটনে চাপ দিয়ে এডমিনকে মেসেজ দিন।"
    )
    keyboard = [
        [InlineKeyboardButton("💬 এডমিনকে মেসেজ দিন", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response_text, parse_mode='Markdown', reply_markup=reply_markup)

    # ২. আপনার (এডমিনের) টেলিগ্রাম ইনবক্সে নোটিফিকেশন পাঠানো
    admin_notification = (
        f"🔔 **নতুন পেমেন্ট মেসেজ এসেছে!**\n\n"
        f"👤 **কাস্টমার:** {user_info}\n"
        f"💳 **পেমেন্ট তথ্য / TrxID:** `{user_text}`\n\n"
        f"👉 বিকাশ/নগদে টাকা চেক করে কাস্টমারকে প্রাইভেট চ্যানেলের লিংক পাঠিয়ে দিন।"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notification, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(ChatJoinRequestHandler(auto_approve))

    logger.info("Bot is polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
