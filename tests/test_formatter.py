from formatter import build_card


def test_build_card_includes_expected_sections():
    card = build_card(
        weather={
            "city": "Shanghai",
            "text": "晴",
            "temp": "26",
            "feelsLike": "28",
            "windDir": "东风",
            "windScale": "3级",
            "humidity": "61",
        },
        all_news={
            "时事": [
                {
                    "title": "全球市场回暖",
                    "link": "https://example.com/world",
                    "summary": "主要股指回升。",
                }
            ],
            "科技/AI": [],
            "开发者": [],
        },
        finance_news=[
            {
                "title": "美债收益率回落",
                "link": "https://example.com/bond",
                "summary": "市场风险偏好回升。",
                "sentiment_emoji": "🟢",
            }
        ],
        stocks=[{"name": "标普500", "price": "5200", "change": 12.3, "change_pct": 0.24}],
        commodities=[{"name": "黄金", "price": "2300", "change": -5.6, "change_pct": -0.24}],
        forex_rates={"USD/CNY": {"rate": "7.20", "change": 0.01, "change_pct": 0.14}},
        bonds_vix={
            "treasury_10y": {"name": "美国10年国债", "yield": "4.2", "change": -0.03, "change_pct": -0.71},
            "vix": {"name": "VIX", "value": 14.1, "change": -1.2, "change_pct": -7.8},
        },
        forex_analysis="美元小幅走强。",
        bond_vix_analysis="风险偏好改善。",
        github_trending=[
            {
                "name": "openai/openai-python",
                "url": "https://github.com/openai/openai-python",
                "stars": 1000,
                "language": "Python",
                "description": "Official Python library for the OpenAI API",
            }
        ],
        product_hunt=[
            {
                "name": "AI Notebook",
                "url": "https://example.com/product",
                "tagline": "A faster way to capture research notes",
                "votes": 88,
            }
        ],
        hot_topics=[
            {
                "topic": "AI Agent",
                "count": 3,
                "related_news": [
                    {
                        "title": "Agent infra keeps expanding",
                        "link": "https://example.com/agent",
                        "summary": "Tooling demand keeps rising.",
                    }
                ],
            }
        ],
        sentiment_result={"overall": "positive", "summary": "市场情绪偏积极"},
    )

    assert card["header"]["title"]["content"] == "📋 每日简报"

    contents = [
        element["text"]["content"]
        for element in card["elements"]
        if element.get("tag") == "div"
    ]

    assert any("🌤 **天气**" in content for content in contents)
    assert any("📊 **全球股市**" in content for content in contents)
    assert any("🔥 **今日热点**" in content for content in contents)
    assert any("💻 **GitHub 热门**" in content for content in contents)
    assert any("🚀 **Product Hunt 热门**" in content for content in contents)


def test_build_card_skips_optional_sections_when_data_is_missing():
    card = build_card(
        weather={
            "city": "Beijing",
            "text": "阴",
            "temp": "20",
            "feelsLike": "19",
            "windDir": "北风",
            "windScale": "2级",
            "humidity": "40",
        },
        all_news={},
        finance_news=[],
        stocks=[],
        commodities=[],
        forex_rates={},
        bonds_vix={},
        github_trending=[],
        product_hunt=[],
        hot_topics=[],
        sentiment_result=None,
    )

    contents = [
        element["text"]["content"]
        for element in card["elements"]
        if element.get("tag") == "div"
    ]

    assert any("🌤 **天气**" in content for content in contents)
    assert all("💻 **GitHub 热门**" not in content for content in contents)
    assert all("🚀 **Product Hunt 热门**" not in content for content in contents)
