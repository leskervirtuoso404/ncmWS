"""补充抓取 blues（蓝调）曲目。

背景：主歌单（data/ncm_songs_all_info.csv）中带「蓝调」标签的歌曲只有 2 首，不足以作为测试集。

方案（按艺人 + 音乐百科标签校验）：
1. 网易云「蓝调」分类歌单混杂大量 R&B/Soul（中文语境下常把 R&B 称作蓝调），
   直接按歌单取曲会引入大量错误样本，故不采用。
2. 改为以公认的蓝调艺人（B.B. King / Muddy Waters / Buddy Guy / Stevie Ray Vaughan …）
   为种子，拉取其热门歌曲；
3. 用该歌曲所属专辑的「音乐百科」数据取 songTags，**仅保留标签含「蓝调」的歌曲**，
   与主项目「歌曲类型」的判定口径一致。
4. 与主表按 song id + 歌名/歌手去重后输出。

输出：data/extra_blues.csv
原生缓存：data/raw/wiki/album_{album_id}.json、data/raw/blues_artist_songs.json
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

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent / "data"
RAW_DIR = OUT_DIR / "raw"
WIKI_DIR = RAW_DIR / "wiki"
sys.path.insert(0, str(HERE.parents[1] / "src"))

from ncm_common import (  # noqa: E402
    load_cookie_from_file,
    ms_to_mmss,
    new_session,
    save_json,
)

MAIN_CSV = HERE.parents[1] / "data" / "ncm_songs_all_info.csv"
OUT_CSV = OUT_DIR / "extra_blues.csv"
CLOUDSEARCH_API = "https://music.163.com/api/cloudsearch/get/web"
ARTIST_SONGS_API = "https://music.163.com/api/v1/artist/songs"
ALBUM_API = "https://music.163.com/api/rep/ugc/album/get"

# 公认蓝调艺人（经典 + 现代），作为补充抓取的种子
BLUES_ARTISTS = [
    "B.B. King", "Muddy Waters", "Howlin' Wolf", "Robert Johnson", "Buddy Guy",
    "Stevie Ray Vaughan", "John Lee Hooker", "Etta James", "Albert King", "Freddie King",
    "T-Bone Walker", "Lightnin' Hopkins", "Son House", "Lead Belly", "Big Bill Broonzy",
    "Willie Dixon", "Koko Taylor", "Bonnie Raitt", "Eric Clapton", "Gary Moore",
    "Joe Bonamassa", "Keb' Mo'", "Robert Cray", "Taj Mahal", "Susan Tedeschi",
    "Elmore James", "Little Walter", "Bo Diddley", "Ray Charles", "Bessie Smith",
    "Skip James", "Mississippi John Hurt", "R.L. Burnside", "Junior Wells", "Otis Rush",
    "Magic Sam", "Samantha Fish", "Christone \"Kingfish\" Ingram", "张岭", "杭天",
]


def search_artist(session: requests.Session, name: str) -> dict | None:
    try:
        resp = session.get(
            CLOUDSEARCH_API, params={"s": name, "type": 100, "limit": 5}, timeout=30
        )
        arts = (resp.json().get("result") or {}).get("artists") or []
    except (requests.RequestException, ValueError):
        return None
    target = name.strip().lower()
    for a in arts:
        if (a.get("name") or "").strip().lower() == target:
            return a
    return arts[0] if arts else None


def artist_songs(session: requests.Session, artist_id: int, limit: int, delay: float) -> list[dict]:
    songs: list[dict] = []
    offset = 0
    while len(songs) < limit:
        try:
            resp = session.get(
                ARTIST_SONGS_API,
                params={"id": artist_id, "limit": min(100, limit - len(songs)), "offset": offset},
                timeout=30,
            )
            batch = resp.json().get("songs") or []
        except (requests.RequestException, ValueError):
            break
        if not batch:
            break
        songs.extend(batch)
        offset += len(batch)
        time.sleep(delay)
    return songs[:limit]


_local = threading.local()


def _session(cookie: str) -> tuple[requests.Session, str]:
    sess = getattr(_local, "s", None)
    if sess is None:
        sess = new_session(cookie)
        _local.s = sess
        _local.csrf = sess.cookies.get("__csrf") or ""
    return sess, _local.csrf


def prefetch_albums(cookie: str, album_ids: list[int], workers: int, delay: float) -> None:
    pending = [a for a in album_ids if not (WIKI_DIR / f"album_{a}.json").exists()]
    if not pending:
        print("  专辑 wiki 缓存已完整")
        return
    print(f"  预取 {len(pending)} 个专辑 wiki（{workers} 线程）...")

    def work(album_id: int) -> bool:
        sess, csrf = _session(cookie)
        cache = WIKI_DIR / f"album_{album_id}.json"
        for attempt in range(3):
            try:
                resp = sess.get(
                    ALBUM_API, params={"albumId": album_id, "csrf_token": csrf}, timeout=30
                )
                data = resp.json()
            except (requests.RequestException, ValueError):
                time.sleep(1.5 * (attempt + 1))
                continue
            if data.get("code") == 301:
                raise RuntimeError("登录态失效，请重新运行 python src/get_cookie.py")
            if isinstance(data.get("data"), dict):
                cache.write_text(json.dumps({"data": data["data"]}, ensure_ascii=False), encoding="utf-8")
                time.sleep(delay)
                return True
            time.sleep(1.5 * (attempt + 1))
        return False

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, ok in enumerate(pool.map(work, pending), 1):
            done += ok
            if i % 100 == 0:
                print(f"    预取 {i}/{len(pending)}，成功 {done}")
    print(f"  预取完成：成功 {done}/{len(pending)}")


def album_tags_map(album_id: int) -> dict[tuple[str, int], tuple[str, str]]:
    """返回 {(歌名, songId): (语种, 标签文本)}。"""
    cache = WIKI_DIR / f"album_{album_id}.json"
    if not cache.exists():
        return {}
    try:
        data = json.loads(cache.read_text(encoding="utf-8")).get("data") or {}
    except json.JSONDecodeError:
        return {}
    out = {}
    for x in data.get("songRepVos") or []:
        tags = " / ".join(t.get("name", "") for t in (x.get("songTags") or []) if t.get("name"))
        out[(x.get("songName"), x.get("songId"))] = (x.get("language") or "", tags)
    return out


def pick(tags_map: dict, name: str, song_id: int) -> tuple[str, str] | None:
    if (name, song_id) in tags_map:
        return tags_map[(name, song_id)]
    for (n, _), v in tags_map.items():
        if n == name:
            return v
    for (_, sid), v in tags_map.items():
        if sid == song_id:
            return v
    return None


def load_existing_keys() -> tuple[set[int], set[tuple[str, str]]]:
    ids: set[int] = set()
    names: set[tuple[str, str]] = set()
    if not MAIN_CSV.exists():
        return ids, names
    with MAIN_CSV.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                ids.add(int(r["song id"]))
            except (KeyError, ValueError):
                pass
            names.add(((r.get("歌曲名称") or "").strip().lower(), (r.get("歌手") or "").strip().lower()))
    return ids, names


def main() -> None:
    parser = argparse.ArgumentParser(description="按蓝调艺人补充抓取 blues 曲目")
    parser.add_argument("--songs-per-artist", type=int, default=60, help="每个艺人抓取的热门歌曲上限")
    parser.add_argument("--workers", type=int, default=4, help="专辑 wiki 预取线程数")
    parser.add_argument("--delay", type=float, default=0.2, help="请求间隔秒数")
    args = parser.parse_args()

    cookie = load_cookie_from_file()
    if not cookie:
        raise SystemExit("缺少登录 Cookie，请先运行 python src/get_cookie.py")
    session = new_session(cookie)
    WIKI_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] 解析 {len(BLUES_ARTISTS)} 位蓝调艺人 ...")
    artist_map: dict[int, tuple[str, dict]] = {}
    for name in BLUES_ARTISTS:
        a = search_artist(session, name)
        if a:
            artist_map[a["id"]] = (a.get("name") or name, a)
            print(f"  {name} -> {a.get('id')} ({a.get('name')})")
        else:
            print(f"  {name} -> 未找到")
        time.sleep(args.delay)

    print(f"[2/4] 拉取艺人热门歌曲（每人 <= {args.songs_per_artist} 首）...")
    candidates: list[dict] = []
    for i, (aid, (name, _)) in enumerate(artist_map.items(), 1):
        songs = artist_songs(session, aid, args.songs_per_artist, args.delay)
        for s in songs:
            s["_seed_artist"] = name
        candidates.extend(songs)
        print(f"  {i}/{len(artist_map)} {name} -> {len(songs)} 首")
    save_json(RAW_DIR / "blues_artist_songs.json", {"songs": candidates})

    album_ids = list(
        dict.fromkeys(
            int((s.get("al") or s.get("album") or {}).get("id") or 0) for s in candidates
        )
    )
    album_ids = [a for a in album_ids if a]
    print(f"[3/4] 共 {len(candidates)} 首候选，涉及 {len(album_ids)} 张专辑，预取 wiki ...")
    prefetch_albums(cookie, album_ids, args.workers, args.delay)

    print("[4/4] 校验「蓝调」标签并去重输出 ...")
    existing_ids, existing_names = load_existing_keys()
    tag_cache: dict[int, dict] = {}
    rows = []
    seen_names: set[tuple[str, str]] = set()
    stats = {"no_album": 0, "no_wiki": 0, "not_blues": 0, "kept": 0}
    for s in candidates:
        sid = s.get("id")
        name = s.get("name", "")
        al = s.get("al") or s.get("album") or {}
        album_id = int(al.get("id") or 0)
        if not album_id:
            stats["no_album"] += 1
            continue
        if album_id not in tag_cache:
            tag_cache[album_id] = album_tags_map(album_id)
        hit = pick(tag_cache[album_id], name, sid)
        if not hit:
            stats["no_wiki"] += 1
            continue
        language, tags = hit
        if "蓝调" not in tags:
            stats["not_blues"] += 1
            continue
        artists = s.get("ar") or s.get("artists") or []
        artist_text = " / ".join(a.get("name", "") for a in artists) or s.get("_seed_artist", "")
        key = (name.strip().lower(), artist_text.strip().lower())
        if sid in existing_ids or key in existing_names or key in seen_names:
            continue
        seen_names.add(key)
        stats["kept"] += 1
        rows.append(
            {
                "序号": "",
                "歌曲名称": name,
                "song id": sid,
                "总时长": ms_to_mmss(s.get("dt") or s.get("duration")),
                "歌手": artist_text,
                "artist id": " / ".join(str(a.get("id", "")) for a in artists),
                "专辑": al.get("name", ""),
                "album id": album_id,
                "语种": language,
                "歌曲类型": tags,
                "数据来源": "blues_artist_wiki",
            }
        )

    rows.sort(key=lambda r: (r["歌手"], r["歌曲名称"]))
    for i, r in enumerate(rows, 1):
        r["序号"] = i

    fields = ["序号", "歌曲名称", "song id", "总时长", "歌手", "artist id",
              "专辑", "album id", "语种", "歌曲类型", "数据来源"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  统计 {stats}")
    print(f"  新增 blues 曲目 {len(rows)} 首 -> {OUT_CSV}")


if __name__ == "__main__":
    main()
