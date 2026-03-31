import os
import requests
from typing import List


# Product Hunt 常见词汇翻译
PH_WORDS = {
    # 动词
    "build": "构建",
    "create": "创建",
    "generate": "生成",
    "convert": "转换",
    "automate": "自动化",
    "manage": "管理",
    "track": "追踪",
    "organize": "整理",
    "schedule": "安排",
    "collaborate": "协作",
    "share": "分享",
    "discover": "发现",
    "explore": "探索",
    "learn": "学习",
    "teach": "教学",
    # 名词
    "app": "应用",
    "tool": "工具",
    "platform": "平台",
    "assistant": "助手",
    "bot": "机器人",
    "ai": "AI",
    "chrome extension": "浏览器插件",
    "widget": "小组件",
    "dashboard": "仪表盘",
    "template": "模板",
    "workflow": "工作流",
    "note": "笔记",
    "document": "文档",
    "meeting": "会议",
    "email": "邮件",
    "chat": "聊天",
    "search": "搜索",
    "analytics": "数据分析",
    # 形容词
    "free": "免费",
    "open source": "开源",
    "ai-powered": "AI驱动",
    "smart": "智能",
    "simple": "简单",
    "easy": "简易",
    "fast": "快速",
    "better": "更好的",
    "ultimate": "终极",
    "all-in-one": "一站式",
}


def translate_ph_tagline(tagline: str) -> str:
    """简单翻译 Product Hunt 标语"""
    if not tagline:
        return "新产品"

    tagline_lower = tagline.lower()

    # 提取关键词
    keywords = []
    for en, cn in PH_WORDS.items():
        if en in tagline_lower:
            keywords.append(cn)

    if keywords:
        return "、".join(keywords[:3]) + "工具"

    # 如果无法翻译，返回简化版
    if len(tagline) > 40:
        return tagline[:37] + "..."
    return tagline


def has_ph_token() -> bool:
    """检查是否有 Product Hunt Token"""
    return bool(os.environ.get("PRODUCT_HUNT_TOKEN", "").strip())


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
        token = os.environ.get("PRODUCT_HUNT_TOKEN", "").strip()

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

        errors = data.get("errors", [])
        if errors:
            raise RuntimeError(f"GraphQL errors: {errors}")

        posts = data.get("data", {}).get("posts", {}).get("edges", [])
        if not posts:
            print("  ⚠️  Product Hunt API 返回 0 条结果，切换到 RSS 备用方案")
            return fetch_product_hunt_fallback(limit)

        results = []

        for edge in posts:
            node = edge.get("node", {})
            topics = [
                t.get("node", {}).get("name", "")
                for t in node.get("topics", {}).get("edges", [])
            ]

            raw_tagline = node.get("tagline", "")
            results.append({
                "name": node.get("name", ""),
                "tagline": translate_ph_tagline(raw_tagline),
                "url": node.get("url", ""),
                "votes": node.get("votesCount", 0),
                "topics": topics[:3],
            })

        print(f"  ✅ Product Hunt API 返回 {len(results)} 条")
        return results

    except Exception as e:
        print(f"  ⚠️  Product Hunt API 失败，使用 RSS 备用方案: {e}")
        return fetch_product_hunt_fallback(limit)


def fetch_product_hunt_fallback(limit: int = 10) -> List[dict]:
    """
    Product Hunt 的备用方案 - 获取 featured 产品列表
    通过 RSS 或公开 API 获取
    """
    url = "https://www.producthunt.com/feed"

    try:
        # 使用 RSS 作为备用
        import feedparser

        d = feedparser.parse(url)
        if getattr(d, "bozo", 0):
            print(f"  ⚠️  Product Hunt RSS 解析异常: {getattr(d, 'bozo_exception', 'unknown error')}")

        entries = list(getattr(d, "entries", []))
        if not entries:
            print(f"  ⚠️  Product Hunt RSS 返回 0 条结果: {url}")
            return []

        results = []

        for entry in entries[:limit]:
            raw_desc = entry.get("description", "")
            results.append({
                "name": entry.get("title", ""),
                "tagline": translate_ph_tagline(raw_desc),
                "url": entry.get("link", ""),
                "votes": 0,
                "topics": [],
            })

        print(f"  ✅ Product Hunt RSS 返回 {len(results)} 条")
        return results

    except Exception as e:
        print(f"  ⚠️  Product Hunt RSS fallback 失败: {e}")
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
