"""阶段 3：汇总阶段 1、阶段 2 的结果，输出两份 CSV。

- data/ncm_songs_all_info.csv  全部信息（基本信息 + 语种 + 歌曲类型）
- data/ncm_songs_key_info.csv  关键信息（歌曲名称、时长、歌手、专辑、语种、歌曲类型）
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ncm_common import DATA_DIR  # noqa: E402

STEP1_CSV = DATA_DIR / "step1_playlist.csv"
STEP2_CSV = DATA_DIR / "step2_style.csv"
ALL_CSV = DATA_DIR / "ncm_songs_all_info.csv"
KEY_CSV = DATA_DIR / "ncm_songs_key_info.csv"

ALL_FIELDS = [
    "序号",
    "歌曲名称",
    "song id",
    "总时长",
    "歌手",
    "artist id",
    "专辑",
    "album id",
    "语种",
    "歌曲类型",
]
KEY_FIELDS = ["歌曲名称", "时长", "歌手", "专辑", "语种", "歌曲类型"]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"缺少文件：{path}")
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main() -> None:
    basic = read_csv(STEP1_CSV)
    style = {row["song id"]: row for row in read_csv(STEP2_CSV)}

    all_rows, key_rows, missing = [], [], 0
    for row in basic:
        style_row = style.get(row["song id"])
        if style_row is None:
            missing += 1
            style_row = {"语种": "", "歌曲类型": ""}
        all_rows.append(
            {
                "序号": row["序号"],
                "歌曲名称": row["歌曲名称"],
                "song id": row["song id"],
                "总时长": row["总时长"],
                "歌手": row["歌手"],
                "artist id": row["artist id"],
                "专辑": row["专辑"],
                "album id": row["album id"],
                "语种": style_row["语种"],
                "歌曲类型": style_row["歌曲类型"],
            }
        )
        key_rows.append(
            {
                "歌曲名称": row["歌曲名称"],
                "时长": row["总时长"],
                "歌手": row["歌手"],
                "专辑": row["专辑"],
                "语种": style_row["语种"],
                "歌曲类型": style_row["歌曲类型"],
            }
        )

    with ALL_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=ALL_FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)
    with KEY_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=KEY_FIELDS)
        writer.writeheader()
        writer.writerows(key_rows)

    empty_lang = sum(1 for r in all_rows if not r["语种"])
    empty_genre = sum(1 for r in all_rows if not r["歌曲类型"])
    print(f"全部信息 {len(all_rows)} 条 -> {ALL_CSV}")
    print(f"关键信息 {len(key_rows)} 条 -> {KEY_CSV}")
    print(f"语种为空 {empty_lang} 条，歌曲类型为空 {empty_genre} 条，未匹配阶段2 {missing} 条")


if __name__ == "__main__":
    main()
