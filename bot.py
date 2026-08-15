import base64
import logging
import os
import threading
from urllib.parse import quote
import requests
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- 1. Flask Web Server ---
flask_app = Flask(__name__)


@flask_app.route('/')
def home():
  return 'Bot is running 24/7 successfully!'


def run_flask():
  port = int(os.environ.get('PORT', 8080))
  flask_app.run(host='0.0.0.0', port=port)


# --- 2. CONFIGURATION ---
BOT_TOKEN = '8952565156:AAHubKRCMzY6D6_hLcLwvta-3M5Pd_DoF-E'
STORAGE_CHANNEL_ID = -1004499292164
MAIN_CHANNEL_USERNAME = '@MYxxxxx9'  # আপনার মূল চ্যানেলের ইউজারনেম
BOT_USERNAME = 'MySongPremium2026Bot'  # আপনার বটের ইউজারনেম
WEB_APP_URL = 'https://ji0771295-ctrl.github.io/mybot'  # আপনার গিটহাব পেজের ওয়েবলিংক
ADMIN_ID = 8672040646  # আপনার পার্সোনাল টেলিগ্রাম আইডি


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


# --- 3. COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  chat_id = update.effective_chat.id
  user = update.effective_user

  if context.args:
    arg = context.args[0]

    if arg.startswith('coin_'):
      parts = arg.split('_')
      if len(parts) >= 3:
        amount = parts[1]
        trx_id = '_'.join(parts[2:])

        await update.message.reply_text(
            f'✅ **আপনার কয়েন কেনার আবেদনটি জমা হয়েছে!**\n\n'
            f'💰 **পরিমাণ:** {amount} টাকা\n'
            f'🧾 **TrxID:** `{trx_id}`\n\n'
            f'এডমিন ভেরিফাই করে দ্রুত আপনার অ্যাকাউন্টে কয়েন যোগ করে দেবে। ধন্যবাদ!',
            parse_mode='Markdown',
        )

        if ADMIN_ID != 0:
          try:
            admin_msg = (
                f'💳 **নতুন কয়েন রিচার্জ রিকোয়েস্ট!**\n\n'
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
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            '🚀 Open Mini App', web_app=WebAppInfo(url=WEB_APP_URL)
        )
    ]])
    await update.message.reply_text(
        '👋 **স্বাগতম!**\nনিচের বাটনে চাপ দিয়ে সরাসরি আমাদের মিনি অ্যাপে প্রবেশ করুন এবং ভিডিও উপভোগ করুন।',
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

    encoded_v = quote(msg_id, safe='')
    encoded_t = quote(title, safe='')
    encoded_i = quote(img_url, safe='')

    final_mini_app_url = (
        f'{WEB_APP_URL}?v={encoded_v}&t={encoded_t}&img={encoded_i}'
    )

    # 🔴 চ্যানেলে পাঠানোর জন্য url= ব্যবহার করা হয়েছে (Button_type_invalid ফিক্স করা হয়েছে)
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            '🎬 Watch Video (Mini App) 🎬', url=final_mini_app_url
        )
    ]])

    await context.bot.send_photo(
        chat_id=MAIN_CHANNEL_USERNAME,
        photo=img_url,
        caption=(
            f'🎬 **{title}**\n\nনিচের বাটনে চাপ দিয়ে সরাসরি ভিডিওটি দেখুন:'
        ),
        reply_markup=keyboard,
        parse_mode='Markdown',
    )

    await update.message.reply_text(
        f'✅ পোস্টটি সফলভাবে **{MAIN_CHANNEL_USERNAME}** চ্যানেলে পোস্ট করা হয়েছে!',
        parse_mode='Markdown',
    )
  except Exception as e:
    logger.error(f'Error in create_post: {e}')
    await update.message.reply_text(
        f'❌ পোস্ট তৈরি করতে সমস্যা হয়েছে: `{str(e)}`', parse_mode='Markdown'
    )


# --- 4. AUTO VIDEO HANDLER ---
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

    encoded_v = quote(video_msg_id, safe='')
    encoded_t = quote(title, safe='')
    encoded_i = quote(img_url, safe='')

    mini_app_link = (
        f'{WEB_APP_URL}?v={encoded_v}&t={encoded_t}&img={encoded_i}'
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton('🎬 Open Mini App Test', url=mini_app_link)
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


# --- 5. MAIN FUNCTION ---
def main():
  threading.Thread(target=run_flask, daemon=True).start()

  app = Application.builder().token(BOT_TOKEN).build()

  app.add_handler(CommandHandler('start', start))
  app.add_handler(CommandHandler('post', create_post))
  app.add_handler(
      MessageHandler(filters.VIDEO | filters.Document.ALL, handle_video)
  )

  logger.info('Bot started successfully...')
  app.run_polling()


if __name__ == '__main__':
  main()
