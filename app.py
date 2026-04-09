
import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
@app.route('/telegram')
def telegram():
    return render_template('index.html')
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

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
        "type": "video",
        "maxResults": 10,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    results = []

    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        thumbnail = item["snippet"]["thumbnails"]["medium"]["url"]

        results.append({
            "title": title,
            "video_id": video_id,
            "thumbnail": thumbnail,
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
