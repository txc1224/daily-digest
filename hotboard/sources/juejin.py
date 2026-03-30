import requests as _requests
from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class JuejinFetcher(BaseFetcher):
    platform = "juejin"
    platform_name = "掘金热门"
    icon = "💎"
    group = "tech"
    source_url = "https://juejin.cn/"

    def fetch(self) -> list[HotItem]:
        url = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"
        payload = {
            "id_type": 2,
            "sort_type": 3,
            "cate_id": "6809637767543259144",
            "cursor": "0",
            "limit": 20,
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
        }
        r = _requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        items = []
        for i, entry in enumerate(data.get("data", [])):
            info = entry.get("item_info", {}).get("article_info", {})
            title = info.get("title", "")
            if not title:
                continue
            article_id = info.get("article_id", "")
            digg = info.get("digg_count", 0)
            view = info.get("view_count", 0)
            category = entry.get("item_info", {}).get("category", {}).get("category_name", "")

            items.append(HotItem(
                rank=i + 1,
                title=title,
                url=f"https://juejin.cn/post/{article_id}" if article_id else "",
                hot_value=f"{digg} 赞 · {view} 阅读",
                category=category,
            ))
        return items
