import requests
from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class BilibiliFetcher(BaseFetcher):
    platform = "bilibili"
    platform_name = "B站热门"
    icon = "📺"
    group = "domestic"
    source_url = "https://www.bilibili.com/v/popular/all"

    def fetch(self) -> list[HotItem]:
        url = "https://api.bilibili.com/x/web-interface/popular"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }
        params = {"ps": 30, "pn": 1}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        items = []
        for i, entry in enumerate(data.get("data", {}).get("list", [])):
            title = entry.get("title", "")
            bvid = entry.get("bvid", "")
            stat = entry.get("stat", {})
            view = stat.get("view", 0)
            pic = entry.get("pic", "")
            owner = entry.get("owner", {}).get("name", "")

            items.append(HotItem(
                rank=i + 1,
                title=title,
                url=f"https://www.bilibili.com/video/{bvid}" if bvid else "",
                hot_value=self._format_view(view),
                category=f"UP: {owner}" if owner else "",
                cover_img=pic,
            ))
        return items

    @staticmethod
    def _format_view(num) -> str:
        if num >= 100_000_000:
            return f"{num / 100_000_000:.1f}亿播放"
        if num >= 10_000:
            return f"{num / 10_000:.1f}万播放"
        return f"{num}播放"
