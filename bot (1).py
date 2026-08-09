import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)

# Render Web Service Health Checker
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is live!")

    def log_message(self, format, *args):
        return

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# Bot Configuration
TOKEN = TOKEN = "8952565156:AAF7hsATyy__vnHz76g0_kcOtHj_g-IiciA"
ADMIN_ID = 8672040646
CHANNEL_ID = -1004499292164

BKASH_NO = "01346133685"
NAGAD_NO = "01346133685"

logging.basicConfig(level=logging.INFO)

PLANS = {
    "weekly": {"name": "Weekly Access (7 Days)", "price": 50},
    "monthly": {"name": "Monthly Access (30 Days)", "price": 150},
    "quarterly": {"name": "Quarterly Access (90 Days)", "price": 350},
    "chat": {"name": "Live Chat (30 Days)", "price": 550}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("• Weekly — ৳50 (7 days)", callback_data="plan_weekly")],
        [InlineKeyboardButton("• Monthly — ৳150 (30 days)", callback_data="plan_monthly")],
        [InlineKeyboardButton("• Quarterly — ৳350 (90 days)", callback_data="plan_quarterly")],
        [InlineKeyboardButton("• Live Chat — ৳550 (30 days)", callback_data="plan_chat")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "আমাদের প্রাইভেট চ্যানেল ও লাইভ চ্যাটের সাবস্ক্রিপশন নিতে নিচের প্ল্যানগুলো নির্বাচন করুন:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("plan_"):
        plan_key = data.split("_")[1]
        plan = PLANS[plan_key]
        context.user_data['selected_plan'] = plan_key

        msg = (
            f"আপনি নির্বাচন করেছেন: {plan['name']}\n"
            f"মূল্য: ৳{plan['price']}\n\n"
            f"নিচের নম্বরে সেন্ড মানি (Send Money) করুন:\n"
            f"📱 Bkash Personal: {BKASH_NO}\n"
            f"📱 Nagad Personal: {NAGAD_NO}\n\n"
            f"টাকা পাঠানোর পর বিকাশ/নগদের TrxID বা লাস্ট ৪ ডিজিট লিখে মেসেজ পাঠান।"
        )
        await query.edit_message_text(msg)

    elif data.startswith("approve_"):
        target_user_id = int(data.split("_")[1])
        try:
            # private channel invite link generate
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                member_limit=1
            )
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ আপনার পেমেন্ট ভেরিফাই হয়েছে!\n\nপ্রাইভেট চ্যানেলে যুক্ত হওয়ার লিংক:\n{invite_link.invite_link}"
            )
            await query.edit_message_text(f"✅ Approved for User `{target_user_id}`", parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {e}\n(চ্যানেলে বটকে Admin বানিয়েছেন কি?)")

    elif data.startswith("reject_"):
        target_user_id = int(data.split("_")[1])
        await context.bot.send_message(
            chat_id=target_user_id,
            text="❌ আপনার পেমেন্ট রিকোয়েস্টটি বাতিল করা হয়েছে। সঠিক TrxID দিয়ে আবার চেষ্টা করুন।"
        )
        await query.edit_message_text(f"❌ Rejected for User `{target_user_id}`", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text

    if update.message.chat.type != 'private':
        return

    plan_key = context.user_data.get('selected_plan', 'weekly')
    plan = PLANS.get(plan_key, PLANS['weekly'])

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_msg = (
        f"📥 New Payment Request!\n\n"
        f"User: {user.full_name} (@{user.username})\n"
        f"ID: {user.id}\n"
        f"Plan: {plan['name']}\n"
        f"Price: ৳{plan['price']}\n"
        f"TrxID/Info: {text}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=reply_markup)
    await update.message.reply_text("আপনার পেমেন্ট রিকোয়েস্ট পাঠানো হয়েছে। ভেরিফাই করে দ্রুত অ্যাক্সেস দেওয়া হবে।")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
