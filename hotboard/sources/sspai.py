from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class SspaieFetcher(BaseFetcher):
    platform = "sspai"
    platform_name = "少数派"
    icon = "📱"
    group = "tech"
    source_url = "https://sspai.com/hot"

    def fetch(self) -> list[HotItem]:
        url = "https://sspai.com/api/v1/article/tag/page/get"
        params = {
            "limit": 20,
            "offset": 0,
            "created_at": 0,
            "tag": "热门文章",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://sspai.com/hot",
        }

        try:
            r = self.http_get(url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
            return self._parse_articles(data)
        except Exception as e:
            print(f"少数派热门文章抓取失败，尝试备用接口: {e}")
            return self._fetch_recommend()

    def _fetch_recommend(self) -> list[HotItem]:
        """备用方案：推荐接口"""
        url = "https://sspai.com/api/v1/recommend/page/get"
        params = {"limit": 20, "offset": 0}
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://sspai.com/",
        }

        try:
            r = self.http_get(url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
            return self._parse_articles(data)
        except Exception as e:
            print(f"少数派推荐接口也失败: {e}")
            return []

    @staticmethod
    def _parse_articles(data: dict) -> list[HotItem]:
        """解析少数派文章列表"""
        items = []
        articles = data.get("data", [])

        for i, article in enumerate(articles):
            title = article.get("title", "")
            if not title:
                continue

            article_id = article.get("id", "")
            url = f"https://sspai.com/post/{article_id}" if article_id else ""

            # 热度：点赞数
            like_count = article.get("like_count", 0) or article.get("likes_count", 0)
            hot_value = f"♥ {like_count}" if like_count else ""

            # 分类：取 topic 或 tags
            topic = article.get("topic", {})
            category = ""
            if isinstance(topic, dict):
                category = topic.get("title", "")
            if not category:
                tags = article.get("tags", [])
                if tags:
                    category = tags[0] if isinstance(tags[0], str) else tags[0].get("title", "")

            # 作者
            author = article.get("author", {})
            author_name = author.get("nickname", "") if isinstance(author, dict) else ""
            if author_name and category:
                category = f"{category} · {author_name}"
            elif author_name:
                category = author_name

            items.append(HotItem(
                rank=i + 1,
                title=title,
                url=url,
                hot_value=hot_value,
                category=category,
            ))

        return items
