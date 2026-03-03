import feedparser
from typing import List


# 全部使用境外服务器可正常访问的 RSS 源
RSS_FEEDS = {
    "时事": [
        "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml",             # BBC 中文
        "https://rss.dw.com/rdf/rss-chi-all",                          # 德国之声中文
        "https://feeds.reuters.com/reuters/topNews",                    # 路透社头条
    ],
    "科技/AI": [
        "https://hnrss.org/frontpage",                                  # Hacker News
        "https://www.theverge.com/rss/index.xml",                      # The Verge
        "https://techcrunch.com/feed/",                                 # TechCrunch
        "https://www.technologyreview.com/feed/",                       # MIT Tech Review
    ],
    "开发者": [
        "https://dev.to/feed",                                          # DEV Community
        "https://www.smashingmagazine.com/feed/",                       # Smashing Magazine
        "https://css-tricks.com/feed/",                                 # CSS-Tricks
    ],
}


def fetch_news(feed_urls: List[str], limit: int = 10) -> List[dict]:
    """从多个 RSS 源抓取新闻，去重后取前 limit 条"""
    items = []
    seen_titles = set()
    for url in feed_urls:
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


def fetch_all_news() -> dict:
    """获取所有类别的新闻"""
    return {category: fetch_news(urls) for category, urls in RSS_FEEDS.items()}
