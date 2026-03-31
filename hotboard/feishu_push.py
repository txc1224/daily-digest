import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from hotboard.config import PLATFORMS, FEISHU_TOP_N
from hotboard.analyzer import analyze_cross_platform
from hotboard.app import build_health_overview, fetch_all_boards, get_status_snapshot
from sender import send_to_feishu


def build_hotboard_card(boards: dict) -> dict:
    """构建热榜飞书卡片"""
    elements = [
        {
            "tag": "markdown",
            "content": "📊 **全网热榜精选摘要**\n每个平台 Top 5 热门内容"
        },
        {"tag": "hr"}
    ]

    for platform, board in boards.items():
        conf = PLATFORMS.get(platform)
        if not conf:
            continue

        icon = board.get("icon", conf[1])
        name = board.get("platform_name", conf[0])
        items = board.get("items", [])[:FEISHU_TOP_N]

        if not items:
            continue

        lines = [f"**{icon} {name}**"]
        for item in items:
            title = item.get("title", "")
            url = item.get("url", "")
            hot = item.get("hot_value", "")
            rank = item.get("rank", 0)
            hot_suffix = f" ({hot})" if hot else ""
            if url:
                lines.append(f"{rank}. [{title}]({url}){hot_suffix}")
            else:
                lines.append(f"{rank}. {title}{hot_suffix}")

        elements.append({
            "tag": "markdown",
            "content": "\n".join(lines)
        })
        elements.append({"tag": "hr"})

    # 移除最后多余的 hr
    if elements and elements[-1].get("tag") == "hr":
        elements.pop()

    return {
        "header": {
            "title": {"tag": "plain_text", "content": "🔥 今日全网热榜"},
            "template": "red"
        },
        "elements": elements
    }


