import re
import json
import requests
from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class BaiduFetcher(BaseFetcher):
    platform = "baidu"
    platform_name = "百度热搜"
    icon = "🔍"
    group = "domestic"
    source_url = "https://top.baidu.com/board?tab=realtime"

    def fetch(self) -> list[HotItem]:
        url = "https://top.baidu.com/board?tab=realtime"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html",
        }
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()

        # 百度热搜页面内嵌 JSON 数据
        match = re.search(r'<!--s-data:(.*?)-->', r.text, re.DOTALL)
        if not match:
            return []

        data = json.loads(match.group(1))
        cards = data.get("data", {}).get("cards", [])
        if not cards:
            return []

        items = []
        content = cards[0].get("content", [])
        for i, entry in enumerate(content[:30]):
            word = entry.get("word", entry.get("query", ""))
            hot_score = entry.get("hotScore", "")
            desc = entry.get("desc", "")
            img = entry.get("img", "")
            link = entry.get("url", f"https://www.baidu.com/s?wd={word}")

            items.append(HotItem(
                rank=i + 1,
                title=word,
                url=link,
                hot_value=str(hot_score) if hot_score else "",
                category=desc[:50] if desc else "",
                cover_img=img,
            ))
        return items
