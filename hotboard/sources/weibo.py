import requests
from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class WeiboFetcher(BaseFetcher):
    platform = "weibo"
    platform_name = "微博热搜"
    icon = "🔥"
    group = "domestic"
    source_url = "https://s.weibo.com/top/summary"

    def fetch(self) -> list[HotItem]:
        url = "https://weibo.com/ajax/statuses/hot_band"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://weibo.com/",
        }
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        items = []
        band_list = data.get("data", {}).get("band_list", [])
        for i, entry in enumerate(band_list[:30]):
            word = entry.get("word", "")
            # word_scheme 格式为 #xxx#，从中提取
            if not word:
                scheme = entry.get("word_scheme", "")
                word = scheme.strip("#")
            if not word:
                continue

            raw_hot = entry.get("raw_hot", 0)
            hot_str = self._format_hot(raw_hot)
            label = entry.get("label_name", "")
            category = label if label else entry.get("field_tag", "")

            items.append(HotItem(
                rank=i + 1,
                title=word,
                url=f"https://s.weibo.com/weibo?q=%23{word}%23",
                hot_value=hot_str,
                category=category,
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
