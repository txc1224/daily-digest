import feedparser
from typing import List


FINANCE_FEEDS = [
    "http://feed.eastmoney.com/roll_yw.xml",   # 东方财富·要闻
    "https://rsshub.app/gelonghui/home",        # 格隆汇
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
