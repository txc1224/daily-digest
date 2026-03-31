from hotboard.app import build_health_overview


def test_build_health_overview_counts_failing_stale_and_slow_platforms():
    statuses = {
        "github": {
            "name": "GitHub Trending",
            "enabled": True,
            "has_fetcher": True,
            "cached": True,
            "consecutive_failures": 0,
            "last_error": "",
            "cache_age_seconds": 120,
            "last_duration_ms": 220,
            "last_item_count": 20,
        },
        "reddit": {
            "name": "Reddit",
            "enabled": True,
            "has_fetcher": True,
            "cached": False,
            "consecutive_failures": 2,
            "last_error": "timeout",
            "cache_age_seconds": None,
            "last_duration_ms": 900,
            "last_item_count": 0,
        },
        "producthunt": {
            "name": "Product Hunt",
            "enabled": True,
            "has_fetcher": True,
            "cached": True,
            "consecutive_failures": 0,
            "last_error": "",
            "cache_age_seconds": 1200,
            "last_duration_ms": 650,
            "last_item_count": 20,
        },
    }

    overview = build_health_overview(statuses)

    assert overview["enabled_count"] == 3
    assert overview["healthy_count"] == 2
    assert overview["failing_count"] == 1
    assert overview["stale_count"] == 1
    assert overview["failing_platforms"][0]["platform"] == "reddit"
    assert overview["slow_platforms"][0]["platform"] == "reddit"
