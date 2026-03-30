"""
热榜数据生成脚本 — 供 GitHub Actions 调用

用法:
    python generate.py

输出:
    docs/api/boards.json                    — 最新数据（每次覆盖）
    docs/api/history/2026-03-30-08.json     — 历史快照（按日期时间保留）
    docs/api/history.json                   — 历史索引（供前端查询）
"""
import json
import os
import sys
import glob
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from hotboard.sources import ALL_FETCHERS
from hotboard.config import PLATFORMS, GROUP_ORDER, GROUP_NAMES
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

    # 按分组整理
    grouped = {}
    for group_key in GROUP_ORDER:
        group_boards = [b for b in boards.values() if b.get("group") == group_key]
        if group_boards:
            grouped[group_key] = {
                "name": GROUP_NAMES.get(group_key, group_key),
                "boards": group_boards,
            }

    bj_tz = timezone(timedelta(hours=8))
    now = datetime.now(bj_tz)
    generated_at = now.isoformat(timespec="seconds")
    snapshot_id = now.strftime("%Y-%m-%d-%H")  # 如 2026-03-30-08

    output = {
        "generated_at": generated_at,
        "snapshot_id": snapshot_id,
        "platform_count": len(boards),
        "grouped": grouped,
        "boards": boards,
    }

    base_dir = os.path.join(os.path.dirname(__file__), "docs", "api")
    history_dir = os.path.join(base_dir, "history")
    os.makedirs(history_dir, exist_ok=True)

    # 1. 写入最新 boards.json（覆盖）
    latest_path = os.path.join(base_dir, "boards.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 2. 写入历史快照
    snapshot_path = os.path.join(history_dir, f"{snapshot_id}.json")
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 3. 更新历史索引 history.json
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
    print(f"  latest  -> {latest_path}")
    print(f"  snapshot -> {snapshot_path}")
    print(f"  history  -> {len(history_index)} snapshots")


def _read_platform_count(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("platform_count", 0)
    except Exception:
        return 0


if __name__ == "__main__":
    main()
