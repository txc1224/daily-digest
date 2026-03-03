from datetime import datetime
from typing import List, Dict, Optional


WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def build_card(
    weather: dict,
    all_news: dict,
    finance_news: list,
    stocks: List[dict],
    commodities: List[dict],
    forex_rates: Optional[Dict] = None,
    bonds_vix: Optional[Dict] = None,
    forex_analysis: str = "",
    bond_vix_analysis: str = "",
    github_trending: Optional[List[dict]] = None,
    product_hunt: Optional[List[dict]] = None,
    hot_topics: Optional[List[dict]] = None,
    sentiment_result: Optional[Dict] = None
) -> dict:
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

    # ── 汇率 ──────────────────────────────────────────────────
    if forex_rates and any(forex_rates.values()):
        forex_lines = []
        for pair, rate in forex_rates.items():
            if rate:
                emoji = "📈" if rate.get("change", 0) >= 0 else "📉"
                sign = "+" if rate.get("change", 0) >= 0 else ""
                forex_lines.append(
                    f"{emoji} **{pair}**: {rate['rate']} "
                    f"({sign}{rate.get('change_pct', 0)}%)"
                )
        forex_text = "\n".join(forex_lines)
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"💱 **汇率**\n{forex_text}",
            }
        })

        # 汇率解读
        if forex_analysis:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"💡 **解读**: {forex_analysis}"
                }
            })
        elements.append({"tag": "hr"})

    # ── 国债收益率与VIX ────────────────────────────────────────
    if bonds_vix and any(bonds_vix.values()):
        bond_vix_lines = []

        if bonds_vix.get("treasury_10y"):
            t = bonds_vix["treasury_10y"]
            emoji = "📈" if t.get("change", 0) >= 0 else "📉"
            sign = "+" if t.get("change", 0) >= 0 else ""
            bond_vix_lines.append(
                f"{emoji} **{t['name']}**: {t['yield']}% "
                f"({sign}{t.get('change_pct', 0)}%)"
            )

        if bonds_vix.get("vix"):
            v = bonds_vix["vix"]
            emoji = "😱" if v["value"] > 30 else "😰" if v["value"] > 20 else "😐" if v["value"] > 15 else "😊"
            sign = "+" if v.get("change", 0) >= 0 else ""
            bond_vix_lines.append(
                f"{emoji} **{v['name']}**: {v['value']} "
                f"({sign}{v.get('change_pct', 0)}%)"
            )

        bond_vix_text = "\n".join(bond_vix_lines)
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"📈 **债市与恐慌指数**\n{bond_vix_text}",
            }
        })

        # 债券/VIX解读
        if bond_vix_analysis:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"💡 **解读**: {bond_vix_analysis}"
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

    # ── 市场情绪 ──────────────────────────────────────────────
    if sentiment_result:
        sentiment_emoji = {
            "positive": "🟢",
            "negative": "🔴",
            "neutral": "⚪"
        }.get(sentiment_result.get("overall", "neutral"), "⚪")

        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"{sentiment_emoji} **市场情绪**: {sentiment_result.get('summary', '')}"
            }
        })
        elements.append({"tag": "hr"})

    # ── 热点话题 ──────────────────────────────────────────────
    if hot_topics:
        hot_lines = []
        for i, topic in enumerate(hot_topics[:3], 1):
            topic_name = topic['topic']
            count = topic['count']
            hot_lines.append(f"🔥 **{topic_name}** ({count}篇相关)")

            # 显示相关新闻标题（带摘要）
            for news in topic['related_news'][:2]:
                title = news.get('title', '')
                summary = news.get('summary', '')
                if summary:
                    hot_lines.append(f"   • [{title}]({news.get('link', '')})\n     💡 {summary}")
                else:
                    hot_lines.append(f"   • [{title}]({news.get('link', '')})")

        hot_text = "\n".join(hot_lines)
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"🔥 **今日热点**\n{hot_text}",
            }
        })
        elements.append({"tag": "hr"})

    # ── 新闻各分类（带摘要）─────────────────────────────────────
    emoji_map = {"时事": "📰", "科技/AI": "🤖", "开发者": "💻"}
    for category, items in all_news.items():
        if not items:
            continue
        emoji = emoji_map.get(category, "📌")
        lines = []
        for item in items:
            title = item.get('title', '')
            link = item.get('link', '')
            summary = item.get('summary', '')

            if summary:
                lines.append(f"• [{title}]({link})\n  💡 {summary}")
            else:
                lines.append(f"• [{title}]({link})")

        news_text = "\n".join(lines)
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"{emoji} **{category}**\n{news_text}",
            }
        })
        elements.append({"tag": "hr"})

    # ── 财经新闻（带摘要）────────────────────────────────────────
    if finance_news:
        lines = []
        for item in finance_news:
            title = item.get('title', '')
            link = item.get('link', '')
            summary = item.get('summary', '')
            sentiment_emoji = item.get('sentiment_emoji', '')

            if summary:
                lines.append(f"{sentiment_emoji} [{title}]({link})\n  💡 {summary}")
            else:
                lines.append(f"{sentiment_emoji} [{title}]({link})")

        finance_text = "\n".join(lines)
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"💹 **财经**\n{finance_text}",
            }
        })
        elements.append({"tag": "hr"})

    # ── GitHub Trending ────────────────────────────────────────
    if github_trending:
        gh_lines = []
        for item in github_trending[:10]:
            name = item.get('name', '')
            url = item.get('url', '')
            stars = item.get('stars', 0)
            language = item.get('language', '未知')
            desc = item.get('description', '')[:40]
            if len(desc) == 40:
                desc += "..."

            gh_lines.append(f"⭐ [{name}]({url}) ({stars:,}⭐｜{language})\n   {desc}")

        gh_text = "\n".join(gh_lines)
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"💻 **GitHub 热门**\n{gh_text}",
            }
        })
        elements.append({"tag": "hr"})

    # ── Product Hunt ───────────────────────────────────────────
    if product_hunt:
        ph_lines = []
        for item in product_hunt[:10]:
            name = item.get('name', '')
            url = item.get('url', '')
            tagline = item.get('tagline', '')[:50]
            if len(tagline) == 50:
                tagline += "..."
            votes = item.get('votes', 0)

            if votes > 0:
                ph_lines.append(f"🚀 [{name}]({url}) (↑{votes})\n   {tagline}")
            else:
                ph_lines.append(f"🚀 [{name}]({url})\n   {tagline}")

        ph_text = "\n".join(ph_lines)
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"🚀 **Product Hunt 热门**\n{ph_text}",
            }
        })
        elements.append({"tag": "hr"})

    # ── 底部注脚 ──────────────────────────────────────────────
    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": "由 GitHub Actions 自动推送 · 每天 08:00 · 含 AI 摘要与情感分析"
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
