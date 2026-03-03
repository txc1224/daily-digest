import feedparser
from typing import List


# 全部使用境外服务器可正常访问的 RSS 源
RSS_FEEDS = {
    "时事": [
        "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml",   # BBC 中文
        "https://rthk9.rthk.hk/rthk/news/rss/c_expressnews_clocal.xml",  # 香港电台
    ],
    "科技/AI": [
        "https://hnrss.org/frontpage",                       # Hacker News
        "https://www.technologyreview.com/feed/",            # MIT Tech Review
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
            continue
    return items[:limit]


def fetch_all_news() -> dict:
    """获取所有类别的新闻"""
    return {category: fetch_news(urls) for category, urls in RSS_FEEDS.items()}
