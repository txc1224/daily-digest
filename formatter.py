from datetime import datetime
from typing import List


WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def build_card(weather: dict, all_news: dict, finance_news: list, stocks: List[dict], commodities: List[dict]) -> dict:
    """
    组装飞书交互卡片（card JSON）。
    使用 div + markdown 标签拼接内容，兼容飞书机器人卡片格式。
    """
    now = datetime.now()
    weekday = WEEKDAY_CN[now.weekday()]
    today = now.strftime(f"%Y-%m-%d {weekday}")

    elements = []

    # ── 标题 ──────────────────────────────────────────────────
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**🗓 每日简报 · {today}**",
        }
    })
    elements.append({"tag": "hr"})

    # ── 天气 ──────────────────────────────────────────────────
    w = weather
    weather_text = (
        f"🌤 **天气**：{w.get('city', 'Beijing')}  {w['text']}  {w['temp']}°C（体感 {w['feelsLike']}°C）\n"
        f"💨 {w['windDir']} {w['windScale']}　💧 湿度 {w['humidity']}%"
    )
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": weather_text}
    })
    elements.append({"tag": "hr"})

    # ── 股市行情 ──────────────────────────────────────────────
    if stocks:
        stock_lines = []
        for stock in stocks:
            emoji = "📈" if stock["change"] >= 0 else "📉"
            sign = "+" if stock["change"] >= 0 else ""
            stock_lines.append(
                f"{emoji} **{stock['name']}**: {stock['price']} "
                f"({sign}{stock['change']}, {sign}{stock['change_pct']}%)"
            )
        stock_text = "\n".join(stock_lines)
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"📊 **全球股市**\n{stock_text}",
            }
        })
        elements.append({"tag": "hr"})

    # ── 大宗商品 ──────────────────────────────────────────────
    if commodities:
        comm_lines = []
        for comm in commodities:
            emoji = "📈" if comm["change"] >= 0 else "📉"
            sign = "+" if comm["change"] >= 0 else ""
            unit = "美元/桶" if "原油" in comm["name"] else "美元/盎司"
            comm_lines.append(
                f"{emoji} **{comm['name']}**: {comm['price']} "
                f"({sign}{comm['change_pct']}%)"
            )
        comm_text = "\n".join(comm_lines)
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"🛢 **大宗商品**\n{comm_text}",
            }
        })
        elements.append({"tag": "hr"})

    # ── 新闻各分类 ────────────────────────────────────────────
    emoji_map = {"时事": "📰", "科技/AI": "🤖"}
    for category, items in all_news.items():
        if not items:
            continue
        emoji = emoji_map.get(category, "📌")
        lines = "\n".join(
            f"• [{item['title']}]({item['link']})" for item in items
        )
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"{emoji} **{category}**\n{lines}",
            }
        })
        elements.append({"tag": "hr"})

    # ── 财经 ──────────────────────────────────────────────────
    if finance_news:
        lines = "\n".join(
            f"• [{item['title']}]({item['link']})" for item in finance_news
        )
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"💹 **财经**\n{lines}",
            }
        })
        elements.append({"tag": "hr"})

    # ── 底部注脚 ──────────────────────────────────────────────
    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": "由 GitHub Actions 自动推送 · 每天 08:00"
        }]
    })

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "📋 每日简报"},
            "template": "blue",
        },
        "elements": elements,
    }
