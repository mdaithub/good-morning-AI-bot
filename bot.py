# good_morning_bot.py

import os
import json
import random
import logging
import requests
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# --- Config ---
TOKEN = 'YOUR_BOT_TOKEN'  # Replace this with your bot token

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Files ---
FILES = {
    "times": "group_times.json",
    "modes": "group_modes.json",
    "langs": "group_languages.json",
    "skip": "skip_groups.json",
    "fallback": "fallback_messages_and_images.json",
    "index": "fallback_index_tracker.json",
    "festivals": "festivals.json"
}

# --- Load JSON files ---
def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return default

group_times = load_json(FILES['times'], {})
group_modes = load_json(FILES['modes'], {})
group_langs = load_json(FILES['langs'], {})
skip_groups = set(load_json(FILES['skip'], []))
fallback_data = load_json(FILES['fallback'], {"messages": [], "image_urls": []})
index_data = load_json(FILES['index'], {"last_used_date": None, "message_index": 0, "image_index": 0})
festivals = load_json(FILES['festivals'], {})

# --- Scheduler ---
scheduler = BackgroundScheduler()
scheduler.start()

bot = Bot(token=TOKEN)
updater = Updater(bot=bot, use_context=True)
dispatcher = updater.dispatcher

# --- Admin check ---
def is_admin(update: Update) -> bool:
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ["creator", "administrator"]
    except:
        return False

# --- Helpers ---
def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def get_festival_message():
    today = datetime.now().strftime("%m-%d")
    return festivals.get(today)

def fetch_daily_quote():
    try:
        res = requests.get("https://zenquotes.io/api/today", timeout=5)
        if res.status_code == 200:
            q = res.json()[0]
            return f"🌅 Good Morning!\n\n“{q['q']}”\n— {q['a']}"
    except Exception as e:
        logger.warning(f"Quote API failed: {e}")
    return get_rotating_fallback()[0]

def fetch_daily_image():
    try:
        url = "https://source.unsplash.com/featured/?good-morning"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return url
    except Exception as e:
        logger.warning(f"Image fetch failed: {e}")
    return get_rotating_fallback()[1]

def get_rotating_fallback():
    today_str = str(datetime.today().date())
    if index_data["last_used_date"] != today_str:
        index_data["message_index"] = (index_data["message_index"] + 1) % len(fallback_data["messages"])
        index_data["image_index"] = (index_data["image_index"] + 1) % len(fallback_data["image_urls"])
        index_data["last_used_date"] = today_str
        save_json(FILES['index'], index_data)

    msg = fallback_data["messages"][index_data["message_index"]]
    img = fallback_data["image_urls"][index_data["image_index"]]
    return msg, img

def send_to_group(group_id):
    if group_id in skip_groups:
        skip_groups.discard(group_id)
        save_json(FILES['skip'], list(skip_groups))
        return

    festival_msg = get_festival_message()
    if festival_msg:
        bot.send_message(chat_id=int(group_id), text=festival_msg)
        return

    mode = group_modes.get(group_id, "mixed")
    lang = group_langs.get(group_id, "en")
    weekday = datetime.today().weekday()

    if mode in ["text", "image", "mixed"] and weekday in [5, 6]:
        mode = "sticker"

    try:
        if mode == "text":
            msg = fetch_daily_quote()
            bot.send_message(chat_id=int(group_id), text=msg)

        elif mode == "image":
            url = fetch_daily_image()
            bot.send_photo(chat_id=int(group_id), photo=url, caption="🌅 Good Morning!")

        elif mode == "sticker":
            sticker_id = random.choice([
                "CAACAgUAAxkBAAIBZ2YVBLX8gH3qtxZfZUXkJXx6N4bqAAJwAQACGvDFVYIQUYCKrEGZNAQ",
                "CAACAgUAAxkBAAIBamYVBNeH4JqUsGMeqZ3i3N-X6nQaAAJnAQACGvDFVfJ52SctP14LNAQ"
            ])
            bot.send_sticker(chat_id=int(group_id), sticker=sticker_id)

        else:  # mixed
            if random.choice([True, False]):
                send_to_group(group_id)  # recurse with text or image logic
            else:
                bot.send_sticker(chat_id=int(group_id), sticker=random.choice([
                    "CAACAgUAAxkBAAIBZ2YVBLX8gH3qtxZfZUXkJXx6N4bqAAJwAQACGvDFVYIQUYCKrEGZNAQ"
                ]))
    except Exception as e:
        logger.error(f"Sending failed to {group_id}: {e}")

