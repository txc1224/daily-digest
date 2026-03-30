import requests
from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class WeixinFetcher(BaseFetcher):
    """澎湃新闻热榜（替代微信热搜，数据更稳定）"""
    platform = "thepaper"
    platform_name = "澎湃热榜"
    icon = "📰"
    group = "domestic"
    source_url = "https://www.thepaper.cn/"

    def fetch(self) -> list[HotItem]:
        url = "https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = self.http_get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

        hot_news = data.get("data", {}).get("hotNews", [])
        items = []
        for i, entry in enumerate(hot_news[:30]):
            title = entry.get("name", "")
            if not title:
                continue
            cont_id = entry.get("contId", "")
            praise = entry.get("praiseTimes", "0")
            comments = entry.get("interactionNum", "0")
            node = entry.get("nodeInfo", {}).get("name", "")

            items.append(HotItem(
                rank=i + 1,
                title=title,
                url=f"https://www.thepaper.cn/newsDetail_forward_{cont_id}" if cont_id else "",
                hot_value=f"{praise} 赞" if praise and praise != "0" else "",
                category=node,
            ))
        return items
