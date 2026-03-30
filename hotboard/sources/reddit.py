from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class RedditFetcher(BaseFetcher):
    platform = "reddit"
    platform_name = "Reddit"
    icon = "🤖"
    group = "overseas"
    source_url = "https://www.reddit.com/r/popular/"

    def fetch(self) -> list[HotItem]:
        url = "https://old.reddit.com/r/popular/.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; HotBoard/1.0; +https://github.com/daily-digest)",
        }
        params = {"limit": 30}
        r = self.http_get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        items = []
        children = data.get("data", {}).get("children", [])
        for i, child in enumerate(children):
            post = child.get("data", {})
            title = post.get("title", "")
            permalink = post.get("permalink", "")
            ups = post.get("ups", 0)
            subreddit = post.get("subreddit", "")
            num_comments = post.get("num_comments", 0)

            items.append(HotItem(
                rank=i + 1,
                title=title,
                url=f"https://www.reddit.com{permalink}" if permalink else "",
                hot_value=self._format_ups(ups),
                category=f"r/{subreddit} · {num_comments} comments",
            ))
        return items

    @staticmethod
    def _format_ups(num) -> str:
        if num >= 1000:
            return f"{num / 1000:.1f}k upvotes"
        return f"{num} upvotes"
