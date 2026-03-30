"""
热榜数据生成脚本 — 供 GitHub Actions 调用

用法:
    python generate.py

输出:
    docs/api/boards.json  — 所有平台热榜数据（静态 JSON）
"""
import json
import os
import sys
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
    output = {
        "generated_at": datetime.now(bj_tz).isoformat(timespec="seconds"),
        "platform_count": len(boards),
        "grouped": grouped,
        "boards": boards,
    }

    # 写入 docs/api/boards.json
    out_dir = os.path.join(os.path.dirname(__file__), "docs", "api")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "boards.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(boards)} platforms -> {out_path}")


if __name__ == "__main__":
    main()