# --- Scheduling ---
def schedule_group(group_id, time_str):
    hour, minute = map(int, time_str.split(":"))
    job_id = f"group_{group_id}"
    scheduler.add_job(lambda: send_to_group(group_id), CronTrigger(hour=hour, minute=minute), id=job_id, replace_existing=True)

# --- Commands ---
def start(update: Update, context: CallbackContext):
    update.message.reply_text("✅ Bot is active! Use /settime to get started.")

def settime(update: Update, context: CallbackContext):
    if not is_admin(update):
        update.message.reply_text("❌ Only group admins can use this command.")
        return

    chat_id = str(update.effective_chat.id)
    args = context.args
    if not args:
        update.message.reply_text("Usage: /settime HH:MM (24h format)")
        return
    try:
        hour, minute = map(int, args[0].split(":"))
        group_times[chat_id] = f"{hour:02d}:{minute:02d}"
        save_json(FILES['times'], group_times)
        schedule_group(chat_id, f"{hour:02d}:{minute:02d}")

        lang_code = update.effective_user.language_code or "en"
        if chat_id not in group_langs:
            group_langs[chat_id] = lang_code[:2]
            save_json(FILES['langs'], group_langs)

        update.message.reply_text(f"🕒 Time set to {hour:02d}:{minute:02d}")
    except:
        update.message.reply_text("⚠️ Invalid format. Use HH:MM")

def mode(update: Update, context: CallbackContext):
    if not is_admin(update):
        update.message.reply_text("❌ Only group admins can use this command.")
        return

    chat_id = str(update.effective_chat.id)
    args = context.args
    if not args or args[0] not in ["text", "image", "sticker", "mixed"]:
        update.message.reply_text("Usage: /mode text|image|sticker|mixed")
        return
    group_modes[chat_id] = args[0]
    save_json(FILES['modes'], group_modes)
    update.message.reply_text(f"✅ Mode set to {args[0]}")

def language(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)
    args = context.args
    if not args:
        update.message.reply_text("Usage: /language en|hi|ta|bn|ar|es|fr|de")
        return
    group_langs[chat_id] = args[0]
    save_json(FILES['langs'], group_langs)
    update.message.reply_text(f"🌐 Language set to {args[0]}")

def skip(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)
    skip_groups.add(chat_id)
    save_json(FILES['skip'], list(skip_groups))
    update.message.reply_text("⏭️ This group will skip the next message.")

def stop(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)
    for f in [group_times, group_modes, group_langs]:
        f.pop(chat_id, None)
    skip_groups.discard(chat_id)
    for k, v in zip([FILES['times'], FILES['modes'], FILES['langs']], [group_times, group_modes, group_langs]):
        save_json(k, v)
    save_json(FILES['skip'], list(skip_groups))
    scheduler.remove_job(f"group_{chat_id}")
    update.message.reply_text("🛑 Group unsubscribed.")

# --- Load scheduled jobs ---
for gid, t in group_times.items():
    schedule_group(gid, t)

# --- Register handlers ---
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("settime", settime))
dispatcher.add_handler(CommandHandler("mode", mode))
dispatcher.add_handler(CommandHandler("language", language))
dispatcher.add_handler(CommandHandler("skip", skip))
dispatcher.add_handler(CommandHandler("stop", stop))

# --- Start bot ---
updater.start_polling()
logger.info("🤖 Good Morning Bot is running...")
updater.idle()
