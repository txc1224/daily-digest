from hotboard.feishu_push import build_hotboard_daily_brief_card


def test_build_hotboard_daily_brief_card_contains_topics_groups_and_health():
    boards = {
        "github": {
            "platform_name": "GitHub Trending",
            "group": "tech",
            "items": [
                {"rank": 1, "title": "repo-a", "url": "https://example.com/repo-a", "hot_value": "12k"},
            ],
        },
        "zhihu": {
            "platform_name": "知乎热榜",
            "group": "domestic",
            "items": [
                {"rank": 1, "title": "topic-a", "url": "https://example.com/topic-a", "hot_value": "热"},
            ],
        },
    }
    statuses = {
        "github": {
            "name": "GitHub Trending",
            "enabled": True,
            "has_fetcher": True,
            "cached": True,
            "consecutive_failures": 0,
            "last_error": "",
            "cache_age_seconds": 10,
            "last_duration_ms": 120,
            "last_item_count": 20,
        },
        "zhihu": {
            "name": "知乎热榜",
            "enabled": True,
            "has_fetcher": True,
            "cached": False,
            "consecutive_failures": 2,
            "last_error": "timeout",
            "cache_age_seconds": None,
            "last_duration_ms": 800,
            "last_item_count": 0,
        },
    }

    card = build_hotboard_daily_brief_card(boards, statuses)

    assert card["header"]["title"]["content"] == "📡 HotBoard 日摘要"
    contents = [element["content"] for element in card["elements"] if element.get("tag") == "markdown"]
    assert any("今日概览" in content for content in contents)
    assert any("即刻关注" in content for content in contents)
    assert any("跨平台热点" in content for content in contents)
    assert any("技术社区 精选" in content for content in contents)
    assert any("国内平台 精选" in content for content in contents)
    assert any("抓取异常" in content for content in contents)
