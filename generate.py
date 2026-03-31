"""
热榜数据生成脚本 — 供 GitHub Actions 调用

用法:
    python generate.py

输出:
    docs/api/boards.json                    — 最新数据（每次覆盖）
    docs/api/status.json                    — 最新抓取状态
    docs/api/history/2026-03-30-08.json     — 历史快照
    docs/api/history.json                   — 历史索引
"""
import json
import os
import sys
import glob
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from hotboard.sources import ALL_FETCHERS
from hotboard.config import PLATFORMS, GROUP_ORDER, GROUP_NAMES
from hotboard.analyzer import analyze_cross_platform
from concurrent.futures import ThreadPoolExecutor


def _get_platform_state(status: dict) -> str:
    if status.get("consecutive_failures", 0) > 0 or status.get("last_error"):
        return "failing"
    if status.get("cache_age_seconds") is not None and status.get("cache_age_seconds", 0) > 600:
        return "stale"
    if status.get("cached"):
        return "healthy"
    return "unknown"


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
        if status["enabled"] and status["has_fetcher"] and _get_platform_state(status) == "failing"
    ]
    stale_platforms = [
        {"platform": platform, **status}
        for platform, status in statuses.items()
        if status["enabled"] and status["has_fetcher"] and _get_platform_state(status) == "stale"
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


def fetch_one(platform: str) -> dict:
    fetcher_cls = ALL_FETCHERS.get(platform)
    if not fetcher_cls:
        return {"platform": platform, "board": None, "duration_ms": None, "error": "fetcher missing"}

    started_at = datetime.now(timezone.utc)
    try:
        fetcher = fetcher_cls()
        board = fetcher.get_board()
        duration_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
        return {"platform": platform, "board": board.to_dict(), "duration_ms": duration_ms, "error": ""}
    except Exception as e:
        duration_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
        print(f"  [WARN] {platform}: {e}", file=sys.stderr)
        return {"platform": platform, "board": None, "duration_ms": duration_ms, "error": str(e)}


def build_statuses(results: dict, generated_at: str) -> dict:
    statuses = {}
    for platform, conf in PLATFORMS.items():
        result = results.get(platform, {})
        board = result.get("board")
        duration_ms = result.get("duration_ms")
        error = result.get("error", "")
        success = board is not None
        item_count = len(board.get("items", [])) if board else 0
        statuses[platform] = {
            "name": conf[0],
            "enabled": conf[3],
            "has_fetcher": platform in ALL_FETCHERS,
            "cached": success,
            "updated_at": board.get("updated_at", "") if board else "",
            "cache_updated_at": generated_at if success else "",
            "cache_age_seconds": 0 if success else None,
            "attempts": 1 if platform in results else 0,
            "successes": 1 if success else 0,
            "failures": 0 if success else (1 if platform in results else 0),
            "success_rate": 1.0 if success else 0.0,
            "consecutive_failures": 0 if success else (1 if platform in results else 0),
            "last_attempt_at": generated_at if platform in results else "",
            "last_success_at": generated_at if success else "",
            "last_duration_ms": duration_ms,
            "last_item_count": item_count,
            "last_error": error[:500],
            "state": "healthy" if success else ("failing" if platform in results else "unknown"),
        }
    return statuses


def compute_platform_trends(statuses: dict, snapshots: list, limit: int = 8) -> list:
    recent_snapshots = snapshots[:limit]
    trend_rows = []

    for platform, status in statuses.items():
        if not status["enabled"] or not status["has_fetcher"]:
            continue

        samples = []
        failing_count = 0
        healthy_count = 0
        duration_sum = 0
        duration_count = 0

        for snapshot in recent_snapshots:
            snap_status = snapshot.get("statuses", {}).get(platform)
            if not snap_status:
                continue

            state = snap_status.get("state") or _get_platform_state(snap_status)
            samples.append({
                "id": snapshot.get("snapshot_id") or snapshot.get("snapshot", {}).get("id", ""),
                "state": state,
                "duration_ms": snap_status.get("last_duration_ms"),
                "item_count": snap_status.get("last_item_count", 0),
            })
            if state == "healthy":
                healthy_count += 1
            elif state == "failing":
                failing_count += 1
            if snap_status.get("last_duration_ms") is not None:
                duration_sum += snap_status["last_duration_ms"]
                duration_count += 1

        sample_count = len(samples)
        availability_rate = round(healthy_count / sample_count, 4) if sample_count else 0.0
        avg_duration_ms = round(duration_sum / duration_count) if duration_count else None

        trend_rows.append({
            "platform": platform,
            "name": status["name"],
            "state": status.get("state") or _get_platform_state(status),
            "availability_rate": availability_rate,
            "avg_duration_ms": avg_duration_ms,
            "current_duration_ms": status.get("last_duration_ms"),
            "failing_samples": failing_count,
            "healthy_samples": healthy_count,
            "sample_count": sample_count,
            "last_error": status.get("last_error", ""),
            "sparkline": [sample["state"] for sample in samples],
        })

    trend_rows.sort(
        key=lambda row: (
            0 if row["state"] == "failing" else 1 if row["state"] == "stale" else 2,
            row["availability_rate"],
            -(row["avg_duration_ms"] or 0),
            row["name"],
        )
    )
    return trend_rows


def build_health_history(snapshots: list, limit: int = 8) -> list:
    history = []
    for snapshot in snapshots[:limit]:
        health = snapshot.get("health", {})
        history.append({
            "id": snapshot.get("snapshot_id") or snapshot.get("snapshot", {}).get("id", ""),
            "generated_at": snapshot.get("generated_at", ""),
            "healthy_count": health.get("healthy_count", 0),
            "failing_count": health.get("failing_count", 0),
            "stale_count": health.get("stale_count", 0),
            "enabled_count": health.get("enabled_count", 0),
        })
    return history


def load_previous_snapshot(base_dir: str, current_id: str) -> dict | None:
    """加载上一次快照数据"""
    index_path = os.path.join(base_dir, "history.json")
    if not os.path.exists(index_path):
        return None
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            history = json.load(f)
        # 找到最近一个不是当前 ID 的快照
        for entry in sorted(history, key=lambda x: x["id"], reverse=True):
            if entry["id"] != current_id:
                snap_path = os.path.join(base_dir, entry["file"])
                if os.path.exists(snap_path):
                    with open(snap_path, "r", encoding="utf-8") as f:
                        return json.load(f)
        return None
    except Exception:
        return None


def load_recent_snapshots(base_dir: str, current_id: str, limit: int = 8) -> list:
    index_path = os.path.join(base_dir, "history.json")
    if not os.path.exists(index_path):
        return []
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return []

    snapshots = []
    for entry in sorted(history, key=lambda x: x["id"], reverse=True):
        if entry["id"] == current_id:
            continue
        snap_path = os.path.join(base_dir, entry["file"])
        if not os.path.exists(snap_path):
            continue
        try:
            with open(snap_path, "r", encoding="utf-8") as f:
                snapshots.append(json.load(f))
        except Exception:
            continue
        if len(snapshots) >= limit:
            break
    return snapshots


def compute_trends(boards: dict, prev_snapshot: dict | None) -> list:
    """
    对比当前数据和上次快照，为每条 item 标记趋势状态，
    并返回 rising_topics 列表
    """
    if not prev_snapshot:
        # 没有历史数据，所有条目标记为 new
        for board in boards.values():
            for item in board.get("items", []):
                item["trend"] = "new"
                item["rank_change"] = None
        return []

    prev_boards = prev_snapshot.get("boards", {})
    rising_topics = []

    for platform, board in boards.items():
        prev_board = prev_boards.get(platform, {})
        prev_titles = {}
        for item in prev_board.get("items", []):
            prev_titles[item.get("title", "")] = item.get("rank", 99)

        for item in board.get("items", []):
            title = item.get("title", "")
            rank = item.get("rank", 99)

            if title not in prev_titles:
                item["trend"] = "new"
                item["rank_change"] = None
                if rank <= 10:
                    rising_topics.append({
                        "title": title,
                        "platform": platform,
                        "platform_name": board.get("platform_name", platform),
                        "trend": "new",
                        "rank": rank,
                        "rank_change": None,
                    })
            else:
                prev_rank = prev_titles[title]
                change = prev_rank - rank  # 正数=上升
                if change > 0:
                    item["trend"] = "up"
                    item["rank_change"] = change
                    if change >= 3 and rank <= 15:
                        rising_topics.append({
                            "title": title,
                            "platform": platform,
                            "platform_name": board.get("platform_name", platform),
                            "trend": "up",
                            "rank": rank,
                            "rank_change": change,
                        })
                elif change < 0:
                    item["trend"] = "down"
                    item["rank_change"] = change
                else:
                    item["trend"] = "same"
                    item["rank_change"] = 0

    # 按热度排序：新上榜优先，然后按上升幅度
    rising_topics.sort(key=lambda x: (
        0 if x["trend"] == "new" else 1,
        x.get("rank", 99),
    ))
    return rising_topics[:15]


def main():
    enabled = [k for k, v in PLATFORMS.items() if v[3] and k in ALL_FETCHERS]
    print(f"Fetching {len(enabled)} platforms: {', '.join(enabled)}")

    boards = {}
    results = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_one, p): p for p in enabled}
        for future in futures:
            platform = futures[future]
            try:
                result = future.result(timeout=30)
                results[platform] = result
                board = result.get("board")
                if board:
                    boards[platform] = board
                    count = len(board.get("items", []))
                    print(f"  [OK] {platform}: {count} items / {result.get('duration_ms')}ms")
                else:
                    print(f"  [SKIP] {platform}: {result.get('error') or 'no data'}")
            except Exception as e:
                print(f"  [FAIL] {platform}: {e}")

    bj_tz = timezone(timedelta(hours=8))
    now = datetime.now(bj_tz)
    generated_at = now.isoformat(timespec="seconds")
    snapshot_id = now.strftime("%Y-%m-%d-%H")

    base_dir = os.path.join(os.path.dirname(__file__), "docs", "api")
    history_dir = os.path.join(base_dir, "history")
    os.makedirs(history_dir, exist_ok=True)

    # === 趋势追踪 ===
    print("📊 计算趋势变化...")
    prev_snapshot = load_previous_snapshot(base_dir, snapshot_id)
    recent_snapshots = load_recent_snapshots(base_dir, snapshot_id)
    rising_topics = compute_trends(boards, prev_snapshot)
    if prev_snapshot:
        print(f"  [OK] 对比上次快照, {len(rising_topics)} 条飙升热点")
    else:
        print(f"  [INFO] 无历史快照, 所有条目标记为 new")

    print("🩺 汇总抓取状态...")
    statuses = build_statuses(results, generated_at)
    health = build_health_overview(statuses)

    # === AI 热点分析 ===
    print("🤖 运行跨平台热点分析...")
    analysis = analyze_cross_platform(boards)
    topic_count = len(analysis.get("cross_platform_topics", []))
    print(f"  [OK] 发现 {topic_count} 个跨平台热点")
    analysis["generated_at"] = generated_at

    snapshot_for_trends = {
        "snapshot_id": snapshot_id,
        "generated_at": generated_at,
        "statuses": statuses,
        "health": health,
    }
    trend_history = {
        "health_history": build_health_history([snapshot_for_trends, *recent_snapshots]),
        "platform_trends": compute_platform_trends(statuses, [snapshot_for_trends, *recent_snapshots]),
    }

    # === 组装输出 ===
    grouped = {}
    for group_key in GROUP_ORDER:
        group_boards = [b for b in boards.values() if b.get("group") == group_key]
        if group_boards:
            grouped[group_key] = {
                "name": GROUP_NAMES.get(group_key, group_key),
                "boards": group_boards,
            }

    output = {
        "generated_at": generated_at,
        "snapshot_id": snapshot_id,
        "platform_count": len(boards),
        "grouped": grouped,
        "boards": boards,
        "statuses": statuses,
        "health": health,
        "trend_history": trend_history,
        "analysis": analysis,
        "rising_topics": rising_topics,
    }
    status_output = {
        "generated_at": generated_at,
        "snapshot_id": snapshot_id,
        "platform_count": len(boards),
        "statuses": statuses,
        "health": health,
        "trend_history": trend_history,
    }

    # 1. 写入最新 boards.json
    latest_path = os.path.join(base_dir, "boards.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 1.1 写入最新 status.json
    status_path = os.path.join(base_dir, "status.json")
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status_output, f, ensure_ascii=False, indent=2)

    # 2. 写入历史快照
    snapshot_path = os.path.join(history_dir, f"{snapshot_id}.json")
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 3. 更新历史索引
    snapshots = sorted(glob.glob(os.path.join(history_dir, "*.json")))
    history_index = []
    for sp in snapshots:
        fname = os.path.basename(sp)
        sid = fname.replace(".json", "")
        history_index.append({
            "id": sid,
            "file": f"history/{fname}",
            **(_read_snapshot_meta(sp) if sid != snapshot_id else {
                "platform_count": output["platform_count"],
                "healthy_count": health["healthy_count"],
                "failing_count": health["failing_count"],
                "stale_count": health["stale_count"],
            }),
        })

    index_path = os.path.join(base_dir, "history.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(history_index, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(boards)} platforms")
    print(f"  latest   -> {latest_path}")
    print(f"  status   -> {status_path}")
    print(f"  snapshot -> {snapshot_path}")
    print(f"  history  -> {len(history_index)} snapshots")
    print(f"  analysis -> {topic_count} cross-platform topics")
    print(f"  rising   -> {len(rising_topics)} rising topics")


def _read_platform_count(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("platform_count", 0)
    except Exception:
        return 0


def _read_snapshot_meta(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        health = payload.get("health", {})
        return {
            "platform_count": payload.get("platform_count", 0),
            "healthy_count": health.get("healthy_count", 0),
            "failing_count": health.get("failing_count", 0),
            "stale_count": health.get("stale_count", 0),
        }
    except Exception:
        return {
            "platform_count": _read_platform_count(path),
            "healthy_count": 0,
            "failing_count": 0,
            "stale_count": 0,
        }


if __name__ == "__main__":
    main()
