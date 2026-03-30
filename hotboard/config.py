import os

CACHE_DIR = "cache"
CACHE_TTL_SECONDS = 300  # 5 minutes

REFRESH_INTERVAL_MINUTES = 5

# 代理配置（用于访问海外平台）
# 支持环境变量 HOTBOARD_PROXY 或 ALL_PROXY 或 HTTPS_PROXY
PROXY_URL = os.environ.get("HOTBOARD_PROXY") or os.environ.get("ALL_PROXY") or os.environ.get("HTTPS_PROXY") or ""

# 需要代理才能访问的平台
PROXY_PLATFORMS = {"hackernews", "v2ex", "reddit", "twitter", "tiktok", "instagram", "linkedin", "producthunt", "google_trends"}

FEISHU_PUSH_HOUR = 9
FEISHU_PUSH_MINUTE = 0
FEISHU_TOP_N = 5  # 飞书推送每平台 Top N 条

# 平台配置：key -> (显示名, 图标, 分组, 是否启用)
PLATFORMS = {
    "weibo":       ("微博热搜",    "🔥", "domestic", True),
    "zhihu":       ("知乎热榜",    "💡", "domestic", True),
    "baidu":       ("百度热搜",    "🔍", "domestic", True),
    "bilibili":    ("B站热门",     "📺", "domestic", True),
    "hackernews":  ("HackerNews", "🟠", "tech",     True),
    "github":      ("GitHub Trending", "🐙", "tech", True),
    "v2ex":        ("V2EX",       "💬", "tech",     True),
    "reddit":      ("Reddit",     "🤖", "overseas", True),
    # Phase 2
    "douyin":      ("抖音热榜",    "🎵", "domestic", False),
    "xiaohongshu": ("小红书热门",  "📕", "domestic", False),
    "twitter":     ("Twitter/X",  "🐦", "overseas", False),
    "producthunt": ("Product Hunt", "🚀", "tech",   False),
    "google_trends": ("Google Trends", "📊", "seo", False),
    # Phase 3
    "tiktok":      ("TikTok",     "🎶", "overseas", False),
    "instagram":   ("Instagram",  "📷", "overseas", False),
    "linkedin":    ("LinkedIn",   "💼", "overseas", False),
}

GROUP_NAMES = {
    "domestic": "🇨🇳 国内平台",
    "tech": "💻 技术社区",
    "overseas": "🌍 海外平台",
    "seo": "🔍 搜索热词",
}

GROUP_ORDER = ["domestic", "tech", "overseas", "seo"]
