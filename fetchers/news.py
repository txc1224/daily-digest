import feedparser
from typing import List


RSS_FEEDS = {
    "时事": [
        "https://www.zaobao.com/rss/realtime/china",       # 联合早报·中国
        "https://rsshub.app/xinhua/world",                  # 新华社·国际
    ],
    "科技/AI": [
        "https://36kr.com/feed",                           # 36氪
        "https://hnrss.org/frontpage",                     # Hacker News 首页
    ],
}


def fetch_news(feed_urls: List[str], limit: int = 5) -> List[dict]:
    """从多个 RSS 源抓取新闻，合并后取前 limit 条"""
    items = []
    for url in feed_urls:
        try:
            d = feedparser.parse(url)
            for entry in d.entries[:limit]:
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                if title and link:
                    items.append({"title": title, "link": link})
        except Exception:
            # 单个源失败不影响整体
            continue
    return items[:limit]


def fetch_all_news() -> dict:
    """获取所有类别的新闻"""
    return {category: fetch_news(urls) for category, urls in RSS_FEEDS.items()}
