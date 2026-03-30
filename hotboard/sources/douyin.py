from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class DouyinFetcher(BaseFetcher):
    platform = "douyin"
    platform_name = "抖音热榜"
    icon = "🎵"
    group = "domestic"
    source_url = "https://www.douyin.com/hot"

    def fetch(self) -> list[HotItem]:
        url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://www.douyin.com/",
        }
        try:
            r = self.http_get(url, headers=headers)
            r.raise_for_status()
            data = r.json()
        except Exception:
            return []

        items = []
        word_list = data.get("data", {}).get("word_list", [])
        for i, entry in enumerate(word_list[:30]):
            word = entry.get("word", "")
            if not word:
                continue

            hot_value = entry.get("hot_value", 0)
            sentence_id = entry.get("sentence_id", "")
            event_url = (
                f"https://www.douyin.com/hot/{sentence_id}"
                if sentence_id
                else self.source_url
            )

            items.append(HotItem(
                rank=i + 1,
                title=word,
                url=event_url,
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
