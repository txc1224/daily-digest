import requests
from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class Kr36Fetcher(BaseFetcher):
    platform = "kr36"
    platform_name = "36氪热榜"
    icon = "💹"
    group = "tech"
    source_url = "https://36kr.com/hot-list"

    def fetch(self) -> list[HotItem]:
        url = "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
        }
        payload = {
            "partner_id": "wap",
            "param": {"siteId": 1, "platformId": 2},
        }
        try:
            kwargs = {"timeout": 10}
            proxies = self.proxies
            if proxies:
                kwargs["proxies"] = proxies
            r = requests.post(url, json=payload, headers=headers, **kwargs)
            r.raise_for_status()
            data = r.json()
        except Exception:
            return []

        items = []
        hot_list = (
            data.get("data", {})
            .get("hotRankList", [])
        )
        for i, entry in enumerate(hot_list[:30]):
            template = entry.get("templateMaterial", {})
            title = template.get("widgetTitle", "")
            if not title:
                continue

            item_id = template.get("itemId", "")
            article_url = (
                f"https://36kr.com/p/{item_id}"
                if item_id
                else self.source_url
            )
            hot_value = template.get("statRead", "")
            cover = template.get("widgetImage", "")

            items.append(HotItem(
                rank=i + 1,
                title=title,
                url=article_url,
                hot_value=self._format_hot(hot_value),
                cover_img=cover,
            ))
        return items

    @staticmethod
    def _format_hot(num) -> str:
        if not num:
            return ""
        try:
            num = int(num)
        except (ValueError, TypeError):
            return str(num)
        if num >= 100_000_000:
            return f"{num / 100_000_000:.1f}亿"
        if num >= 10_000:
            return f"{num / 10_000:.1f}万"
        return str(num)
