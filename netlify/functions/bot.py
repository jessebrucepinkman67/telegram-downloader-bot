import os
import json
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# CONFIGURATION & ENVIRONMENT SETUP
# ==========================================
# Netlify will inject these environment variables dynamically
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_FALLBACK_TOKEN")
MONETAG_SMARTLINK = os.getenv("MONETAG_SMARTLINK", "https://www.google.com") 
COBALT_API_URL = "https://api.cobalt.tools/api/json"

# ==========================================
# ASYNCHRONOUS CORE LOGIC PIPELINE
# ==========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcoming welcome greeting to the user."""
    await update.message.reply_text(
        "👋 Welcome! Send me any YouTube link, and I will instantly extract your high-speed download links."
    )

async def process_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts text inputs, queries the Cobalt engine, and responds with monetization payloads."""
    user_url = update.message.text.strip()
    
    # Filter for rough YouTube syntax footprint
    if not ("youtube.com" in user_url or "youtu.be" in user_url):
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    status_message = await update.message.reply_text("⏳ Processing your video link... Please wait...")

    try:
        # Construct the payloads according to Cobalt standards
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": user_url,
            "videoQuality": "720",
            "downloadMode": "auto"
        }

        # Send request synchronously inside the async runner wrapper via requests
        response = requests.post(COBALT_API_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            stream_url = data.get("url")

            if stream_url:
                # Build the conversion keyboard architecture
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
                await status_message.edit_text("❌ Failed to parse media stream extraction vectors from server response.")
        else:
            await status_message.edit_text(f"❌ Processing engine responded with error status: {response.status_code}")

    except Exception as e:
        await status_message.edit_text(f"💥 Error processing request: {str(e)}")

# ==========================================
# SYNCHRONOUS NETLIFY RUNTIME EXECUTION GATEWAY
# ==========================================

def handler(event, context):
    """
    Standard synchronous entrypoint for Netlify Serverless Functions.
    Interprets incoming webhooks from Telegram and maps them into the Async event loop.
    """
    # Verify that request payload exists and is valid
    if not event.get("body"):
        return {
            "statusCode": 400,
            "body": json.dumps({"status": "error", "message": "Missing request payload body."})
        }

    try:
        # Initialize standard framework container locally to prevent persistent memory footprints
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        # Wire up event routers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_youtube_link))

        # Parse data arriving from Telegram
        body_data = json.loads(event["body"])
        tg_update = Update.de_json(body_data, application.bot)

        # Initialize explicit asyncio loop mapping execution pipeline context
        asyncio.run(application.initialize())
        asyncio.run(application.process_update(tg_update))
        asyncio.run(application.shutdown())

        return {
            "statusCode": 200,
            "body": json.dumps({"status": "success", "message": "Webhook pipeline executed successfully."})
        }

    except Exception as err:
        print(f"Serverless Runtime Execution Crash: {str(err)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "runtime_crash", "error": str(err)})
        }