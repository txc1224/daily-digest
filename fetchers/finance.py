import feedparser
from typing import List


# 使用境外可访问的财经 RSS 源
FINANCE_FEEDS = [
    "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",  # MarketWatch
    "https://www.investing.com/rss/news.rss",                             # Investing.com
    "https://feeds.reuters.com/reuters/businessNews",                     # 路透社财经
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",              # CNBC 财经
]


def fetch_finance(limit: int = 5) -> List[dict]:
    """从财经 RSS 源抓取财经资讯，去重后取前 limit 条"""
    items = []
    seen_titles = set()
    for url in FINANCE_FEEDS:
        try:
            d = feedparser.parse(url)
            for entry in d.entries:
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                if title and link and title not in seen_titles:
                    seen_titles.add(title)
                    items.append({"title": title, "link": link})
                if len(items) >= limit:
                    break
        except Exception:
            continue
        if len(items) >= limit:
            break
    return items[:limit]
