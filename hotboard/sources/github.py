import sys
import os

# 允许导入项目根目录的 fetchers 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem
from fetchers.github_trending import fetch_github_trending


class GitHubFetcher(BaseFetcher):
    platform = "github"
    platform_name = "GitHub Trending"
    icon = "🐙"
    group = "tech"
    source_url = "https://github.com/trending"

    def fetch(self) -> list[HotItem]:
        repos = fetch_github_trending(limit=20)
        items = []
        for i, repo in enumerate(repos):
            name = repo.get("name", "")
            stars = repo.get("stars", 0)
            lang = repo.get("language", "")
            desc = repo.get("description", "")

            items.append(HotItem(
                rank=i + 1,
                title=name,
                url=repo.get("url", f"https://github.com/{name}"),
                hot_value=f"⭐ {stars:,}",
                category=f"{lang} · {desc[:60]}" if desc else lang,
            ))
        return items
