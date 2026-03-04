import requests
from typing import List, Optional
from datetime import datetime, timedelta


# 常见英文技术词汇翻译映射
TECH_WORDS = {
    # 动词/动作
    "build": "构建",
    "create": "创建",
    "generate": "生成",
    "convert": "转换",
    "transform": "转换",
    "manage": "管理",
    "automate": "自动化",
    "deploy": "部署",
    "develop": "开发",
    "track": "追踪",
    "monitor": "监控",
    "analyze": "分析",
    "search": "搜索",
    "query": "查询",
    "render": "渲染",
    "sync": "同步",
    "fetch": "获取",
    "parse": "解析",
    "extract": "提取",
    "scrape": "抓取",
    "crawl": "爬取",
    # 名词
    "tool": "工具",
    "framework": "框架",
    "library": "库",
    "app": "应用",
    "application": "应用",
    "platform": "平台",
    "service": "服务",
    "api": "API",
    "cli": "命令行",
    "ui": "界面",
    "interface": "界面",
    "database": "数据库",
    "server": "服务器",
    "client": "客户端",
    "bot": "机器人",
    "agent": "智能体",
    "workflow": "工作流",
    "pipeline": "流水线",
    "dashboard": "仪表盘",
    "visualization": "可视化",
    "scraper": "爬虫",
    "crawler": "爬虫",
    "parser": "解析器",
    # 形容词
    "open source": "开源",
    "lightweight": "轻量级",
    "simple": "简单",
    "easy": "简易",
    "fast": "快速",
    "modern": "现代化",
    "powerful": "强大",
    "flexible": "灵活",
    "scalable": "可扩展",
    "real-time": "实时",
    "ai-powered": "AI驱动",
    "self-hosted": "自托管",
}


def translate_tech_desc(desc: str) -> str:
    """简单翻译技术描述"""
    if not desc:
        return "暂无描述"

    # 转换为小写进行匹配
    desc_lower = desc.lower()
    translated = desc

    # 替换常见词汇
    for en, cn in TECH_WORDS.items():
        if en in desc_lower:
            translated = translated.replace(en, cn).replace(en.capitalize(), cn)

    # 如果翻译后还是英文为主，返回简化版
    if len([c for c in translated if ord(c) < 128]) > len(translated) * 0.7:
        # 大部分是英文，提取关键词
        keywords = []
        for en, cn in TECH_WORDS.items():
            if en in desc_lower:
                keywords.append(cn)
        if keywords:
            return "、".join(keywords[:3]) + "相关项目"
        return "开源项目"

    return translated[:60]


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
            raw_desc = item.get("description", "") or "暂无描述"
            results.append({
                "name": item.get("full_name", ""),
                "url": item.get("html_url", ""),
                "description": translate_tech_desc(raw_desc),
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language") or "未知",
                "stars_today": item.get("stargazers_count", 0),
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
    desc = item.get("description", "暂无描述")
    if len(desc) > 30:
        desc = desc[:27] + "..."

    return f"⭐ {name} ({stars:,}⭐｜{language}) - {desc}"
