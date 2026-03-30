import requests
from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class ZhihuFetcher(BaseFetcher):
    platform = "zhihu"
    platform_name = "知乎热榜"
    icon = "💡"
    group = "domestic"
    source_url = "https://www.zhihu.com/hot"

    def fetch(self) -> list[HotItem]:
        url = "https://api.zhihu.com/topstory/hot-lists/total"
        headers = {
            "User-Agent": "osee2unifiedRel498/2.27.0 Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
            "Accept": "application/json",
            "x-api-version": "3.0.76",
        }
        params = {"limit": 30}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        items = []
        for i, entry in enumerate(data.get("data", [])):
            target = entry.get("target", {})
            # 新版 API: title_area.text
            title = target.get("title_area", {}).get("text", "")
            hot_value = target.get("metrics_area", {}).get("text", "")
            link = target.get("link", {}).get("url", "")
            excerpt = target.get("excerpt_area", {}).get("text", "")
            cover = target.get("image_area", {}).get("url", "")

            items.append(HotItem(
                rank=i + 1,
                title=title,
                url=link,
                hot_value=hot_value,
                category=excerpt[:60] if excerpt else "",
                cover_img=cover,
            ))
        return items
