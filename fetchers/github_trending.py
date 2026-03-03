import requests
from typing import List, Optional
from datetime import datetime, timedelta


def fetch_github_trending(limit: int = 10) -> List[dict]:
    """
    获取 GitHub Trending 热门仓库。
    使用 GitHub API 搜索最近创建且有大量 star 的仓库。
    """
    try:
        # 获取最近一周创建的热门仓库
        # 使用搜索API按stars排序
        one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        url = "https://api.github.com/search/repositories"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Daily-Digest-Bot/1.0"
        }
        params = {
            "q": f"created:>{one_week_ago}",
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }

        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        items = data.get("items", [])
        results = []

        for item in items:
            results.append({
                "name": item.get("full_name", ""),
                "url": item.get("html_url", ""),
                "description": item.get("description", "") or "暂无描述",
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language") or "未知",
                "stars_today": item.get("stargazers_count", 0),  # 使用总star数代替
            })

        return results

    except Exception as e:
        print(f"GitHub trending fetch failed: {e}")
        return []


def format_github_item(item: dict) -> str:
    """格式化单个 GitHub 项目为易读字符串"""
    name = item.get("name", "")
    stars = item.get("stars", 0)
    language = item.get("language", "未知")
    desc = item.get("description", "")[:50]  # 截断描述
    if len(desc) == 50:
        desc += "..."

    return f"⭐ {name} ({stars:,}⭐｜{language}) - {desc}"
