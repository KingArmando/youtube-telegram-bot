import os
import json
import urllib.request
import xml.etree.ElementTree as ET

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNELS = os.environ["TELEGRAM_CHAT_IDS"].split(",")
YOUTUBE_CHANNEL_ID = os.environ["YOUTUBE_CHANNEL_ID"]

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
STATE_FILE = "last_video.json"


def telegram_send(chat_id, video_id, title):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

    caption = f"🎮 ویدیوی جدید گیمر ددی منتشر شد!\n\n{title}\n\n▶️ تماشای ویدیو:\n{video_url}"

    data = {
        "chat_id": chat_id,
        "photo": thumbnail,
        "caption": caption
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not result.get("ok"):
        raise RuntimeError(f"Telegram error: {result}")


def main():
    request = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    namespace = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015"
    }

    entries = root.findall("atom:entry", namespace)

    if not entries:
        print("No videos found.")
        return

    latest = entries[0]
    video_id = latest.findtext("yt:videoId", namespaces=namespace)
    title = latest.findtext("atom:title", namespaces=namespace)

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            last_video_id = json.load(file).get("last_video_id")
    except (FileNotFoundError, json.JSONDecodeError):
        last_video_id = None

    if video_id == last_video_id:
        print("No new video.")
        return

    if last_video_id is None:
        print("First run: saving latest video without sending.")
    else:
        for chat_id in CHANNELS:
            telegram_send(chat_id.strip(), video_id, title)

    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump({"last_video_id": video_id}, file)

    print("Done.")


if __name__ == "__main__":
    main()
