from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class V2exFetcher(BaseFetcher):
    platform = "v2ex"
    platform_name = "V2EX"
    icon = "💬"
    group = "tech"
    source_url = "https://www.v2ex.com/?tab=hot"

    def fetch(self) -> list[HotItem]:
        url = "https://www.v2ex.com/api/topics/hot.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }
        r = self.http_get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

        items = []
        for i, topic in enumerate(data[:30]):
            title = topic.get("title", "")
            topic_id = topic.get("id", "")
            replies = topic.get("replies", 0)
            node = topic.get("node", {}).get("title", "")

            items.append(HotItem(
                rank=i + 1,
                title=title,
                url=f"https://www.v2ex.com/t/{topic_id}" if topic_id else "",
                hot_value=f"{replies} 回复",
                category=node,
            ))
        return items
