import os
import json
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# CONFIGURATION & ENVIRONMENT SETUP
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
MONETAG_SMARTLINK = os.getenv("MONETAG_SMARTLINK", "https://www.google.com") 
COBALT_API_URL = "https://api.cobalt.tools/api/json"

# ==========================================
# BOT CORE ACTIONS
# ==========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcoming greeting to the user."""
    await update.message.reply_text(
        "👋 Welcome! Send me any YouTube link, and I will instantly extract your high-speed download links."
    )

async def process_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts text inputs, queries Cobalt, and responds with buttons."""
    user_url = update.message.text.strip()
    
    if not ("youtube.com" in user_url or "youtu.be" in user_url):
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    status_message = await update.message.reply_text("⏳ Processing your video link... Please wait...")

    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": user_url,
            "videoQuality": "720",
            "downloadMode": "auto"
        }

        response = requests.post(COBALT_API_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            stream_url = data.get("url")

            if stream_url:
                keyboard = [
                    [InlineKeyboardButton("🚀 High-Speed Download (Fast)", url=MONETAG_SMARTLINK)],
                    [InlineKeyboardButton("📁 Direct Stream Link (Backup)", url=stream_url)]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await status_message.delete()
                await update.message.reply_text(
                    "✅ Your video is fully processed and ready!\n\nSelect a download mirror below:",
                    reply_markup=reply_markup
                )
            else:
                await status_message.edit_text("❌ Failed to parse media stream extraction vectors.")
        else:
            await status_message.edit_text(f"❌ Processing engine error: {response.status_code}")

    except Exception as e:
        await status_message.edit_text(f"💥 Error processing request: {str(e)}")

# ==========================================
# HOUSING EVERYTHING IN ONE ASYNC RUNNER
# ==========================================

async def main_pipeline(tg_update, application):
    """Executes all steps sequentially inside a single unified async loop."""
    await application.initialize()
    await application.start()  # Required to wake up route listening
    await application.process_update(tg_update)
    await application.stop()   # Gracefully wind down before freeze
    await application.shutdown()

# ==========================================
# SYNCHRONOUS NETLIFY RUNTIME GATEWAY
# ==========================================

def handler(event, context):
    """Standard synchronous entrypoint for Netlify Serverless Functions."""
    if not event.get("body"):
        return {"statusCode": 400, "body": "Missing request payload body."}

    try:
        # Create application instance
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Wire up event routers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_youtube_link))
        # Parse incoming update
        body_data = json.loads(event["body"])
        tg_update = Update.de_json(body_data, application.bot)

        # Run everything in ONE single event loop execution
        asyncio.run(main_pipeline(tg_update, application))

        return {
            "statusCode": 200,
            "body": json.dumps({"status": "success"})
        }

    except Exception as err:
        print(f"Crash details: {str(err)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "error": str(err)})
        }