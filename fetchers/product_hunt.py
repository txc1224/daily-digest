import os
import requests
from typing import List, Optional
from datetime import datetime


def has_ph_token() -> bool:
    """检查是否有 Product Hunt Token"""
    return bool(os.environ.get("PRODUCT_HUNT_TOKEN", ""))


def fetch_product_hunt_trending(limit: int = 10) -> List[dict]:
    """
    获取 Product Hunt 今日热门产品。
    使用 Product Hunt API 获取今日热门产品列表。

    注意：Product Hunt 需要 API Token，如果不可用则自动使用 RSS 备用方案
    """
    # 如果没有 Token，直接使用备用方案
    if not has_ph_token():
        print("  ℹ️  未检测到 PRODUCT_HUNT_TOKEN，使用 RSS 备用方案")
        return fetch_product_hunt_fallback(limit)

    try:
        # Product Hunt GraphQL API
        url = "https://api.producthunt.com/v2/api/graphql"
        token = os.environ.get("PRODUCT_HUNT_TOKEN", "")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # GraphQL 查询
        query = """
        {
          posts(first: %d, order: RANKING) {
            edges {
              node {
                id
                name
                tagline
                url
                votesCount
                thumbnail {
                  url
                }
                topics {
                  edges {
                    node {
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """ % limit

        r = requests.post(
            url,
            headers=headers,
            json={"query": query},
            timeout=15
        )
        r.raise_for_status()
        data = r.json()

        posts = data.get("data", {}).get("posts", {}).get("edges", [])
        results = []

        for edge in posts:
            node = edge.get("node", {})
            topics = [
                t.get("node", {}).get("name", "")
                for t in node.get("topics", {}).get("edges", [])
            ]

            results.append({
                "name": node.get("name", ""),
                "tagline": node.get("tagline", ""),
                "url": node.get("url", ""),
                "votes": node.get("votesCount", 0),
                "topics": topics[:3],  # 只取前3个话题
            })

        return results

    except Exception as e:
        print(f"Product Hunt API 失败，使用 RSS 备用方案: {e}")
        return fetch_product_hunt_fallback(limit)


def fetch_product_hunt_fallback(limit: int = 10) -> List[dict]:
    """
    Product Hunt 的备用方案 - 获取 featured 产品列表
    通过 RSS 或公开 API 获取
    """
    try:
        # 使用 RSS 作为备用
        import feedparser

        # Product Hunt 有 RSS feed，虽然不是实时的但可用
        url = "https://www.producthunt.com/feed"

        d = feedparser.parse(url)
        results = []

        for entry in d.entries[:limit]:
            results.append({
                "name": entry.get("title", ""),
                "tagline": entry.get("description", "")[:100],
                "url": entry.get("link", ""),
                "votes": 0,  # RSS 不包含票数
                "topics": [],
            })

        return results

    except Exception as e:
        print(f"Product Hunt fallback fetch failed: {e}")
        return []


def format_ph_item(item: dict) -> str:
    """格式化单个 Product Hunt 产品为易读字符串"""
    name = item.get("name", "")
    tagline = item.get("tagline", "")[:60]
    if len(tagline) == 60:
        tagline += "..."
    votes = item.get("votes", 0)

    if votes > 0:
        return f"🚀 {name} (↑{votes}) - {tagline}"
    else:
        return f"🚀 {name} - {tagline}"
