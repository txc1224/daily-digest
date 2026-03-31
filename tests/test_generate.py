from generate import build_health_overview, build_statuses, compute_platform_trends, compute_trends


def test_compute_trends_marks_all_items_new_without_history():
    boards = {
        "github": {
            "platform_name": "GitHub Trending",
            "items": [{"title": "repo-a", "rank": 1}, {"title": "repo-b", "rank": 3}],
        }
    }

    rising_topics = compute_trends(boards, None)

    assert rising_topics == []
    assert boards["github"]["items"][0]["trend"] == "new"
    assert boards["github"]["items"][0]["rank_change"] is None
    assert boards["github"]["items"][1]["trend"] == "new"


def test_compute_trends_detects_new_up_down_and_same_items():
    boards = {
        "github": {
            "platform_name": "GitHub Trending",
            "items": [
                {"title": "repo-up", "rank": 2},
                {"title": "repo-down", "rank": 7},
                {"title": "repo-same", "rank": 4},
                {"title": "repo-new", "rank": 5},
            ],
        }
    }
    previous_snapshot = {
        "boards": {
            "github": {
                "items": [
                    {"title": "repo-up", "rank": 8},
                    {"title": "repo-down", "rank": 3},
                    {"title": "repo-same", "rank": 4},
                ]
            }
        }
    }

    rising_topics = compute_trends(boards, previous_snapshot)
    items = {item["title"]: item for item in boards["github"]["items"]}

    assert items["repo-up"]["trend"] == "up"
    assert items["repo-up"]["rank_change"] == 6
    assert items["repo-down"]["trend"] == "down"
    assert items["repo-down"]["rank_change"] == -4
    assert items["repo-same"]["trend"] == "same"
    assert items["repo-same"]["rank_change"] == 0
    assert items["repo-new"]["trend"] == "new"
    assert items["repo-new"]["rank_change"] is None
    assert [topic["title"] for topic in rising_topics] == ["repo-new", "repo-up"]


def test_compute_trends_only_promotes_large_rank_improvements():
    boards = {
        "reddit": {
            "platform_name": "Reddit",
            "items": [
                {"title": "topic-small-up", "rank": 8},
                {"title": "topic-big-up", "rank": 10},
            ],
        }
    }
    previous_snapshot = {
        "boards": {
            "reddit": {
                "items": [
                    {"title": "topic-small-up", "rank": 9},
                    {"title": "topic-big-up", "rank": 14},
                ]
            }
        }
    }

    rising_topics = compute_trends(boards, previous_snapshot)

    assert [topic["title"] for topic in rising_topics] == ["topic-big-up"]


def test_build_statuses_and_health_overview_capture_failures():
    results = {
        "github": {
            "board": {"updated_at": "2026-03-31T08:00:00+08:00", "items": [{"title": "repo", "rank": 1}]},
            "duration_ms": 320,
            "error": "",
        },
        "producthunt": {
            "board": None,
            "duration_ms": 1200,
            "error": "upstream timeout",
        },
    }

    statuses = build_statuses(results, "2026-03-31T08:00:00+08:00")
    overview = build_health_overview(statuses)

    assert statuses["github"]["state"] == "healthy"
    assert statuses["github"]["success_rate"] == 1.0
    assert statuses["producthunt"]["state"] == "failing"
    assert statuses["producthunt"]["last_error"] == "upstream timeout"
    assert overview["healthy_count"] >= 1
    assert overview["failing_count"] >= 1


def test_compute_platform_trends_summarizes_recent_snapshots():
    statuses = {
        "github": {
            "name": "GitHub Trending",
            "enabled": True,
            "has_fetcher": True,
            "state": "healthy",
            "last_duration_ms": 300,
            "last_error": "",
        },
        "producthunt": {
            "name": "Product Hunt",
            "enabled": True,
            "has_fetcher": True,
            "state": "failing",
            "last_duration_ms": 1100,
            "last_error": "timeout",
        },
    }
    snapshots = [
        {
            "snapshot_id": "2026-03-31-08",
            "statuses": {
                "github": {"state": "healthy", "last_duration_ms": 300, "last_item_count": 20},
                "producthunt": {"state": "failing", "last_duration_ms": 1100, "last_item_count": 0},
            },
        },
        {
            "snapshot_id": "2026-03-31-07",
            "statuses": {
                "github": {"state": "healthy", "last_duration_ms": 280, "last_item_count": 20},
                "producthunt": {"state": "healthy", "last_duration_ms": 900, "last_item_count": 10},
            },
        },
    ]

    trends = compute_platform_trends(statuses, snapshots)

    assert trends[0]["platform"] == "producthunt"
    assert trends[0]["availability_rate"] == 0.5
    assert trends[0]["sparkline"] == ["failing", "healthy"]
    assert trends[1]["platform"] == "github"
