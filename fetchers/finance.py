import feedparser
from typing import List


# 使用境外可访问的财经 RSS 源
FINANCE_FEEDS = [
    "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",  # MarketWatch
    "https://www.investing.com/rss/news.rss",                              # Investing.com
]


def fetch_finance(limit: int = 5) -> List[dict]:
    """从财经 RSS 源抓取财经资讯"""
    items = []
    for url in FINANCE_FEEDS:
        try:
            d = feedparser.parse(url)
            for entry in d.entries[:limit]:
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                if title and link:
                    items.append({"title": title, "link": link})
        except Exception:
            continue
    return items[:limit]
