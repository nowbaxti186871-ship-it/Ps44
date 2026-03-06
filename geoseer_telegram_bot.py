
import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Replace with your actual GeoSeer API Key
GEOSEER_API_KEY = os.environ.get("GEOSEER_API_KEY", "gsk_qKoLEEhXh_JN1oS8qRDbb8Z4MGxMWIbsmti_j3h5pK8")

# Replace with your actual Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8512837274:AAFoJ4WxFlmrY_PsBKNahtgMEAtVyHMSTps")

# GeoSeer API endpoint (as per documentation found)
GEOSEER_API_BASE_URL = "https://api.geoseer.net/v1/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"مرحباً {user.mention_html()}!\nأنا بوت GeoSeer. أرسل لي استعلام بحث (مثل اسم مدينة أو معلم جغرافي) وسأبحث لك عن بيانات مكانية."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /help is issued."""
    await update.message.reply_text("أرسل لي أي نص للبحث عن بيانات مكانية باستخدام GeoSeer API.")

async def search_geoseer(query: str) -> dict:
    """Searches GeoSeer API for the given query."""
    headers = {"Authorization": f"Bearer {GEOSEER_API_KEY}"}
    params = {"q": query}
    try:
        # Based on OpenAPI documentation, search might be at /search or /datasets
        response = requests.get(f"{GEOSEER_API_BASE_URL}search", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling GeoSeer API: {e}")
        return {"error": str(e)}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming messages and performs GeoSeer search."""
    user_query = update.message.text
    await update.message.reply_text(f"جاري البحث عن '{user_query}'...")

    search_results = await search_geoseer(user_query)

    if "error" in search_results:
        await update.message.reply_text(f"حدث خطأ أثناء البحث: {search_results['error']}\nيرجى التأكد من صحة مفتاح الـ API.")
        return

    # Process results based on GeoSeer's actual JSON structure
    results = search_results.get("results", [])
    if not results:
        await update.message.reply_text("لم يتم العثور على نتائج لطلبك.")
        return

    response_text = "نتائج البحث:\n\n"
    for result in results[:5]:  # Show top 5 results
        title = result.get("title", "لا يوجد عنوان")
        abstract = result.get("abstract", "لا يوجد وصف")
        service_type = result.get("service_type", "غير محدد")
        
        response_text += f"📍 **{title}**\n"
        response_text += f"نوع الخدمة: {service_type}\n"
        response_text += f"الوصف: {abstract[:100]}...\n\n"

    await update.message.reply_text(response_text, parse_mode="Markdown")

def main() -> None:
    """Start the bot."""
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("Please set your TELEGRAM_BOT_TOKEN!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
