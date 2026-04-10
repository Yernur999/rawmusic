import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": query,
        "key": YOUTUBE_API_KEY,
        "type": "video",
        "maxResults": 10
    }

    r = requests.get(url, params=params)
    data = r.json()

    results = []

    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        thumbnail = item["snippet"]["thumbnails"]["default"]["url"]

        results.append({
            "title": title,
            "video_id": video_id,
            "thumbnail": thumbnail
        })

    return jsonify(results)


@app.route("/play_from_app", methods=["POST"])
def play_from_app():
    data = request.get_json()

    user_id = data.get("user_id")
    title = data.get("title", "Test Track")

    if not user_id or not TELEGRAM_BOT_TOKEN:
        return jsonify({"ok": False, "error": "missing user_id or bot token"}), 400

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendAudio"

    payload = {
        "chat_id": user_id,
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "title": title,
        "performer": "RawMusic"
    }

    r = requests.post(telegram_url, data=payload, timeout=20)

    return jsonify({
        "ok": r.ok,
        "status_code": r.status_code
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
