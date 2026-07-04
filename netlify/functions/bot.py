import os
import json
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
MONETAG_SMARTLINK = os.getenv("MONETAG_SMARTLINK", "https://www.google.com")
COBALT_API_URL = "https://api.cobalt.tools/api/json"

def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

def handler(event, context):
    if not event.get("body"):
        return {"statusCode": 400, "body": "Missing body"}

    try:
        body_data = json.loads(event["body"])
        message = body_data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()

        if not chat_id or not text:
            return {"statusCode": 200, "body": "No action"}

        if text.startswith("/start"):
            send_telegram_message(
                chat_id, 
                "👋 *Welcome!*\n\nSend me any valid YouTube link, and I will instantly extract your high-speed download links."
            )
            return {"statusCode": 200, "body": "Success"}

        if "youtube.com" in text or "youtu.be" in text:
            send_telegram_message(chat_id, "⏳ *Processing your video link... Please wait...*")

            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            payload = {"url": text, "videoQuality": "720", "downloadMode": "auto"}

            try:
                response = requests.post(COBALT_API_URL, json=payload, headers=headers, timeout=12)
                if response.status_code == 200:
                    stream_url = response.json().get("url")
                    if stream_url:
                        reply_markup = {
                            "inline_keyboard": [
                                [{"text": "🚀 High-Speed Download (Fast)", "url": MONETAG_SMARTLINK}],
                                [{"text": "📁 Direct Stream Link (Backup)", "url": stream_url}]
                            ]
                        }
                        send_telegram_message(
                            chat_id, 
                            "✅ *Your video is fully processed and ready!*\n\nSelect a download mirror below:", 
                            reply_markup=reply_markup
                        )
                    else:
                        send_telegram_message(chat_id, "❌ Failed to parse media stream extraction vectors.")
                else:
                    send_telegram_message(chat_id, f"❌ Processing engine error: {response.status_code}")
            except Exception as e:
                send_telegram_message(chat_id, f"💥 Error calling processing server: {str(e)}")
        else:
            send_telegram_message(chat_id, "❌ Please send a valid YouTube link.")

        return {"statusCode": 200, "body": "Success"}

    except Exception as err:
        print(f"Crash: {str(err)}")
        return {"statusCode": 500, "body": "Error"}