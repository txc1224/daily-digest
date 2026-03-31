import json
import os
import threading
from datetime import datetime, timezone

from hotboard.config import CACHE_DIR


_status_lock = threading.Lock()
_cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), CACHE_DIR)
_status_path = os.path.join(_cache_dir, "_fetch_status.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _load_statuses() -> dict:
    if not os.path.exists(_status_path):
        return {}
    try:
        with open(_status_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_statuses(statuses: dict) -> None:
    os.makedirs(_cache_dir, exist_ok=True)
    with open(_status_path, "w", encoding="utf-8") as f:
        json.dump(statuses, f, ensure_ascii=False, indent=2)


def _default_status() -> dict:
    return {
        "attempts": 0,
        "successes": 0,
        "failures": 0,
        "success_rate": 0.0,
        "consecutive_failures": 0,
        "last_attempt_at": "",
        "last_success_at": "",
        "last_duration_ms": None,
        "last_item_count": 0,
        "last_error": "",
    }


def record_fetch_result(
    platform: str,
    *,
    success: bool,
    duration_ms: int,
    item_count: int = 0,
    error: str = "",
) -> dict:
    with _status_lock:
        statuses = _load_statuses()
        status = statuses.get(platform, _default_status())

        status["attempts"] += 1
        status["last_attempt_at"] = _utc_now()
        status["last_duration_ms"] = duration_ms
        status["last_item_count"] = item_count

        if success:
            status["successes"] += 1
            status["consecutive_failures"] = 0
            status["last_success_at"] = status["last_attempt_at"]
            status["last_error"] = ""
        else:
            status["failures"] += 1
            status["consecutive_failures"] += 1
            status["last_error"] = error[:500]

        attempts = status["attempts"]
        status["success_rate"] = round(status["successes"] / attempts, 4) if attempts else 0.0
        statuses[platform] = status
        _save_statuses(statuses)
        return dict(status)


def get_platform_status(platform: str) -> dict:
    statuses = _load_statuses()
    status = statuses.get(platform)
    if not status:
        return _default_status()
    merged = _default_status()
    merged.update(status)
    return merged
