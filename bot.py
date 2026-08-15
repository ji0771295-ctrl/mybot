import base64
import json
import logging
import os
import sqlite3
import threading
from urllib.parse import quote
from flask import Flask, jsonify, request
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = '8952565156:AAHubKRCMzY6D6_hLcLwvta-3M5Pd_DoF-E'
STORAGE_CHANNEL_ID = -1004499292164
MAIN_CHANNEL_USERNAME = '@MYxxxxx9'  # আপনার মূল চ্যানেলের ইউজারনেম
BOT_USERNAME = 'MySongPremium2026Bot'  # আপনার বটের ইউজারনেম
WEB_APP_URL = 'https://ji0771295-ctrl.github.io/mybot'  # আপনার গিটহাব পেজের ওয়েবলিংক
ADMIN_ID = 8672040646  # আপনার পার্সোনাল টেলিগ্রাম আইডি

# --- 1. SQLite Database Setup (Users & Unlocked Videos) ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # ইউজার টেবিল (কয়েন এবং রেফার কাউন্ট ট্র্যাক করার জন্য)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0
        )
    ''')
    # আনলক করা ভিডিও টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unlocked_videos (
            user_id INTEGER,
            video_id TEXT,
            PRIMARY KEY (user_id, video_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 2. JSON Database Persistence (Videos Database) ---
DB_FILE = "videos_db.json"
videos_db = []

def load_videos():
    global videos_db
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                videos_db = json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON DB: {e}")
            videos_db = []

def save_video_entry(v_id, title, img_url):
    global videos_db
    entry = {
        "id": str(v_id),
        "title": title,
        "thumb": img_url,
        "category": "vip",
        "isNew": True,
        "timeAgo": "এখনই যুক্ত হয়েছে",
        "todayViews": "১,২০০ জন আজকে দেখেছে 🔥"
    }
    # ডুপ্লিকেট চেক
    for v in videos_db:
        if v['id'] == str(v_id):
            v['title'] = title
            v['thumb'] = img_url
            _write_to_db()
            return
            
    videos_db.insert(0, entry)
    _write_to_db()

def _write_to_db():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(videos_db, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error writing to JSON DB: {e}")

load_videos()

# --- 3. Flask Web Server ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return 'Bot & Security Backend is running 24/7 successfully!'

# 🌟 মিনি অ্যাপের জন্য ডাইনামিক ভিডিও API
@flask_app.route('/api/videos', methods=['GET'])
def get_videos():
    response = jsonify(videos_db)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# 🌟 সার্ভার সাইড ভিডিও আনলক ও কয়েন যাচাইকরণ এপিআই (চালাকি রোধ করতে)
@flask_app.route('/api/unlock', methods=['POST'])
def unlock_video():
    data = request.json
    user_id = data.get('user_id')
    video_id = data.get('video_id')
    
    if not user_id or not video_id:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # চেক করুন ভিডিওটি ইতিমধ্যে আনলক করা আছে কি না
    cursor.execute("SELECT * FROM unlocked_videos WHERE user_id = ? AND video_id = ?", (user_id, video_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({"status": "success", "message": "Already unlocked"})

    # ইউজারের কয়েন ব্যালেন্স চেক করা
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    coins = user[0] if user else 0
    
    if coins > 0:
        # ১টি কয়েন কেটে নেওয়া এবং ভিডিও আনলক লিস্টে যুক্ত করা
        cursor.execute("UPDATE users SET coins = coins - 1 WHERE user_id = ?", (user_id,))
        cursor.execute("INSERT OR IGNORE INTO unlocked_videos (user_id, video_id) VALUES (?, ?)", (user_id, video_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Unlocked successfully"})
    else:
        conn.close()
        return jsonify({"status": "fail", "message": "Insufficient coins"})

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)

# Helper function: Decode Safe Base64 Text
def decode_base64_text(encoded_str):
    try:
        padding = (
            '=' * (4 - len(encoded_str) % 4) if len(encoded_str) % 4 != 0 else ''
        )
        clean_str = encoded_str.replace('-', '+').replace('_', '/') + padding
        decoded_bytes = base64.b64decode(clean_str)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f'Base64 decode error: {e}')
        return 'রিকোয়েস্ট বোঝা যায়নি'

# --- 4. COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    # প্রতিবার স্টার্ট করলে ইউজারকে ডাটাবেজে রেজিস্টার করা (যদি না থাকে)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, coins, referrals) VALUES (?, 0, 0)", (chat_id,))
    conn.commit()
    conn.close()

    if context.args:
        arg = context.args[0]

        # 🌟 রেফারেল লজিক (যেমন: /start ref_123456)
        if arg.startswith('ref_'):
            try:
                referrer_id = int(arg.split('_')[1])
                if referrer_id != chat_id:  # নিজের লিঙ্কে নিজে ক্লিক রোধ করতে
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR IGNORE INTO users (user_id, coins, referrals) VALUES (?, 0, 0)", (referrer_id,))
                    cursor.execute("UPDATE users SET coins = coins + 1, referrals = referrals + 1 WHERE user_id = ?", (referrer_id,))
                    conn.commit()
                    conn.close()
            except Exception as e:
                logger.error(f"Referral processing error: {e}")
            
            await update.message.reply_text(
                "✅ **স্বাগতম!** আপনি সফলভাবে রেফারেল লিংকের মাধ্যমে যুক্ত হয়েছেন।",
                parse_mode='Markdown'
            )
            return

        elif arg.startswith('coin_'):
            parts = arg.split('_')
            if len(parts) >= 3:
                amount = parts[1]
                trx_id = '_'.join(parts[2:])

                await update.message.reply_text(
                    f'✅ **আপনার কয়েন কেনার আবেদনটি জমা হয়েছে!**\n\n'
                    f'💰 **পরিমাণ:** {amount} টাকা\n'
                    f'🧾 **TrxID:** `{trx_id}`\n\n'
                    f'এডমিন ভেরিফাই করে দ্রুত আপনার অ্যাকাউন্টে কয়েন যোগ করে দেবে। ধন্যবাদ!',
                    parse_mode='Markdown',
                )

                if ADMIN_ID != 0:
                    try:
                        admin_msg = (
                            f'💳 **নতুন কয়েন রিচার্জ রিকোয়েস্ট!**\n\n'
                            f'👤 **ইউজার:** {user.full_name} (@{user.username or "No Username"})\n'
                            f'🆔 **আইডি:** `{chat_id}`\n'
                            f'💵 **টাকা:** {amount} BDT\n'
                            f'🧾 **TrxID:** `{trx_id}`'
                        )
                        await context.bot.send_message(
                            chat_id=ADMIN_ID, text=admin_msg, parse_mode='Markdown'
                        )
                    except Exception as admin_err:
                        logger.error(f'Error notifying admin for coin request: {admin_err}')
            return

        elif arg.startswith('req_'):
            raw_payload = arg.replace('req_', '')
            user_request = decode_base64_text(raw_payload)

            await update.message.reply_text(
                f'✅ **আপনার রিকোয়েস্টটি এডমিনের কাছে পাঠানো হয়েছে!**\n\n'
                f'📝 **মেসেজ:** `{user_request}`\n\n'
                f'খুব শীঘ্রই আপনার পছন্দের কন্টেন্ট যুক্ত করা হবে। ধন্যবাদ!',
                parse_mode='Markdown',
            )

            if ADMIN_ID != 0:
                try:
                    admin_msg = (
                        f'📥 **নতুন ভিডিও রিকোয়েস্ট!**\n\n'
                        f'👤 **ইউজার:** {user.full_name} (@{user.username or "No Username"})\n'
                        f'🆔 **আইডি:** `{chat_id}`\n'
                        f'📝 **মেসেজ:** {user_request}'
                    )
                    await context.bot.send_message(
                        chat_id=ADMIN_ID, text=admin_msg, parse_mode='Markdown'
                    )
                except Exception as admin_err:
                    logger.error(f'Error sending to admin: {admin_err}')
            return

        else:
            video_msg_id = arg
            try:
                await update.message.reply_text(
                    '⏳ আপনার ভিডিও ফাইলটি পাঠানো হচ্ছে, ১ সেকেন্ড অপেক্ষা করুন...'
                )
                await context.bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=STORAGE_CHANNEL_ID,
                    message_id=int(video_msg_id),
                )
            except Exception as e:
                logger.error(f'Error sending video: {e}')
                await update.message.reply_text(
                    '❌ দুঃখিত, ভিডিওটি পাওয়া যায়নি বা স্টোরেজ চ্যানেল থেকে মুছে ফেলা হয়েছে।'
                )
    else:
        # নতুন যোগ করা চ্যানেল লিংক এবং মিনি অ্যাপ বাটন সহ আপডেট করা কিবোর্ড
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton('📢 প্রথমে আমাদের পাবলিক চ্যানেলে জয়েন করুন', url='https://t.me/MYxxxxx9')],
            [InlineKeyboardButton('🎬 Netflix Zone মিনি অ্যাপ খুলুন', web_app=WebAppInfo(url=WEB_APP_URL))]
        ])
        
        welcome_text = (
            f"👋 স্বাগতম! আমাদের বটের মাধ্যমে আপনি এক্সক্লুসিভ সব ভিডিও দেখতে পারবেন।\n\n"
            f"⚠️ ভিডিও ও আপডেট পেতে প্রথমে আমাদের **পাবলিক চ্যানেলে** জয়েন করুন, তারপর মিনি অ্যাপে প্রবেশ করুন।"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode='Markdown',
        )

async def create_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw_text = ' '.join(context.args)
        if not raw_text or '|' not in raw_text:
            await update.message.reply_text(
                '❌ **ভুল ফরম্যাট!**\n\n'
                'সঠিক নিয়ম:\n'
                '`/post ভিডিও_আইডি | টাইটেল | থাম্বনেইল_ছবি_লিঙ্ক`',
                parse_mode='Markdown',
            )
            return

        parts = [x.strip() for x in raw_text.split('|')]
        if len(parts) < 3:
            await update.message.reply_text('❌ সব তথ্য সঠিকভাবে দিন।')
            return

        msg_id, title, img_url = parts[0], parts[1], parts[2]

        # মিনি অ্যাপের ডেটাবেজে সেভ করা হলো
        save_video_entry(msg_id, title, img_url)

        encoded_v = quote(msg_id, safe='')
        encoded_t = quote(title, safe='')
        encoded_i = quote(img_url, safe='')

        final_mini_app_url = (
            f'https://t.me/{BOT_USERNAME}/viralvideos?v={encoded_v}&t={encoded_t}&img={encoded_i}'
        )

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                '🎬 Watch Video (Mini App) 🎬', url=final_mini_app_url
            )
        ]])

        await context.bot.send_photo(
            chat_id=MAIN_CHANNEL_USERNAME,
            photo=img_url,
            caption=(
                f'🎬 **{title}**\n\nনিচের বাটনে চাপ দিয়ে সরাসরি ভিডিওটি দেখুন:'
            ),
            reply_markup=keyboard,
            parse_mode='Markdown',
        )

        await update.message.reply_text(
            f'✅ পোস্টটি সফলভাবে **{MAIN_CHANNEL_USERNAME}** চ্যানেলে পোস্ট করা হয়েছে এবং মিনি অ্যাপ ডেটাবেজে যুক্ত হয়েছে!',
            parse_mode='Markdown',
        )
    except Exception as e:
        logger.error(f'Error in create_post: {e}')
        await update.message.reply_text(
            f'❌ পোস্ট তৈরি করতে সমস্যা হয়েছে: `{str(e)}`', parse_mode='Markdown'
        )

# --- 5. AUTO VIDEO HANDLER ---
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.video and not msg.document:
        return

    status_msg = await msg.reply_text(
        '⏳ ভিডিও স্টোরেজে পাঠানো ও প্রসেসিং হচ্ছে...'
    )

    try:
        stored_msg = await context.bot.copy_message(
            chat_id=STORAGE_CHANNEL_ID,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
        )
        video_msg_id = str(stored_msg.message_id)

        img_url = 'https://i.postimg.cc/bvg5CYpW/IMG-20260814-013409-080.png'
        thumb_obj = None

        if msg.video and msg.video.thumbnail:
            thumb_obj = msg.video.thumbnail
        elif msg.document and msg.document.thumbnail:
            thumb_obj = msg.document.thumbnail

        if thumb_obj:
            thumb_file = await context.bot.get_file(thumb_obj.file_id)
            thumb_path = f'thumb_{msg.message_id}.jpg'
            await thumb_file.download_to_drive(thumb_path)

            try:
                with open(thumb_path, 'rb') as f:
                    response = requests.post(
                        'https://catbox.moe/user/api.php',
                        data={'reqtype': 'fileupload'},
                        files={'fileToUpload': f},
                    )
                    if response.status_code == 200 and response.text.startswith('http'):
                        img_url = response.text.strip()
            except Exception as upload_err:
                logger.error(f'Image upload failed: {upload_err}')

            if os.path.exists(thumb_path):
                os.remove(thumb_path)

        title = msg.caption or 'নতুন এক্সক্লুসিভ মিউজিক ভিডিও 🎵'

        # মিনি অ্যাপের ডেটাবেজে অটো সেভ করা হলো
        save_video_entry(video_msg_id, title, img_url)

        encoded_v = quote(video_msg_id, safe='')
        encoded_t = quote(title, safe='')
        encoded_i = quote(img_url, safe='')

        mini_app_link = (
            f'{WEB_APP_URL}?v={encoded_v}&t={encoded_t}&img={encoded_i}'
        )

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton('🎬 Open Mini App Test', web_app=WebAppInfo(url=mini_app_link))
        ]])

        reply_text = (
            f'✅ **ভিডিও প্রসেস সফল হয়েছে!**\n\n'
            f'📌 **স্টোরেজ আইডি:** `{video_msg_id}`\n'
            f'📝 **টাইটেল:** {title}\n'
            f'🖼 **থাম্বনেইল:** [Image Link]({img_url})\n\n'
            f'👉 **পাবলিক চ্যানেলে পোস্ট করতে নিচের লাইনটি কপি করে বোটকে সেন্ড করুন:**\n'
            f'`/post {video_msg_id} | {title} | {img_url}`'
        )

        await status_msg.edit_text(
            reply_text, parse_mode='Markdown', reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f'Error processing video: {e}')
        await status_msg.edit_text(
            f'❌ ভিডিও প্রসেস করতে সমস্যা হয়েছে: `{str(e)}`', parse_mode='Markdown'
        )

# --- 6. MAIN FUNCTION ---
def main():
    # ব্যাকগ্রাউন্ডে Flask সার্ভার রান করানো
    threading.Thread(target=run_flask, daemon=True).start()

    # টেলিগ্রাম বট ইনিশিয়ালাইজেশন
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('post', create_post))
    app.add_handler(
        MessageHandler(filters.VIDEO | filters.Document.ALL, handle_video)
    )

    logger.info('Bot and Flask server started successfully...')
    app.run_polling()

if __name__ == '__main__':
    main()
