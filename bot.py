import os
import logging
import threading
import cv2
import requests
from urllib.parse import quote
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 1. Flask Web Server (UptimeRobot দিয়ে ২৪/৭ চালু রাখার জন্য) ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running 24/7 successfully!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

# --- 2. CONFIGURATION ---
BOT_TOKEN = "8952565156:AAHubKRCMzY6D6_hLcLwvta-3M5Pd_DoF-E"
STORAGE_CHANNEL_ID = -1004499292164
MAIN_CHANNEL_USERNAME = "@MYxxxxx9"                         # আপনার মূল চ্যানেলের ইউজারনেম
BOT_USERNAME = "MySongPremium2026Bot"                       # আপনার বটের ইউজারনেম
WEB_APP_URL = "https://ji0771295-ctrl.github.io/mybot"     # আপনার গিটহাব পেজের ওয়েবলিংক
IMGBB_API_KEY = "YOUR_IMGBB_API_KEY"                       # ImgBB API Key (অপশনাল)

# --- 3. COMMAND HANDLERS ---

# /start হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if context.args:
        video_msg_id = context.args[0]
        try:
            await update.message.reply_text("⏳ আপনার ভিডিও ফাইলটি পাঠানো হচ্ছে, ১ সেকেন্ড অপেক্ষা করুন...")
            
            # প্রাইভেট স্টোরেজ চ্যানেল থেকে ফাইল ইউজারের ইনবক্সে কপি পাঠাবে
            await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=int(video_msg_id)
            )
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            await update.message.reply_text("❌ দুঃখিত! ফাইলটি পাওয়া যায়নি অথবা প্রাইভেট চ্যানেল থেকে মুছে ফেলা হয়েছে।")
    else:
        await update.message.reply_text("স্বাগতম! আমাদের ভিডিও পেতে চ্যানেলের মিনি অ্যাপ লিংকে ক্লিক করুন।")

# /post ম্যানুয়াল কমান্ড
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

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Play Video 🔥", url=final_mini_app_url)]
        ])

        # পাবলিক চ্যানেলে পোস্ট পাঠানো
        await context.bot.send_photo(
            chat_id=MAIN_CHANNEL_USERNAME,
            photo=img_url,
            caption=f"🎬 **{title}**\n\nনিচের বাটনে ক্লিক করে পুরো ভিডিওটি দেখুন:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        await update.message.reply_text(
            f"✅ পোস্টটি সফলভাবে **{MAIN_CHANNEL_USERNAME}** চ্যানেলে পোস্ট করা হয়েছে!",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in create_post: {e}")
        await update.message.reply_text(f"❌ পোস্ট তৈরি করতে সমস্যা হয়েছে: `{str(e)}`", parse_mode="Markdown")

# --- 4. AUTO VIDEO HANDLER ---
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.video and not msg.document:
        return

    status_msg = await msg.reply_text("⏳ ভিডিও প্রসেসিং হচ্ছে... অনুগ্রহ করে অপেক্ষা করুন।")
    
    try:
        # ১. স্টোরেজ চ্যানেলে ফাইল পাঠানো
        stored_msg = await context.bot.copy_message(
            chat_id=STORAGE_CHANNEL_ID,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id
        )
        video_msg_id = str(stored_msg.message_id)

        file_id = msg.video.file_id if msg.video else msg.document.file_id

        # ২. ভিডিও ডাউনলোড ও ১ সেকেণ্ডের ফ্রেম থেকে থাম্বনেইল কাটা
        video_file = await context.bot.get_file(file_id)
        video_path = f"video_{msg.message_id}.mp4"
        await video_file.download_to_drive(video_path)

        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_MSEC, 1000)
        success, image = cap.read()
        img_path = f"thumb_{msg.message_id}.jpg"

        if success:
            cv2.imwrite(img_path, image)
        cap.release()

        # ৩. ইমেজ ব্যাকআপ ইউআরএল
        img_url = "https://i.postimg.cc/bvg5CYpW/IMG-20260814-013409-080.png" 
        
        if os.path.exists(img_path) and IMGBB_API_KEY != "YOUR_IMGBB_API_KEY":
            try:
                with open(img_path, "rb") as file:
                    response = requests.post(
                        "https://api.imgbb.com/1/upload",
                        data={"key": IMGBB_API_KEY},
                        files={"image": file}
                    )
                    res_data = response.json()
                    if res_data.get("success"):
                        img_url = res_data["data"]["url"]
            except Exception as upload_err:
                logger.error(f"Image upload failed: {upload_err}")

        # মেমোরি ফাঁকা করা
        if os.path.exists(video_path): os.remove(video_path)
        if os.path.exists(img_path): os.remove(img_path)

        # ৪. টাইটেল ও মিনি অ্যাপ লিঙ্ক তৈরি
        title = msg.caption or "নতুন এক্সক্লুসিভ মিউজিক ভিডিও 🎵"
        
        encoded_v = quote(video_msg_id, safe='')
        encoded_t = quote(title, safe='')
        encoded_i = quote(img_url, safe='')

        mini_app_link = f"{WEB_APP_URL}?v={encoded_v}&t={encoded_t}&i={encoded_i}"

        # ৫. রেসপন্স
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Mini App Link Test", url=mini_app_link)]
        ])

        reply_text = (
            f"✅ **ভিডিও প্রসেস সফল হয়েছে!**\n\n"
            f"📌 **স্টোরেজ আইডি:** `{video_msg_id}`\n"
            f"📝 **টাইটেল:** {title}\n"
            f"🖼 **থাম্বনেইল:** [Image Link]({img_url})\n\n"
            f"👉 **পাবলিক চ্যানেলে পোস্ট করতে নিচের লাইনটি কপি করে বোটকে সেন্ড করুন:**\n"
            f"`/post {video_msg_id} | {title} | {img_url}`"
        )

        await status_msg.edit_text(reply_text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await status_msg.edit_text(f"❌ ভিডিও প্রসেস করতে সমস্যা হয়েছে: `{str(e)}`", parse_mode="Markdown")

# --- 5. MAIN FUNCTION ---
def main():
    # ফ্লাস্ক ব্যাকগ্রাউন্ড সার্ভার চালু করা (২৪/৭ আপটাইমের জন্য)
    threading.Thread(target=run_flask, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", create_post))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_video))

    logger.info("Bot started successfully...")
    app.run_polling()

if __name__ == '__main__':
    main()
