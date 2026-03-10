
import logging
import os
import json
import asyncio
from datetime import datetime

import instaloader
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Configuration --- #
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8512837274:AAFoJ4WxFlmrY_PsBKNahtgMEAtVyHMSTps")
INSTAGRAM_USERNAME = os.environ.get("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.environ.get("INSTAGRAM_PASSWORD")

# File to store watched profiles data
WATCHED_PROFILES_FILE = "watched_profiles.json"

# Interval for checking profiles (in seconds)
CHECK_INTERVAL_SECONDS = 300 # 5 minutes

# --- Instaloader Setup --- #
L = instaloader.Instaloader()

# --- Data Storage --- #
# Structure: {chat_id: {username: {last_bio: str, last_pic_url: str, last_posts_count: int, last_followers_count: int, last_full_name: str}}}
watched_profiles = {}

def load_watched_profiles():
    global watched_profiles
    if os.path.exists(WATCHED_PROFILES_FILE):
        with open(WATCHED_PROFILES_FILE, "r", encoding="utf-8") as f:
            watched_profiles = json.load(f)
        logger.info(f"Loaded {len(watched_profiles)} watched profiles from file.")

def save_watched_profiles():
    with open(WATCHED_PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(watched_profiles, f, indent=4, ensure_ascii=False)
    logger.info("Watched profiles saved to file.")

# --- Instagram Login --- #
async def login_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        await update.message.reply_text(
            "لم يتم تعيين بيانات تسجيل الدخول لإنستجرام. يرجى استخدام الأمر /set_instagram_credentials أولاً."
        )
        return False
    try:
        L.load_session_from_file(INSTAGRAM_USERNAME, f"instaloader_{INSTAGRAM_USERNAME}.session")
        logger.info(f"Loaded Instaloader session for {INSTAGRAM_USERNAME}.")
    except FileNotFoundError:
        try:
            L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            L.save_session_to_file(f"instaloader_{INSTAGRAM_USERNAME}.session")
            logger.info(f"Logged in to Instagram as {INSTAGRAM_USERNAME} and saved session.")
        except Exception as e:
            logger.error(f"Failed to log in to Instagram: {e}")
            await update.message.reply_text(
                f"فشل تسجيل الدخول إلى إنستجرام: {e}. يرجى التحقق من بيانات الاعتماد."
            )
            return False
    return True

# --- Telegram Commands --- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"مرحباً {user.mention_html()}!\nأنا بوت مراقبة إنستجرام. يمكنني مراقبة التغييرات في ملفات تعريف إنستجرام وإعلامك بها.\n\n"\
        "استخدم /set_instagram_credentials لتعيين بيانات تسجيل الدخول لإنستجرام.\n"\
        "استخدم /add_profile [اسم_المستخدم] لمراقبة ملف تعريف.\n"\
        "استخدم /list_profiles لعرض الملفات الشخصية التي تتم مراقبتها.\n"\
        "استخدم /remove_profile [اسم_المستخدم] لإزالة ملف تعريف من المراقبة."
    )

async def set_instagram_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 2:
        await update.message.reply_text(
            "الاستخدام: /set_instagram_credentials [اسم_مستخدم_إنستجرام] [كلمة_مرور_إنستجرام]\n"\
            "ملاحظة: سيتم حفظ بيانات الاعتماد كمتغيرات بيئة في بيئة الاستضافة."
        )
        return
    
    # In a real deployment, these should be set as environment variables on the hosting platform.
    # For local testing, you can set them like: export INSTAGRAM_USERNAME="your_username" etc.
    # For this example, we'll just inform the user.
    await update.message.reply_text(
        "يرجى تعيين INSTAGRAM_USERNAME و INSTAGRAM_PASSWORD كمتغيرات بيئة في بيئة الاستضافة الخاصة بك.\n"\
        "إذا كنت تختبر محليًا، يمكنك تعيينها باستخدام `export` في الطرفية."
    )
    # Note: We don't store them directly in the bot's memory for security reasons.

async def add_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await login_instagram(update, context):
        return

    args = context.args
    if not args:
        await update.message.reply_text("الاستخدام: /add_profile [اسم_مستخدم_إنستجرام]")
        return

    target_username = args[0].lower()
    chat_id = str(update.effective_chat.id)

    if chat_id not in watched_profiles:
        watched_profiles[chat_id] = {}

    if target_username in watched_profiles[chat_id]:
        await update.message.reply_text(f"أنت تراقب بالفعل @{target_username}.")
        return

    try:
        profile = instaloader.Profile.from_username(L.context, target_username)
        watched_profiles[chat_id][target_username] = {
            "last_bio": profile.biography,
            "last_pic_url": profile.profile_pic_url,
            "last_posts_count": profile.mediacount,
            "last_followers_count": profile.followers,
            "last_full_name": profile.full_name,
            "added_at": datetime.now().isoformat()
        }
        save_watched_profiles()
        await update.message.reply_text(f"بدأت مراقبة @{target_username} بنجاح!\n"\
                                       f"السيرة الذاتية: {profile.biography[:50]}...\n"\
                                       f"عدد المنشورات: {profile.mediacount}")
    except instaloader.exceptions.ProfileNotExistsException:
        await update.message.reply_text(f"الملف الشخصي @{target_username} غير موجود.")
    except Exception as e:
        logger.error(f"Error adding profile {target_username}: {e}")
        await update.message.reply_text(f"حدث خطأ أثناء إضافة الملف الشخصي: {e}")

async def list_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    if chat_id not in watched_profiles or not watched_profiles[chat_id]:
        await update.message.reply_text("أنت لا تراقب أي ملفات شخصية حاليًا.")
        return

    response_text = "الملفات الشخصية التي تتم مراقبتها:\n"
    for username, data in watched_profiles[chat_id].items():
        response_text += f"- @{username} (تمت الإضافة في: {data.get('added_at', 'N/A')[:10]})\n"
    await update.message.reply_text(response_text)

async def remove_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text("الاستخدام: /remove_profile [اسم_مستخدم_إنستجرام]")
        return

    target_username = args[0].lower()
    chat_id = str(update.effective_chat.id)

    if chat_id in watched_profiles and target_username in watched_profiles[chat_id]:
        del watched_profiles[chat_id][target_username]
        save_watched_profiles()
        await update.message.reply_text(f"تمت إزالة @{target_username} من المراقبة.")
    else:
        await update.message.reply_text(f"الملف الشخصي @{target_username} ليس ضمن قائمة المراقبة.")

async def check_profiles_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Running scheduled profile check...")
    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        logger.warning("Instagram credentials not set. Skipping profile check.")
        return

    try:
        L.load_session_from_file(INSTAGRAM_USERNAME, f"instaloader_{INSTAGRAM_USERNAME}.session")
    except FileNotFoundError:
        try:
            L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            L.save_session_to_file(f"instaloader_{INSTAGRAM_USERNAME}.session")
        except Exception as e:
            logger.error(f"Failed to log in to Instagram for background check: {e}")
            # Optionally, notify all users that login failed
            return
    except Exception as e:
        logger.error(f"Error loading Instaloader session: {e}")
        return

    for chat_id, profiles in list(watched_profiles.items()): # Use list() to allow modification during iteration
        for username, last_data in list(profiles.items()):
            try:
                profile = instaloader.Profile.from_username(L.context, username)
                changes = []

                # Check Bio
                if profile.biography != last_data["last_bio"]:
                    changes.append(f"السيرة الذاتية (Bio) تغيرت من:\n`{last_data['last_bio']}`\nإلى:\n`{profile.biography}`")
                    last_data["last_bio"] = profile.biography
                
                # Check Profile Picture
                if profile.profile_pic_url != last_data["last_pic_url"]:
                    changes.append(f"صورة الملف الشخصي تغيرت! [الجديدة هنا]({profile.profile_pic_url})")
                    last_data["last_pic_url"] = profile.profile_pic_url
                    # Optionally send the new picture directly
                    # await context.bot.send_photo(chat_id=chat_id, photo=profile.profile_pic_url)

                # Check Posts Count
                if profile.mediacount != last_data["last_posts_count"]:
                    if profile.mediacount > last_data["last_posts_count"]:
                        changes.append(f"تم نشر منشور جديد! (العدد الحالي: {profile.mediacount})")
                    else:
                        changes.append(f"تم حذف منشور! (العدد الحالي: {profile.mediacount})")
                    last_data["last_posts_count"] = profile.mediacount
                
                # Check Full Name
                if profile.full_name != last_data["last_full_name"]:
                    changes.append(f"الاسم الكامل تغير من `{last_data['last_full_name']}` إلى `{profile.full_name}`")
                    last_data["last_full_name"] = profile.full_name

                if changes:
                    notification_text = f"🚨 **تغيير في ملف @{username} على إنستجرام!** 🚨\n\n" + "\n\n".join(changes)
                    await context.bot.send_message(chat_id=chat_id, text=notification_text, parse_mode="Markdown")
                    save_watched_profiles()

            except instaloader.exceptions.ProfileNotExistsException:
                await context.bot.send_message(chat_id=chat_id, text=f"⚠️ الملف الشخصي @{username} لم يعد موجودًا. تمت إزالته من المراقبة.")
                del watched_profiles[chat_id][username]
                save_watched_profiles()
            except Exception as e:
                logger.error(f"Error checking profile {username} for chat {chat_id}: {e}")
                # Optionally, notify the user about the error

    logger.info("Finished scheduled profile check.")

def main() -> None:
    load_watched_profiles()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    job_queue = application.job_queue

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_instagram_credentials", set_instagram_credentials))
    application.add_handler(CommandHandler("add_profile", add_profile))
    application.add_handler(CommandHandler("list_profiles", list_profiles))
    application.add_handler(CommandHandler("remove_profile", remove_profile))

    # Schedule the background job to check profiles periodically
    job_queue.run_repeating(check_profiles_job, interval=CHECK_INTERVAL_SECONDS, first=10) # Start after 10 seconds

    logger.info("Bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
