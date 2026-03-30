"""
热榜数据生成脚本 — 供 GitHub Actions 调用

用法:
    python generate.py

输出:
    docs/api/boards.json                    — 最新数据（每次覆盖）
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


def fetch_one(platform: str) -> dict | None:
    fetcher_cls = ALL_FETCHERS.get(platform)
    if not fetcher_cls:
        return None
    try:
        fetcher = fetcher_cls()
        board = fetcher.get_board()
        return board.to_dict()
    except Exception as e:
        print(f"  [WARN] {platform}: {e}", file=sys.stderr)
        return None


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
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_one, p): p for p in enabled}
        for future in futures:
            platform = futures[future]
            try:
                board = future.result(timeout=30)
                if board:
                    boards[platform] = board
                    count = len(board.get("items", []))
                    print(f"  [OK] {platform}: {count} items")
                else:
                    print(f"  [SKIP] {platform}: no data")
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
    rising_topics = compute_trends(boards, prev_snapshot)
    if prev_snapshot:
        print(f"  [OK] 对比上次快照, {len(rising_topics)} 条飙升热点")
    else:
        print(f"  [INFO] 无历史快照, 所有条目标记为 new")

    # === AI 热点分析 ===
    print("🤖 运行跨平台热点分析...")
    analysis = analyze_cross_platform(boards)
    topic_count = len(analysis.get("cross_platform_topics", []))
    print(f"  [OK] 发现 {topic_count} 个跨平台热点")
    analysis["generated_at"] = generated_at

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
        "analysis": analysis,
        "rising_topics": rising_topics,
    }

    # 1. 写入最新 boards.json
    latest_path = os.path.join(base_dir, "boards.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

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
            "platform_count": output["platform_count"] if sid == snapshot_id else _read_platform_count(sp),
        })

    index_path = os.path.join(base_dir, "history.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(history_index, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(boards)} platforms")
    print(f"  latest   -> {latest_path}")
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


if __name__ == "__main__":
    main()