def build_hotboard_daily_brief_card(boards: dict, statuses: dict | None = None) -> dict:
    """构建更适合日常消费的 HotBoard 摘要卡片"""
    analysis = analyze_cross_platform(boards)
    cross_topics = analysis.get("cross_platform_topics", [])[:4]
    statuses = statuses or {}
    health = build_health_overview(statuses) if statuses else {
        "healthy_count": 0,
        "enabled_count": 0,
        "failing_count": 0,
        "stale_count": 0,
        "failing_platforms": [],
        "slow_platforms": [],
    }

    board_count = len([board for board in boards.values() if board.get("items")])
    top_signals = []
    for board in boards.values():
        items = board.get("items", [])
        if not items:
            continue
        top_item = items[0]
        top_signals.append({
            "platform_name": board.get("platform_name", ""),
            "title": top_item.get("title", ""),
            "rank": top_item.get("rank", 999),
            "hot_value": top_item.get("hot_value", ""),
        })
    top_signals.sort(key=lambda item: (item["rank"], item["platform_name"]))
    top_signals = top_signals[:3]

    elements = [
        {
            "tag": "markdown",
            "content": "📌 **HotBoard Daily Brief**\n先看高信号热点，再看平台精选和抓取状态",
        },
        {
            "tag": "markdown",
            "content": (
                f"**今日概览**\n"
                f"已汇总 {board_count} 个平台，跨平台热点 {len(cross_topics)} 个，"
                f"健康平台 {health.get('healthy_count', 0)}/{health.get('enabled_count', 0)}"
            ),
        },
        {"tag": "hr"},
    ]

    if top_signals:
        lines = ["**⚡ 即刻关注**"]
        for signal in top_signals:
            suffix = f" ({signal['hot_value']})" if signal["hot_value"] else ""
            lines.append(f"• **{signal['platform_name']}**: {signal['title']}{suffix}")
        elements.append({"tag": "markdown", "content": "\n".join(lines)})
        elements.append({"tag": "hr"})

    if cross_topics:
        lines = ["**🔥 跨平台热点**"]
        for topic in cross_topics:
            platforms = " / ".join(topic.get("platforms", [])[:3])
            summary = topic.get("summary") or topic.get("topic", "")
            lines.append(
                f"• **{topic.get('topic', '未命名话题')}** ({topic.get('platform_count', 0)} 平台, 热度 {topic.get('heat_score', 0)})\n"
                f"  {summary}\n"
                f"  来源: {platforms}"
            )
        elements.append({"tag": "markdown", "content": "\n".join(lines)})
        elements.append({"tag": "hr"})

    group_aliases = [
        ("tech", "💻 技术社区"),
        ("domestic", "🇨🇳 国内平台"),
        ("overseas", "🌍 海外平台"),
    ]
    for group_key, group_name in group_aliases:
        group_boards = [
            board for board in boards.values()
            if board.get("group") == group_key and board.get("items")
        ]
        if not group_boards:
            continue

        group_boards.sort(
            key=lambda board: (
                board.get("items", [{}])[0].get("rank", 999),
                -len(board.get("items", [])),
            )
        )
        lines = [f"**{group_name} 精选**"]
        for board in group_boards[:2]:
            top_item = board["items"][0]
            title = top_item.get("title", "")
            url = top_item.get("url", "")
            hot_value = top_item.get("hot_value", "")
            suffix = f" ({hot_value})" if hot_value else ""
            if url:
                lines.append(f"• **{board.get('platform_name', '')}**: [{title}]({url}){suffix}")
            else:
                lines.append(f"• **{board.get('platform_name', '')}**: {title}{suffix}")
        elements.append({"tag": "markdown", "content": "\n".join(lines)})
        elements.append({"tag": "hr"})

    failing_platforms = health.get("failing_platforms", [])[:5]
    if failing_platforms:
        lines = ["**⚠️ 抓取异常**"]
        for platform in failing_platforms:
            error = platform.get("last_error", "unknown error")
            lines.append(
                f"• **{platform.get('name', platform.get('platform', 'unknown'))}**: "
                f"连续失败 {platform.get('consecutive_failures', 0)} 次\n  {error}"
            )
        elements.append({"tag": "markdown", "content": "\n".join(lines)})
        elements.append({"tag": "hr"})
    elif health.get("enabled_count", 0):
        slow_platforms = health.get("slow_platforms", [])[:2]
        slow_text = ""
        if slow_platforms:
            slow_text = "；最慢平台 " + " / ".join(
                f"{platform.get('name', platform.get('platform', 'unknown'))} {platform.get('last_duration_ms', 0)}ms"
                for platform in slow_platforms
            )
        elements.append({
            "tag": "markdown",
            "content": (
                f"**✅ 抓取健康**\n"
                f"健康平台 {health.get('healthy_count', 0)}/{health.get('enabled_count', 0)}，"
                f"缓存过旧 {health.get('stale_count', 0)} 个{slow_text}"
            ),
        })
        elements.append({"tag": "hr"})

    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": "基于 HotBoard 实时抓取结果生成 · 适合快速扫一眼今天值得看的内容",
        }],
    })

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "📡 HotBoard 日摘要"},
            "template": "red",
        },
        "elements": elements,
    }


def push_hotboard_to_feishu():
    """抓取热榜并推送到飞书"""
    print("📡 正在抓取热榜数据...")
    boards = fetch_all_boards()
    if not boards:
        print("⚠️  无热榜数据，跳过推送")
        return

    print(f"✅ 获取到 {len(boards)} 个平台数据")
    card = build_hotboard_card(boards)
    send_to_feishu(card)
    print("📨 热榜推送成功 ✅")


def push_hotboard_daily_brief_to_feishu():
    """抓取热榜并推送更精简的日摘要"""
    print("📡 正在抓取 HotBoard 摘要数据...")
    boards = fetch_all_boards()
    if not boards:
        print("⚠️  无热榜数据，跳过推送")
        return

    statuses = get_status_snapshot()
    card = build_hotboard_daily_brief_card(boards, statuses)
    send_to_feishu(card)
    print("📨 HotBoard 日摘要推送成功 ✅")
