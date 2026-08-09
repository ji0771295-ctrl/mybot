
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

TOKEN = "8952565156:AAF7hsATyy__vnHz76g0_kcOtHj_g-IiciA"
ADMIN_ID = 8672040646
CHANNEL_ID = -1004499292164
CHANNEL_LINK = "https://t.me/+LC8kof81jN9lODg1"

BKASH_NO = "01346133685"
NAGAD_NO = "01346133685"

logging.basicConfig(level=logging.INFO)

PLANS = {
    "weekly": {"name": "Weekly Access (7 Days)", "price": 50, "days": 7},
    "monthly": {"name": "Monthly Access (30 Days)", "price": 150, "days": 30},
    "quarterly": {"name": "Quarterly Access (90 Days)", "price": 350, "days": 90},
    "chat": {"name": "Live Chat (30 Days)", "price": 550, "days": 30},
}

users_db = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("• Weekly — ৳50 (7 days)", callback_data="plan_weekly")],
        [InlineKeyboardButton("• Monthly — ৳150 (30 days)", callback_data="plan_monthly")],
        [InlineKeyboardButton("• Quarterly — ৳350 (90 days)", callback_data="plan_quarterly")],
        [InlineKeyboardButton("• Live Chat — ৳550 (30 days)", callback_data="plan_chat")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = (
        "👋 Welcome to Premium Channel Subscription Bot!\n\n"
        "আমাদের প্রাইভেট চ্যালেন ও লাইভ চ্যাটের সাবস্ক্রিপশন নিতে নিচের প্ল্যানগুলো নির্বাচন করুন:"
    )
    await update.message.reply_text(msg, reply_markup=reply_markup)

async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan_key = query.data.replace("plan_", "")
    plan = PLANS[plan_key]
    context.user_data['selected_plan'] = plan_key

    text = (
        f"আপনি নির্বাচন করেছেন: *{plan['name']}*\n"
        f"মূল্য: *৳{plan['price']}*\n\n"
        f"নিচের নম্বরে সেন্ড মানি (Send Money) করুন:\n"
        f"📱 **Bkash Personal:** `{BKASH_NO}`\n"
        f"📱 **Nagad Personal:** `{NAGAD_NO}`\n\n"
        "টাকা পাঠানোর পর বিকাশ/নগদের **TrxID** বা লাস্ট ৪ ডিজিট লিখে মেসেজ পাঠান।"
    )
    await query.message.reply_text(text, parse_mode="Markdown")

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    trx_id = update.message.text
    plan_key = context.user_data.get('selected_plan', 'monthly')
    plan = PLANS[plan_key]

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"app_{user.id}_{plan_key}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_msg = (
        f"📥 **New Payment Request!**\n\n"
        f"User: {user.full_name} (@{user.username})\n"
        f"ID: `{user.id}`\n"
        f"Plan: {plan['name']}\n"
        f"Price: ৳{plan['price']}\n"
        f"TrxID/Info: `{trx_id}`"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=reply_markup, parse_mode="Markdown")
    await update.message.reply_text("আপনার পেমেন্ট রিকোয়েস্ট পাঠানো হয়েছে। ভেরিফাই করে দ্রুত এক্সেস দেওয়া হবে।")

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action, user_id, plan_key = data[0], int(data[1]), data[2] if len(data) > 2 else None

    if action == "app":
        plan = PLANS[plan_key]
        expire_date = datetime.now() + timedelta(days=plan['days'])
        users_db[user_id] = expire_date

        context.job_queue.run_once(auto_kick_user, when=timedelta(days=plan['days']), user_id=user_id, data={"user_id": user_id})

        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ আপনার পেমেন্ট সফল হয়েছে!\n\nচ্যানেল লিংক: {CHANNEL_LINK}\n\nআপনার মেয়াদের শেষ তারিখ: {expire_date.strftime('%Y-%m-%d %H:%M')}"
        )
        await query.message.edit_text(f"✅ Approved for User `{user_id}` ({plan['name']})")
    elif action == "rej":
        await context.bot.send_message(chat_id=user_id, text="❌ আপনার পেমেন্ট রিকোয়েস্টটি বাতিল করা হয়েছে। সঠিক TrxID দিয়ে আবার চেষ্টা করুন।")
        await query.message.edit_text(f"❌ Rejected for User `{user_id}`")

async def auto_kick_user(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    user_id = job.data["user_id"]
    try:
        await context.bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        await context.bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        await context.bot.send_message(chat_id=user_id, text="⚠️ আপনার চ্যানেল সাবস্ক্রিপশনের মেয়াদ শেষ হয়েছে! আবার সাবস্ক্রাইব করতে /start লিখুন।")
    except Exception as e:
        logging.error(f"Failed to kick user {user_id}: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(plan_selected, pattern="^plan_"))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(app|rej)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment))

    print("Subscription Bot is running...")
    app.run_polling()