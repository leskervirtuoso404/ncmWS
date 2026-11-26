"""阶段 1：抓取歌单页面与歌曲基本信息，输出 CSV。

原生数据（过程性结果）保存到 data/raw/：
- playlist_page.html   歌单页面原始 HTML
- playlist_detail.json 歌单详情原始 JSON（含完整 trackIds）
- song_detail.json     全部歌曲详情原始 JSON

有效数据输出到 data/step1_playlist.csv：
序号, 歌曲名称, song id, 总时长, 歌手, artist id, 专辑, album id
"""

from __future__ import annotations

import argparse
import csv
import json
import sys

import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

from ncm_common import (  # noqa: E402
    DATA_DIR,
    PLAYLIST_ID,
    PLAYLIST_URL,
    RAW_DIR,
    load_cookie_from_file,
    ms_to_mmss,
    new_session,
    parse_playlist_meta,
    parse_precache_song_links,
    save_json,
)

OUT_CSV = DATA_DIR / "step1_playlist.csv"
PAGE_HTML = RAW_DIR / "playlist_page.html"
DETAIL_JSON = RAW_DIR / "playlist_detail.json"
SONG_JSON = RAW_DIR / "song_detail.json"
BATCH_SIZE = 200


def fetch_page(session: requests.Session) -> str:
    resp = session.get(PLAYLIST_URL, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    PAGE_HTML.write_text(resp.text, encoding="utf-8")
    return resp.text


def fetch_playlist_detail(session: requests.Session) -> dict:
    resp = session.get(
        "https://music.163.com/api/v6/playlist/detail",
        params={"id": PLAYLIST_ID},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"歌单详情接口异常: {data.get('code')} {data.get('message')}")
    save_json(DETAIL_JSON, data)
    return data


def fetch_song_details(session: requests.Session, ids: list[int]) -> dict[int, dict]:
    """分批请求歌曲详情（单批上限约 200），返回 song_id -> song。"""
    songs: dict[int, dict] = {}
    for start in range(0, len(ids), BATCH_SIZE):
        batch = ids[start : start + BATCH_SIZE]
        payload = {
            "ids": json.dumps(batch),
            "c": json.dumps([{"id": i} for i in batch]),
        }
        resp = session.post("https://music.163.com/api/song/detail", data=payload, timeout=30)
        resp.raise_for_status()
        for song in resp.json().get("songs", []):
            songs[song["id"]] = song
        print(f"  歌曲详情 {start + len(batch)}/{len(ids)}")
    save_json(SONG_JSON, {"songs": list(songs.values())})
    return songs


def build_rows(ids: list[int], songs: dict[int, dict], limit: int | None = None) -> list[dict]:
    rows = []
    for sid in ids:
        song = songs.get(sid)
        if not song:
            continue
        artists = song.get("artists") or song.get("ar") or []
        album = song.get("album") or song.get("al") or {}
        rows.append(
            {
                "序号": len(rows) + 1,
                "歌曲名称": song.get("name", ""),
                "song id": song.get("id", sid),
                "总时长": ms_to_mmss(song.get("duration") or song.get("dt")),
                "歌手": " / ".join(a.get("name", "") for a in artists),
                "artist id": " / ".join(str(a.get("id", "")) for a in artists),
                "专辑": album.get("name", ""),
                "album id": album.get("id", ""),
            }
        )
        if limit and len(rows) >= limit:
            break
    return rows


def write_csv(rows: list[dict]) -> None:
    fields = ["序号", "歌曲名称", "song id", "总时长", "歌手", "artist id", "专辑", "album id"]
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="阶段1：抓取歌单基本信息")
    parser.add_argument("--limit", type=int, default=None, help="仅处理前 N 首（用于验证）")
    parser.add_argument("--cookie", default=None, help="登录 Cookie 字符串（可选）")
    args = parser.parse_args()

    session = new_session(args.cookie or load_cookie_from_file())

    print("[1/4] 抓取歌单页面 ...")
    html = fetch_page(session)
    meta = parse_playlist_meta(html)
    precache = parse_precache_song_links(html)
    print(f"  歌单：{meta['title']}，页面显示 {meta['track_count']} 首，预缓存链接 {len(precache)} 首")

    print("[2/4] 抓取歌单详情 ...")
    detail = fetch_playlist_detail(session)
    pl = detail["playlist"]
    ids = [t["id"] for t in pl["trackIds"]]
    print(f"  歌单《{pl['name']}》共 {len(ids)} 条曲目记录")

    print("[3/4] 抓取歌曲详情 ...")
    songs = fetch_song_details(session, ids)

    print("[4/4] 生成 CSV ...")
    rows = build_rows(ids, songs, args.limit)
    write_csv(rows)
    missing = len(ids) - len(songs)
    print(f"  已写入 {len(rows)} 条 -> {OUT_CSV}")
    if missing > 0:
        print(f"  注意：{missing} 首歌曲详情接口未返回（可能已下架/无版权）")


if __name__ == "__main__":
    main()
