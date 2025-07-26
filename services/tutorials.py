# services/tutorials.py

import requests
from bs4 import BeautifulSoup
import json

def get_youtube_tutorials(query: str, max_results=3):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"

    try:
        res = requests.get(search_url, headers=headers, timeout=5)
        if res.status_code != 200:
            raise Exception("YouTube response failed")

        soup = BeautifulSoup(res.text, "html.parser")

        # 🔍 Extract embedded JSON data
        for script in soup.find_all("script"):
            if "var ytInitialData" in script.text:
                json_text = script.string
                break
        else:
            return fallback_results(query, search_url)

        start = json_text.find("var ytInitialData = ") + len("var ytInitialData = ")
        end = json_text.find("};", start) + 1
        data = json.loads(json_text[start:end])

        results = []
        videos = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]
        video_items = videos[0]["itemSectionRenderer"]["contents"]

        for item in video_items:
            video = item.get("videoRenderer")
            if not video:
                continue

            video_id = video.get("videoId")
            title_runs = video.get("title", {}).get("runs", [])
            title = title_runs[0]["text"] if title_runs else "YouTube Tutorial"

            if video_id:
                results.append({
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                })

            if len(results) == max_results:
                break

        return results or fallback_results(query, search_url)

    except Exception as e:
        print("❌ YouTube tutorial scraping failed:", e)
        return fallback_results(query, search_url)


def fallback_results(query, search_url):
    return [{
        "title": f"Search YouTube for {query}",
        "url": search_url
    }]
