import os
import json
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATA_FILE = os.path.expanduser("~/rawmusic/data.json")


def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "playlists": {
                "Gym": [],
                "Chill": []
            },
            "favorites": []
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    if "playlists" not in data or not isinstance(data["playlists"], dict):
        data["playlists"] = {
            "Gym": [],
            "Chill": []
        }

    if "favorites" not in data or not isinstance(data["favorites"], list):
        data["favorites"] = []

    return data


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


db = load_data()


@app.route("/")
def home():
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
        "maxResults": 12
    }

    try:
        res = requests.get(url, params=params, timeout=15)
        data = res.json()
    except Exception:
        return jsonify([])

    results = []

    for item in data.get("items", []):
        try:
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            title = snippet.get("title", "Unknown")
            channel = snippet.get("channelTitle", "YouTube")
            thumbs = snippet.get("thumbnails", {})
            cover = (
                thumbs.get("high", {}).get("url")
                or thumbs.get("medium", {}).get("url")
                or thumbs.get("default", {}).get("url")
                or ""
            )

            results.append({
                "title": title,
                "artist": channel,
                "cover_url": cover,
                "video_id": video_id,
                "source": "YouTube"
            })
        except Exception:
            continue

    return jsonify(results)


@app.route("/playlists")
def get_playlists():
    return jsonify(list(db["playlists"].keys()))


@app.route("/playlist/<name>")
def get_playlist(name):
    return jsonify(db["playlists"].get(name, []))


@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"ok": False, "error": "empty"})

    if name in db["playlists"]:
        return jsonify({"ok": False, "error": "exists"})

    db["playlists"][name] = []
    save_data()
    return jsonify({"ok": True})


@app.route("/add", methods=["POST"])
def add_to_playlist():
    data = request.get_json(silent=True) or {}
    playlist_name = data.get("playlist")
    track = data.get("track")

    if playlist_name not in db["playlists"] or not track:
        return jsonify({"ok": False})

    exists = any(
        t.get("video_id") == track.get("video_id")
        for t in db["playlists"][playlist_name]
    )
    if not exists:
        db["playlists"][playlist_name].append(track)
        save_data()

    return jsonify({"ok": True})


@app.route("/remove", methods=["POST"])
def remove_track():
    data = request.get_json(silent=True) or {}
    playlist_name = data.get("playlist")
    index = data.get("index")

    if playlist_name not in db["playlists"]:
        return jsonify({"ok": False})

    try:
        db["playlists"][playlist_name].pop(index)
        save_data()
        return jsonify({"ok": True})
    except Exception:
        return jsonify({"ok": False})


@app.route("/favorites")
def favorites():
    return jsonify(db["favorites"])


@app.route("/favorite/add", methods=["POST"])
def add_favorite():
    data = request.get_json(silent=True) or {}
    track = data.get("track")

    if not track:
        return jsonify({"ok": False})

    exists = any(
        t.get("video_id") == track.get("video_id")
        for t in db["favorites"]
    )
    if not exists:
        db["favorites"].append(track)
        save_data()

    return jsonify({"ok": True})


@app.route("/favorite/remove", methods=["POST"])
def remove_favorite():
    data = request.get_json(silent=True) or {}
    index = data.get("index")

    try:
        db["favorites"].pop(index)
        save_data()
        return jsonify({"ok": True})
    except Exception:
        return jsonify({"ok": False})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
