export default async (req, context) => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  try {
    const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || "";
    const MONETAG_SMARTLINK = process.env.MONETAG_SMARTLINK || "https://www.google.com";
    const COBALT_API_URL = "https://api.cobalt.tools/api/json";

    const bodyData = await req.json();
    const message = bodyData.message || {};
    const chatId = message.chat?.id;
    const text = (message.text || "").trim();

    if (!chatId || !text) {
      return new Response("No action", { status: 200 });
    }

    // Fixed using standard quotes to completely avoid punctuation errors
    const tgUrl = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage";

    if (text.startsWith("/start")) {
      await fetch(tgUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          text: "👋 *Welcome!*\n\nSend me any valid YouTube link, and I will instantly extract your high-speed download links.",
          parse_mode: "Markdown"
        })
      });
      return new Response("Success", { status: 200 });
    }

    if (text.includes("youtube.com") || text.includes("youtu.be")) {
      await fetch(tgUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          chat_id: chatId, 
          text: "⏳ *Processing your video link... Please wait...*", 
          parse_mode: "Markdown" 
        })
      });

      const cobaltResponse = await fetch(COBALT_API_URL, {
        method: "POST",
        headers: { "Accept": "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ url: text, videoQuality: "720", downloadMode: "auto" })
      });

      if (cobaltResponse.status === 200) {
        const cobaltData = await cobaltResponse.json();
        const streamUrl = cobaltData.url;

        if (streamUrl) {
          await fetch(tgUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              chat_id: chatId,
              text: "✅ *Your video is fully processed and ready!*\n\nSelect a download mirror below:",
              reply_markup: {
                inline_keyboard: [
                  [{ text: "🚀 High-Speed Download (Fast)", url: MONETAG_SMARTLINK }],
                  [{ text: "📁 Direct Stream Link (Backup)", url: streamUrl }]
                ]
              }
            })
          });
        } else {
          await fetch(tgUrl, { 
            method: "POST", 
            headers: { "Content-Type": "application/json" }, 
            body: JSON.stringify({ chat_id: chatId, text: "❌ Failed to parse download link." }) 
          });
        }
      } else {
        await fetch(tgUrl, { 
          method: "POST", 
          headers: { "Content-Type": "application/json" }, 
          body: JSON.stringify({ chat_id: chatId, text: "❌ Processing engine error." }) 
        });
      }
    } else {
      await fetch(tgUrl, { 
        method: "POST", 
        headers: { "Content-Type": "application/json" }, 
        body: JSON.stringify({ chat_id: chatId, text: "❌ Please send a valid YouTube link." }) 
      });
    }

    return new Response("Success", { status: 200 });

  } catch (err) {
    console.error("Crash:", err);
    return new Response("Error", { status: 500 });
  }
};