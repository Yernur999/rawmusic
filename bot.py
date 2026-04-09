import os
import json
import yt_dlp
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"playlists": {}, "pending": {}, "create_mode": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = load_data()

def ensure_user(user_id: str):
    if user_id not in db["playlists"]:
        db["playlists"][user_id] = {}

def search_youtube(query: str):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch3:{query}", download=False)
        return result.get("entries", [])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "RawMusic 🎵\n\n"
        "/playlist — создать\n"
        "/playlists — список\n"
        "/view — открыть плейлист\n\n"
        "Напиши трек 🔎"
    )

async def playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db["create_mode"][user_id] = True
    save_data(db)
    await update.message.reply_text("Название плейлиста?")

async def playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    ensure_user(user_id)

    pls = db["playlists"][user_id]

    if not pls:
        await update.message.reply_text("Нет плейлистов")
        return

    text = "\n".join(pls.keys())
    await update.message.reply_text(text)

async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    ensure_user(user_id)

    pls = db["playlists"][user_id]

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"open|{name}")]
        for name in pls.keys()
    ]

    await update.message.reply_text(
        "Выбери:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    ensure_user(user_id)

    text = update.message.text.strip()

    if db["create_mode"].get(user_id):
        db["create_mode"][user_id] = False
        db["playlists"][user_id][text] = []
        save_data(db)
        await update.message.reply_text(f"Создан: {text}")
        return

    results = search_youtube(text)

    db["pending"][user_id] = {}

    for i, r in enumerate(results, 1):
        title = r["title"]
        url = f"https://youtube.com/watch?v={r['id']}"

        db["pending"][user_id][str(i)] = {
            "title": title,
            "url": url
        }

        await update.message.reply_text(
            title,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Открыть", url=url)],
                [InlineKeyboardButton("➕ Add", callback_data=f"choose|{i}")]
            ])
        )

    save_data(db)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = query.data.split("|")

    if data[0] == "choose":
        track = db["pending"][user_id][data[1]]

        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"add|{data[1]}|{name}")]
            for name in db["playlists"][user_id].keys()
        ]

        await query.edit_message_text(
            track["title"],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data[0] == "add":
        track = db["pending"][user_id][data[1]]
        pl = data[2]

        db["playlists"][user_id][pl].append(track)
        save_data(db)

        await query.edit_message_text(f"Добавлено в {pl}")

    elif data[0] == "open":
        pl = data[1]
        tracks = db["playlists"][user_id][pl]

        if not tracks:
            await query.edit_message_text("Пусто")
            return

        for i, t in enumerate(tracks):
            await query.message.reply_text(
                t["title"],
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("▶️ Play", url=t["url"])],
                    [InlineKeyboardButton("❌ Удалить", callback_data=f"del|{pl}|{i}")]
                ])
            )

    elif data[0] == "del":
        pl = data[1]
        idx = int(data[2])

        db["playlists"][user_id][pl].pop(idx)
        save_data(db)

        await query.edit_message_text("Удалено")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("playlist", playlist))
app.add_handler(CommandHandler("playlists", playlists))
app.add_handler(CommandHandler("view", view))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(button))

print("Бот запущен...")
app.run_polling()
