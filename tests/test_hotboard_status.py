import asyncio
import json
import tempfile

from hotboard import status as status_store
from hotboard.app import api_status


def test_record_fetch_result_tracks_success_rate_and_last_error(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(status_store, "_cache_dir", tmpdir)
        monkeypatch.setattr(status_store, "_status_path", f"{tmpdir}/status.json")

        first = status_store.record_fetch_result(
            "github",
            success=True,
            duration_ms=120,
            item_count=10,
        )
        second = status_store.record_fetch_result(
            "github",
            success=False,
            duration_ms=340,
            error="network timeout",
        )

        assert first["success_rate"] == 1.0
        assert second["attempts"] == 2
        assert second["successes"] == 1
        assert second["failures"] == 1
        assert second["success_rate"] == 0.5
        assert second["consecutive_failures"] == 1
        assert second["last_duration_ms"] == 340
        assert second["last_error"] == "network timeout"


def test_api_status_merges_cache_and_fetch_status(monkeypatch):
    monkeypatch.setattr(
        "hotboard.app.get_cache",
        lambda platform: {
            "_cached_at": 1_700_000_000,
            "updated_at": "2026-03-31T09:00:00",
        } if platform == "github" else None,
    )
    monkeypatch.setattr(
        "hotboard.app.get_platform_status",
        lambda platform: {
            "attempts": 3 if platform == "github" else 0,
            "successes": 2 if platform == "github" else 0,
            "failures": 1 if platform == "github" else 0,
            "success_rate": 0.6667 if platform == "github" else 0.0,
            "consecutive_failures": 1 if platform == "github" else 0,
            "last_attempt_at": "2026-03-31T09:00:01Z" if platform == "github" else "",
            "last_success_at": "2026-03-31T08:55:00Z" if platform == "github" else "",
            "last_duration_ms": 480 if platform == "github" else None,
            "last_item_count": 20 if platform == "github" else 0,
            "last_error": "timeout" if platform == "github" else "",
        },
    )
    monkeypatch.setattr("hotboard.app.time.time", lambda: 1_700_000_090)

    response = asyncio.run(api_status())
    payload = json.loads(response.body.decode("utf-8"))
    platforms = payload["platforms"]

    assert platforms["github"]["success_rate"] == 0.6667
    assert platforms["github"]["cache_age_seconds"] == 90
    assert platforms["github"]["last_error"] == "timeout"
    assert platforms["weibo"]["attempts"] == 0
    assert payload["health"]["failing_count"] >= 1
