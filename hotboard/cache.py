import json
import os
import time
from hotboard.config import CACHE_DIR, CACHE_TTL_SECONDS


# 确保缓存目录存在
_cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), CACHE_DIR)
os.makedirs(_cache_dir, exist_ok=True)


def _cache_path(platform: str) -> str:
    return os.path.join(_cache_dir, f"{platform}.json")


def get_cache(platform: str) -> dict | None:
    path = _cache_path(platform)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - data.get("_cached_at", 0) > CACHE_TTL_SECONDS:
            return None
        return data
    except (json.JSONDecodeError, IOError):
        return None


def set_cache(platform: str, board_dict: dict) -> None:
    board_dict["_cached_at"] = time.time()
    path = _cache_path(platform)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(board_dict, f, ensure_ascii=False, indent=2)


def clear_cache(platform: str = None) -> None:
    if platform:
        path = _cache_path(platform)
        if os.path.exists(path):
            os.remove(path)
    else:
        for f in os.listdir(_cache_dir):
            if f.endswith(".json"):
                os.remove(os.path.join(_cache_dir, f))
