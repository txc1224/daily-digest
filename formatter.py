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
            related_news = topic.get('related_news', [])
            display_count = min(len(related_news), count)
            hot_lines.append(f"🔥 **{topic_name}** ({count}篇相关)")

            # 显示相关新闻标题（带摘要），最多显示3条
            for news in related_news[:3]:
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


def build_stock_card(
    title: str,
    focus_stock: Optional[dict] = None,
    us_stocks: Optional[List[dict]] = None,
    stocks: Optional[List[dict]] = None,
    commodities: Optional[List[dict]] = None,
    forex_rates: Optional[Dict] = None,
    time_desc: str = ""
) -> dict:
    """
    组装股市简报卡片
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
            "content": f"**{title} · {today} {time_desc}**",
        }
    })
    elements.append({"tag": "hr"})

    # ── 重点关注指数 ───────────────────────────────────────────
    if focus_stock:
        emoji = "📈" if focus_stock["change"] >= 0 else "📉"
        sign = "+" if focus_stock["change"] >= 0 else ""
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"{emoji} **{focus_stock['name']}**: {focus_stock['price']} "
                          f"({sign}{focus_stock['change']}, {sign}{focus_stock['change_pct']}%)"
            }
        })
        elements.append({"tag": "hr"})

    # ── 美股行情 ──────────────────────────────────────────────
    if us_stocks:
        stock_lines = []
        for stock in us_stocks:
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
                "content": f"🇺🇸 **美股行情**\n{stock_text}",
            }
        })
        elements.append({"tag": "hr"})

    # ── 全球股市（晚间模式）────────────────────────────────────
    if stocks and not focus_stock:
        stock_lines = []
        for stock in stocks:
            emoji = "📈" if stock["change"] >= 0 else "📉"
            sign = "+" if stock["change"] >= 0 else ""
            flag = "🇺🇸" if stock['name'] in ['标普500', '纳斯达克', '道琼斯'] else "🇭🇰" if stock['name'] == '恒生指数' else "🇨🇳"
            stock_lines.append(
                f"{flag} {emoji} **{stock['name']}**: {stock['price']} "
                f"({sign}{stock['change']}, {sign}{stock['change_pct']}%)"
            )
        stock_text = "\n".join(stock_lines)
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"📊 **全球股市收盘**\n{stock_text}",
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
        elements.append({"tag": "hr"})

    # ── 大宗商品 ──────────────────────────────────────────────
    if commodities:
        comm_lines = []
        for comm in commodities:
            emoji = "📈" if comm["change"] >= 0 else "📉"
            sign = "+" if comm["change"] >= 0 else ""
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

    # ── 底部注脚 ──────────────────────────────────────────────
    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": f"由 GitHub Actions 自动推送 · {time_desc}"
        }]
    })

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "📈 股市简报"},
            "template": "orange",
        },
        "elements": elements,
    }


def build_analysis_card(
    analysis_type: str,
    analysis: dict,
    report_type: str = "full"
) -> dict:
    """
    组装股票/板块分析报告卡片
    """
    from datetime import datetime

    now = datetime.now()
    weekday = WEEKDAY_CN[now.weekday()]
    today = now.strftime(f"%Y-%m-%d {weekday}")

    elements = []

    if analysis_type == "stock":
        # 股票分析报告
        stock_code = analysis["stock_code"]
        market = analysis["market"]
        quote = analysis["quote"]

        # 标题
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**📊 股票分析报告 · {stock_code} ({market}) · {today}**",
            }
        })
        elements.append({"tag": "hr"})

        # 实时价格
        emoji = "📈" if quote["change"] >= 0 else "📉"
        sign = "+" if quote["change"] >= 0 else ""
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"{emoji} **实时价格**: {quote['price']} "
                          f"({sign}{quote['change']}, {sign}{quote['change_pct']}%)"
            }
        })

        # 技术分析
        if "technical" in analysis and analysis["technical"]:
            tech = analysis["technical"]
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**📈 技术分析**\n"
                              f"• 趋势: {tech.get('trend', '未知')}\n"
                              f"• 5日均线: {tech.get('ma5', '--')}\n"
                              f"• 10日均线: {tech.get('ma10', '--')}\n"
                              f"• 20日均线: {tech.get('ma20', '--')}\n"
                              f"• 5日涨跌: {tech.get('change_5d', '--')}%\n"
                              f"• 20日涨跌: {tech.get('change_20d', '--')}%\n"
                              f"• 波动率: {tech.get('volatility', '--')}%"
                }
            })

        # 基本面分析
        if "fundamentals" in analysis and analysis["fundamentals"]:
            fund = analysis["fundamentals"]
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**💼 基本面数据**\n"
                              f"• 市盈率 (PE): {fund.get('pe_ratio', '--')}\n"
                              f"• 市净率 (PB): {fund.get('pb_ratio', '--')}\n"
                              f"• 股息率: {fund.get('dividend_yield', '--')}%\n"
                              f"• 52周最高: {fund.get('52w_high', '--')}\n"
                              f"• 52周最低: {fund.get('52w_low', '--')}"
                }
            })

        # 近期价格走势
        if "history" in analysis and analysis["history"]:
            elements.append({"tag": "hr"})
            history_lines = ["**📅 近期走势**"]
            for h in analysis["history"]:
                history_lines.append(f"• {h['date']}: {h['close']}")
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "\n".join(history_lines)
                }
            })

    elif analysis_type == "sector":
        # 板块分析报告
        sector = analysis["sector"]
        market = analysis["market"]
        avg_change = analysis["avg_change"]

        emoji = "📈" if avg_change >= 0 else "📉"

        # 标题
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**📊 板块分析报告 · {sector} ({market}) · {today}**",
            }
        })
        elements.append({"tag": "hr"})

        # 板块概览
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"{emoji} **板块平均涨跌**: {avg_change}%"
            }
        })

        # 领涨股
        if analysis.get("top_gainers"):
            elements.append({"tag": "hr"})
            gainers_lines = ["**🚀 领涨股**"]
            for g in analysis["top_gainers"]:
                gainers_lines.append(f"• {g['name']}: +{g['change_pct']}%")
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "\n".join(gainers_lines)
                }
            })

        # 领跌股
        if analysis.get("top_losers"):
            elements.append({"tag": "hr"})
            losers_lines = ["**📉 领跌股**"]
            for l in analysis["top_losers"]:
                losers_lines.append(f"• {l['name']}: {l['change_pct']}%")
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "\n".join(losers_lines)
                }
            })

        # 成分股列表
        if analysis.get("stocks"):
            elements.append({"tag": "hr"})
            stocks_lines = ["**📋 成分股表现**"]
            for s in analysis["stocks"]:
                emoji = "📈" if s["change"] >= 0 else "📉"
                sign = "+" if s["change"] >= 0 else ""
                stocks_lines.append(f"{emoji} {s['name']}: {s['price']} ({sign}{s['change_pct']}%)")
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "\n".join(stocks_lines)
                }
            })

    # 底部注脚
    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": f"由 GitHub Actions 手动触发 · 类型: {report_type}"
        }]
    })

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "📊 分析报告"},
            "template": "green",
        },
        "elements": elements,
    }
