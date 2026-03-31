from concurrent.futures import ThreadPoolExecutor, as_completed
from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class HackerNewsFetcher(BaseFetcher):
    platform = "hackernews"
    platform_name = "HackerNews"
    icon = "🟠"
    group = "tech"
    source_url = "https://news.ycombinator.com/"

    def fetch(self) -> list[HotItem]:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        r = self.http_get(url)
        r.raise_for_status()
        story_ids = r.json()[:30]

        # 并发获取详情（共享 proxies 配置）
        proxies = self.proxies
        stories = {}
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(self._fetch_story, sid, proxies): sid for sid in story_ids}
            for future in as_completed(futures, timeout=20):
                sid = futures[future]
                try:
                    story = future.result()
                    if story:
                        stories[sid] = story
                except Exception:
                    pass

        items = []
        for sid in story_ids:
            story = stories.get(sid)
            if not story:
                continue
            items.append(HotItem(
                rank=len(items) + 1,
                title=story.get("title", ""),
                url=story.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                hot_value=f"{story.get('score', 0)} points",
                category=f"{story.get('descendants', 0)} comments",
            ))
        return items

    @staticmethod
    def _fetch_story(sid: int, proxies: dict | None = None) -> dict | None:
        import requests
        try:
            r = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                timeout=5,
                proxies=proxies,
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            return None
