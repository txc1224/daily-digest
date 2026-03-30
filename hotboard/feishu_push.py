import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from hotboard.config import PLATFORMS, FEISHU_TOP_N
from hotboard.app import fetch_all_boards
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
