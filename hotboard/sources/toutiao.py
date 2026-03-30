from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class ToutiaoFetcher(BaseFetcher):
    platform = "toutiao"
    platform_name = "今日头条"
    icon = "📰"
    group = "domestic"
    source_url = "https://www.toutiao.com"

    def fetch(self) -> list[HotItem]:
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
        try:
            r = self.http_get(url, headers=headers)
            r.raise_for_status()
            data = r.json()
        except Exception:
            return []

        items = []
        entries = data.get("data", [])
        for i, entry in enumerate(entries[:30]):
            title = entry.get("Title", "")
            if not title:
                continue

            hot_value = entry.get("HotValue", "")
            entry_url = entry.get("Url", "")

            items.append(HotItem(
                rank=i + 1,
                title=title,
                url=entry_url,
                hot_value=self._format_hot(hot_value),
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
