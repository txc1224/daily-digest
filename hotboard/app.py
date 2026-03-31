import os
import sys
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import JSONResponse

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from hotboard.config import PLATFORMS, GROUP_NAMES, GROUP_ORDER
from hotboard.sources import ALL_FETCHERS
from hotboard.cache import get_cache, set_cache, clear_cache
from hotboard.status import get_platform_status, record_fetch_result


_executor = ThreadPoolExecutor(max_workers=8)


def _fetch_one(platform: str) -> dict | None:
    """抓取单个平台，有缓存就用缓存"""
    cached = get_cache(platform)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    fetcher_cls = ALL_FETCHERS.get(platform)
    if not fetcher_cls:
        return None

    started_at = time.perf_counter()
    try:
        fetcher = fetcher_cls()
        board = fetcher.get_board()
        board_dict = board.to_dict()
        set_cache(platform, board_dict)
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        record_fetch_result(
            platform,
            success=True,
            duration_ms=duration_ms,
            item_count=len(board_dict.get("items", [])),
        )
        return board_dict
    except Exception as e:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        record_fetch_result(
            platform,
            success=False,
            duration_ms=duration_ms,
            error=str(e),
        )
        print(f"[{platform}] fetch error: {e}", file=sys.stderr)
        return None


def fetch_all_boards() -> dict:
    """并发抓取所有已启用平台"""
    enabled = [k for k, v in PLATFORMS.items() if v[3] and k in ALL_FETCHERS]
    results = {}

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_fetch_one, p): p for p in enabled}
        for future in futures:
            platform = futures[future]
            try:
                board = future.result(timeout=30)
                if board:
                    results[platform] = board
            except Exception as e:
                print(f"[{platform}] timeout/error: {e}", file=sys.stderr)

    return results


def get_cached_boards() -> dict:
    """只返回已有缓存的数据，不触发抓取"""
    enabled = [k for k, v in PLATFORMS.items() if v[3] and k in ALL_FETCHERS]
    results = {}
    for platform in enabled:
        cached = get_cache(platform)
        if cached:
            cached.pop("_cached_at", None)
            results[platform] = cached
    return results


def get_status_snapshot() -> dict:
    statuses = {}
    for platform, conf in PLATFORMS.items():
        cached = get_cache(platform)
        fetch_status = get_platform_status(platform)
        cache_updated_at = ""
        cache_age_seconds = None
        if cached:
            cached_at = cached.get("_cached_at")
            if cached_at:
                cache_updated_at = datetime.fromtimestamp(cached_at).isoformat(timespec="seconds")
                cache_age_seconds = max(0, int(time.time() - cached_at))
        statuses[platform] = {
            "name": conf[0],
            "enabled": conf[3],
            "has_fetcher": platform in ALL_FETCHERS,
            "cached": cached is not None,
            "updated_at": cached.get("updated_at", "") if cached else "",
            "cache_updated_at": cache_updated_at,
            "cache_age_seconds": cache_age_seconds,
            **fetch_status,
        }
    return statuses


def build_health_overview(statuses: dict) -> dict:
    enabled_statuses = [status for status in statuses.values() if status["enabled"] and status["has_fetcher"]]
    healthy_count = sum(
        1
        for status in enabled_statuses
        if status["cached"] and status["consecutive_failures"] == 0 and not status["last_error"]
    )
    failing_platforms = [
        {"platform": platform, **status}
        for platform, status in statuses.items()
        if status["enabled"] and status["has_fetcher"] and (status["consecutive_failures"] > 0 or status["last_error"])
    ]
    stale_platforms = [
        {"platform": platform, **status}
        for platform, status in statuses.items()
        if status["enabled"]
        and status["has_fetcher"]
        and status["cache_age_seconds"] is not None
        and status["cache_age_seconds"] > 600
    ]
    slow_platforms = sorted(
        (
            {"platform": platform, **status}
            for platform, status in statuses.items()
            if status["enabled"] and status["has_fetcher"] and status["last_duration_ms"] is not None
        ),
        key=lambda status: status["last_duration_ms"],
        reverse=True,
    )[:3]
    failing_platforms.sort(
        key=lambda status: (
            -status["consecutive_failures"],
            -(status["cache_age_seconds"] or 0),
            status["name"],
        )
    )
    return {
        "enabled_count": len(enabled_statuses),
        "healthy_count": healthy_count,
        "failing_count": len(failing_platforms),
        "stale_count": len(stale_platforms),
        "failing_platforms": failing_platforms[:5],
        "slow_platforms": slow_platforms,
    }


# ---- FastAPI App ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 后台预热缓存（不阻塞启动）
    import threading
    threading.Thread(target=fetch_all_boards, daemon=True).start()

    # 启动定时任务
    from hotboard.scheduler import start_scheduler
    scheduler = start_scheduler()

    print("🔥 热榜看板已启动: http://localhost:8000")
    yield

    # 关闭定时任务
    scheduler.shutdown()


app = FastAPI(title="HotBoard", lifespan=lifespan)

_dir = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(_dir, "templates"))


@app.get("/")
async def index(request: Request):
    boards = get_cached_boards()
    statuses = get_status_snapshot()
    health = build_health_overview(statuses)

    grouped = {}
    for group_key in GROUP_ORDER:
        group_boards = []
        for platform, board in boards.items():
            if board.get("group") == group_key:
                group_boards.append(board)
        if group_boards:
            grouped[group_key] = {
                "name": GROUP_NAMES.get(group_key, group_key),
                "boards": group_boards,
            }

    return templates.TemplateResponse(request, "index.html", {
        "grouped": grouped,
        "health": health,
        "statuses": statuses,
    })


@app.get("/api/boards")
async def api_boards():
    return JSONResponse(get_cached_boards())


@app.get("/api/boards/{platform}")
async def api_board(platform: str):
    loop = asyncio.get_event_loop()
    board = await loop.run_in_executor(None, _fetch_one, platform)
    if not board:
        return JSONResponse({"error": f"Platform '{platform}' not found"}, status_code=404)
    return JSONResponse(board)


@app.post("/api/refresh")
async def api_refresh():
    clear_cache()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, fetch_all_boards)
    return JSONResponse({"status": "ok", "platforms": list(get_cached_boards().keys())})


@app.get("/api/status")
async def api_status():
    statuses = get_status_snapshot()
    return JSONResponse({
        "platforms": statuses,
        "health": build_health_overview(statuses),
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("hotboard.app:app", host="0.0.0.0", port=8000, reload=True)
