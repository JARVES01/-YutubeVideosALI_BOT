import os
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import asyncio

# Get token from environment variable or paste token string below
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

LANGS = {
    "UZ": {
        "welcome": "🇺🇿 Tilni tanlang:",
        "ask_link": "🔗 YouTube link yuboring:",
        "not_link": "❌ Bu YouTube link emas. Iltimos to'g'ri link yuboring.",
        "choose": "Nimani yuklaymiz?",
        "downloading": "⏳ Yuklanmoqda, sabr qiling...",
        "error": "❌ Xatolik: {}",
        "done": "✅ Tayyor!"
    },
    "RU": {
        "welcome": "🇷🇺 Выберите язык:",
        "ask_link": "🔗 Отправьте ссылку YouTube:",
        "not_link": "❌ Это не ссылка на YouTube. Пожалуйста, отправьте правильную ссылку.",
        "choose": "Что скачать?",
        "downloading": "⏳ Скачиваю, подождите...",
        "error": "❌ Ошибка: {}",
        "done": "✅ Готово!"
    },
    "EN": {
        "welcome": "🇬🇧 Choose language:",
        "ask_link": "🔗 Send a YouTube link:",
        "not_link": "❌ That's not a YouTube link. Please send a correct link.",
        "choose": "What do you want to download?",
        "downloading": "⏳ Downloading, please wait...",
        "error": "❌ Error: {}",
        "done": "✅ Done!"
    }
}

def is_youtube(url: str) -> bool:
    if not url: return False
    return "youtube.com" in url or "youtu.be" in url

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇺🇿 UZ", callback_data="lang_UZ"),
         InlineKeyboardButton("🇷🇺 RU", callback_data="lang_RU"),
         InlineKeyboardButton("🇬🇧 EN", callback_data="lang_EN")]
    ]
    await update.message.reply_text("Tilni tanlang / Выберите язык / Choose your language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def lang_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # e.g., "lang_UZ"
    lang = data.split("_")[1]
    context.user_data["lang"] = lang
    await query.edit_message_text(LANGS[lang]["ask_link"])

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lang = context.user_data.get("lang", "EN")
    if not is_youtube(text):
        await update.message.reply_text(LANGS[lang]["not_link"])
        return

    # present choice video/audio
    keyboard = [
        [InlineKeyboardButton("🎥 Video", callback_data=f"dl_video|{text}"),
         InlineKeyboardButton("🎵 Audio (mp3)", callback_data=f"dl_audio|{text}")]
    ]
    await update.message.reply_text(LANGS[lang]["choose"], reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # e.g., "dl_video|https://..."
    try:
        choice, url = data.split("|", 1)
    except Exception:
        await query.edit_message_text("❌ Invalid data")
        return

    lang = context.user_data.get("lang", "EN")
    await query.edit_message_text(LANGS[lang]["downloading"])

    uid = str(uuid.uuid4())[:8]
    if choice == "dl_video":
        outtmpl = f"video_{uid}.%(ext)s"
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
        }
    else:
        outtmpl = f"audio_{uid}.%(ext)s"
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "bestaudio",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        }

    loop = asyncio.get_event_loop()
    try:
        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # find generated filename
                filename = ydl.prepare_filename(info)
                # If audio postprocessor changed extension to .mp3, replace
                if choice == "dl_audio":
                    filename = os.path.splitext(filename)[0] + ".mp3"
                return filename

        filename = await loop.run_in_executor(None, run_ydl)

        # send file
        with open(filename, "rb") as f:
            if choice == "dl_video":
                await query.message.reply_video(f)
            else:
                await query.message.reply_audio(f)

        await query.message.reply_text(LANGS[lang]["done"])
    except Exception as e:
        await query.message.reply_text(LANGS[lang]["error"].format(e))
    finally:
        # cleanup possible files (wildcard)
        for fname in os.listdir("."):
            if fname.startswith(f"video_{uid}") or fname.startswith(f"audio_{uid}"):
                try:
                    os.remove(fname)
                except:
                    pass

def main():
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print("Error: Please set BOT_TOKEN environment variable or insert your token into the script.")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_button, pattern=r"^lang_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_click, pattern=r"^dl_"))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
