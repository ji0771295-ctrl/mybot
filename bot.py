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

BKASH_NUMBER = "01346133685"
NAGAD_NUMBER = "01346133685"

# আপনার টেলিগ্রাম ইউজারনেম
ADMIN_USERNAME = "ji0771295" 

# আপনার টেলিগ্রাম Chat ID
ADMIN_CHAT_ID = 8672040646

# প্রিমিয়াম চ্যানেলের লিংক
PREMIUM_CHANNEL_LINK = "https://t.me/+LC8kof81jN9lODg1"

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
        [InlineKeyboardButton("• Weekly — ৳50 (7 days)", callback_data='plan_weekly')],
        [InlineKeyboardButton("• Monthly — ৳150 (30 days)", callback_data='plan_monthly')],
        [InlineKeyboardButton("• Quarterly — ৳350 (90 days)", callback_data='plan_quarterly')],
        [InlineKeyboardButton("• Live Chat — ৳550 (30 days)", callback_data='plan_livechat')],
        [InlineKeyboardButton("• ভিডিও কলে মেয়েদের সাথে কথা বলতে চাইলে — ৳550", callback_data='plan_videocall')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "আমাদের প্রাইভেট চ্যানেল ও লাইভ চ্যাটের সাবস্ক্রিপশন নিতে নিচের প্ল্যানগুলো নির্বাচন করুন:"
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith('plan_'):
        plan_name = query.data.replace('plan_', '').capitalize()
        context.user_data['selected_plan'] = plan_name

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

    elif query.data.startswith('approve_'):
        user_id = int(query.data.split('_')[1])
        
        # কাস্টমারকে জয়েন লিংক পাঠানো
        success_text = (
            f"🎉 **আপনার পেমেন্ট ভেরিফাই হয়েছে!**\n\n"
            f"নিচের '🚀 প্রিমিয়াম চ্যানেলে জয়েন করুন' বাটনে চাপ দিয়ে এখনই আমাদের প্রাইভেট চ্যানেলে যুক্ত হয়ে যান:"
        )
        keyboard = [
            [InlineKeyboardButton("🚀 প্রিমিয়াম চ্যানেলে জয়েন করুন", url=PREMIUM_CHANNEL_LINK)],
            [InlineKeyboardButton("💬 যেকোনো প্রয়োজনে এডমিন", url=f"https://t.me/{ADMIN_USERNAME}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(chat_id=user_id, text=success_text, parse_mode='Markdown', reply_markup=reply_markup)
            await query.edit_message_text(text=f"✅ **Approved for User `{user_id}`**", parse_mode='Markdown')
        except Exception as e:
            await query.message.reply_text(f"❌ এরর: মেসেজ পাঠানো যায়নি ({e})")

    elif query.data.startswith('reject_'):
        user_id = int(query.data.split('_')[1])
        
        # কাস্টমারকে রিজেক্ট মেসেজ পাঠানো
        reject_text = (
            f"❌ **আপনার পেমেন্ট রিকোয়েস্টটি বাতিল করা হয়েছে।**\n\n"
            f"সঠিক TrxID/লাস্ট ৪ ডিজিট দিয়ে আবার চেষ্টা করুন অথবা এডমিনের সাথে যোগাযোগ করুন।"
        )
        keyboard = [
            [InlineKeyboardButton("💬 এডমিনকে মেসেজ দিন", url=f"https://t.me/{ADMIN_USERNAME}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await context.bot.send_message(chat_id=user_id, text=reject_text, parse_mode='Markdown', reply_markup=reply_markup)
            await query.edit_message_text(text=f"❌ **Rejected for User `{user_id}`**", parse_mode='Markdown')
        except Exception as e:
            await query.message.reply_text(f"❌ এরর: মেসেজ পাঠানো যায়নি ({e})")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_text = update.message.text
    selected_plan = context.user_data.get('selected_plan', 'General')
    
    user_info = f"@{user.username}" if user.username else f"None"

    # ১. কাস্টমারকে মেসেজ পাঠানো
    response_text = (
        f"✅ ধন্যবাদ! আপনার পেমেন্ট রিকোয়েস্ট পাঠানো হয়েছে।\n\n"
        f"এডমিন চেক করে এপ্রুভ করলে অটোমেটিক আপনার কাছে চ্যানেল লিংক চলে আসবে।"
    )
    keyboard = [
        [InlineKeyboardButton("💬 এডমিনকে মেসেজ দিন", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response_text, reply_markup=reply_markup)

    # ২. এডমিনের কাছে Approve & Reject বাটনসহ নোটিফিকেশন পাঠানো
    admin_notification = (
        f"📥 **New Payment Request!**\n\n"
        f"**User:** {user.first_name} (@{user_info})\n"
        f"**ID:** `{user.id}`\n"
        f"**Plan:** {selected_plan}\n"
        f"**TrxID/Info:** {user_text}"
    )
    
    admin_keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
        ]
    ]
    admin_reply_markup = InlineKeyboardMarkup(admin_keyboard)

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID, 
            text=admin_notification, 
            parse_mode='Markdown', 
            reply_markup=admin_reply_markup
        )
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
