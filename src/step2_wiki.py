"""阶段 2：获取每首歌的语种与歌曲类型。

思路（对应 task.md 2.1）：
1. 用阶段 1 得到的 song id / album id 构造网易云 wiki 页面 URL：
   https://music.163.com/#/wiki/song?songId={song_id}&type=1
   https://music.163.com/#/wiki/album?albumId={album_id}
2. 按 album id 拉取该专辑在「音乐百科」中的全部歌曲信息（含 language / songTags），
   在专辑歌曲列表中按歌曲名称（songId 兜底）匹配到目标歌曲，得到语种与歌曲类型。
3. 专辑级数据缺失时，退回歌曲级接口补全。

该接口需要登录 Cookie（data/cookies.json，由 src/get_cookie.py 生成）。

原生数据：data/raw/wiki/album_{album_id}.json
有效数据：data/step2_style.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ncm_common import (  # noqa: E402
    DATA_DIR,
    RAW_DIR,
    load_cookie_from_file,
    new_session,
)

STEP1_CSV = DATA_DIR / "step1_playlist.csv"
OUT_CSV = DATA_DIR / "step2_style.csv"
WIKI_RAW_DIR = RAW_DIR / "wiki"

ALBUM_WIKI_URL = "https://music.163.com/#/wiki/album?albumId={album_id}"
SONG_WIKI_URL = "https://music.163.com/#/wiki/song?songId={song_id}&type=1"
ALBUM_API = "https://music.163.com/api/rep/ugc/album/get"
SONG_API = "https://music.163.com/api/rep/ugc/song/get"


def load_step1(limit: int | None) -> list[dict]:
    with STEP1_CSV.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


class WikiClient:
    def __init__(self, session: requests.Session, delay: float = 0.3):
        self.session = session
        self.csrf = session.cookies.get("__csrf") or ""
        self.delay = delay
        self.calls = 0

    def _get(self, url: str, params: dict) -> dict | None:
        params = {**params, "csrf_token": self.csrf}
        for attempt in range(3):
            try:
                resp = self.session.get(url, params=params, timeout=30)
                data = resp.json()
            except (requests.RequestException, ValueError):
                time.sleep(1.5 * (attempt + 1))
                continue
            if data.get("code") == 301:
                raise RuntimeError(
                    "登录态失效（接口返回 301，前端会跳转登录页）。请重新运行 python src/get_cookie.py"
                )
            if isinstance(data.get("data"), dict):
                self.calls += 1
                time.sleep(self.delay)
                return data["data"]
            time.sleep(1.5 * (attempt + 1))
        return None

    def album(self, album_id: int) -> dict | None:
        cache = WIKI_RAW_DIR / f"album_{album_id}.json"
        if cache.exists():
            try:
                return json.loads(cache.read_text(encoding="utf-8")).get("data")
            except json.JSONDecodeError:
                pass
        data = self._get(ALBUM_API, {"albumId": album_id})
        if data:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(
                json.dumps({"data": data}, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return data

    def song(self, song_id: int) -> dict | None:
        cache = WIKI_RAW_DIR / f"song_{song_id}.json"
        if cache.exists():
            try:
                return json.loads(cache.read_text(encoding="utf-8")).get("data")
            except json.JSONDecodeError:
                pass
        data = self._get(SONG_API, {"songId": song_id})
        if data:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(
                json.dumps({"data": data}, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return data


def tags_to_text(tags) -> str:
    if not tags:
        return ""
    return " / ".join(t.get("name", "") for t in tags if t.get("name"))


_local = threading.local()


def _thread_session(cookie: str) -> tuple[requests.Session, str]:
    """每个线程复用独立的会话。"""
    sess = getattr(_local, "session", None)
    if sess is None:
        sess = new_session(cookie)
        _local.session = sess
        _local.csrf = sess.cookies.get("__csrf") or ""
    return sess, _local.csrf


def prefetch_albums(cookie: str, album_ids: list[int], delay: float, workers: int) -> None:
    """多线程预取尚未缓存的专辑 wiki 数据，写入 data/raw/wiki/album_{id}.json。"""
    pending = [a for a in album_ids if not (WIKI_RAW_DIR / f"album_{a}.json").exists()]
    if not pending:
        print("专辑缓存已完整，跳过预取", flush=True)
        return
    print(f"预取 {len(pending)} 个专辑（{workers} 线程）...", flush=True)

    def work(album_id: int) -> bool:
        sess, csrf = _thread_session(cookie)
        for attempt in range(3):
            try:
                resp = sess.get(
                    ALBUM_API,
                    params={"albumId": album_id, "csrf_token": csrf},
                    timeout=30,
                )
                data = resp.json()
            except (requests.RequestException, ValueError):
                time.sleep(1.5 * (attempt + 1))
                continue
            if data.get("code") == 301:
                raise RuntimeError(
                    "登录态失效（接口返回 301）。请重新运行 python src/get_cookie.py"
                )
            if isinstance(data.get("data"), dict):
                cache = WIKI_RAW_DIR / f"album_{album_id}.json"
                cache.write_text(
                    json.dumps({"data": data["data"]}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                time.sleep(delay)
                return True
            time.sleep(1.5 * (attempt + 1))
        return False

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, ok in enumerate(pool.map(work, pending), 1):
            done += ok
            if i % 100 == 0:
                print(f"  预取 {i}/{len(pending)}，成功 {done}", flush=True)
    print(f"预取完成：成功 {done}/{len(pending)}", flush=True)


def pick_song(album_data: dict, song_name: str, song_id: int) -> dict | None:
    """在专辑歌曲列表中按名称匹配（同名多版本时用 songId 消歧），最后用 songId 兜底。"""
    songs = album_data.get("songRepVos") or []
    for song in songs:
        if song.get("songName") == song_name and song.get("songId") == song_id:
            return song
    for song in songs:
        if song.get("songName") == song_name:
            return song
    for song in songs:
        if song.get("songId") == song_id:
            return song
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="阶段2：获取语种与歌曲类型")
    parser.add_argument("--limit", type=int, default=None, help="仅处理前 N 首（用于验证）")
    parser.add_argument("--delay", type=float, default=0.3, help="每次请求间隔秒数")
    parser.add_argument("--workers", type=int, default=4, help="预取专辑时的并发线程数")
    parser.add_argument("--cookie", default=None, help="登录 Cookie 字符串（可选）")
    args = parser.parse_args()

    cookie = args.cookie or load_cookie_from_file()
    if not cookie:
        raise SystemExit("缺少登录 Cookie，请先运行 python src/get_cookie.py")

    rows = load_step1(args.limit)
    album_ids = list(dict.fromkeys(int(r["album id"]) for r in rows))
    prefetch_albums(cookie, album_ids, args.delay, args.workers)
    client = WikiClient(new_session(cookie), delay=args.delay)

    album_cache: dict[int, dict | None] = {}
    out_rows = []
    stats = {"album_hit": 0, "song_fallback": 0, "missing": 0}

    for i, row in enumerate(rows, 1):
        song_id = int(row["song id"])
        album_id = int(row["album id"])
        song_name = row["歌曲名称"]

        album_data = album_cache.get(album_id)
        if album_id not in album_cache:
            album_data = client.album(album_id)
            album_cache[album_id] = album_data

        language = genre = ""
        source = "album"
        matched = pick_song(album_data, song_name, song_id) if album_data else None
        if matched:
            language = matched.get("language") or ""
            genre = tags_to_text(matched.get("songTags"))
            stats["album_hit"] += 1

        if not language or not genre:
            song_data = client.song(song_id)
            if song_data:
                language = language or (song_data.get("language") or "")
                genre = genre or tags_to_text(song_data.get("songTags"))
                source = "song"
                if language or genre:
                    stats["song_fallback"] += 1
        if not language and not genre:
            source = "missing"
            stats["missing"] += 1

        out_rows.append(
            {
                "序号": row["序号"],
                "歌曲名称": song_name,
                "song id": song_id,
                "歌手": row["歌手"],
                "专辑": row["专辑"],
                "album id": album_id,
                "语种": language,
                "歌曲类型": genre,
                "wiki_album_url": ALBUM_WIKI_URL.format(album_id=album_id),
                "wiki_song_url": SONG_WIKI_URL.format(song_id=song_id),
                "数据来源": source,
            }
        )
        if i % 20 == 0 or i == len(rows):
            print(f"  进度 {i}/{len(rows)}  专辑请求 {len(album_cache)}  {stats}", flush=True)

    fields = [
        "序号",
        "歌曲名称",
        "song id",
        "歌手",
        "专辑",
        "album id",
        "语种",
        "歌曲类型",
        "wiki_album_url",
        "wiki_song_url",
        "数据来源",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"已写入 {len(out_rows)} 条 -> {OUT_CSV}")


if __name__ == "__main__":
    main()
