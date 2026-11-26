"""按指定歌单构建 blues/classical/country/hiphop/jazz/pop/rock 七流派测试集。

需求：
1. 七种流派各对应一个给定歌单；
2. 按歌单顺序逐首抓取歌曲信息；
3. 仅当歌曲的「歌曲类型」包含该流派标签时计入（blues->蓝调、classical->古典 …）；
4. 若类型不符则继续向后扫描，直到该类别收满 100 首；
   若给定歌单耗尽仍不足 100 首，则从同风格「分类歌单」继续补足（同样需通过标签校验）。

数据来源：
- 歌单曲目：/api/v6/playlist/detail
- 分类歌单：/api/playlist/list
- 歌曲信息：/api/song/detail（批量）
- 语种/歌曲类型：音乐百科 /api/rep/ugc/album/get（需登录 Cookie，data/cookies.json）

输出（genre_testset/data/）：
- testset_<genre>.csv   各类前 100 首符合风格的曲目
- testset_all.csv       七类合并
- testset_summary.csv   各类抓取统计
原生缓存（data/raw/）：playlist_*.json、song_detail_*.json、cat_*_playlists.json、wiki/album_*.json
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

PLAYLIST_DETAIL_API = "https://music.163.com/api/v6/playlist/detail"
PLAYLIST_LIST_API = "https://music.163.com/api/playlist/list"
SONG_DETAIL_API = "https://music.163.com/api/song/detail"
ALBUM_API = "https://music.163.com/api/rep/ugc/album/get"
BATCH_SIZE = 200
CHUNK = 150

# genre -> 给定歌单 id、判定标签、补充抓取用的分类歌单 cat
GENRES: list[dict] = [
    {"genre": "blues", "tag": "蓝调", "playlist_id": "102463641", "cat": "蓝调"},
    {"genre": "classical", "tag": "古典", "playlist_id": "167900089", "cat": "古典"},
    {"genre": "country", "tag": "乡村", "playlist_id": "697173945", "cat": "乡村"},
    {"genre": "hiphop", "tag": "嘻哈说唱", "playlist_id": "439484002", "cat": "说唱"},
    {"genre": "jazz", "tag": "爵士", "playlist_id": "2829895462", "cat": "爵士"},
    {"genre": "pop", "tag": "流行", "playlist_id": "18639113421", "cat": "流行"},
    {"genre": "rock", "tag": "摇滚", "playlist_id": "18639045526", "cat": "摇滚"},
]

ZH2EN = {
    "流行": "pop", "电子": "electronic", "摇滚": "rock", "嘻哈说唱": "hiphop",
    "原声带": "soundtrack", "R&B": "rnb", "另类/独立": "alternative", "二次元": "acg",
    "轻音乐": "easy_listening", "民谣": "folk", "古典": "classical", "朋克": "punk",
    "放克": "funk", "国风": "guofeng", "金属": "metal", "其他": "other",
    "乡村": "country", "爵士": "jazz", "新世纪": "new_age", "唱作人": "singer_songwriter",
    "纯演奏音乐": "instrumental", "节日音乐": "holiday", "宗教": "religious",
    "世界音乐": "world", "儿童": "children", "实验": "experimental", "舞台": "stage",
    "慢摇DJ": "slow_dj", "蓝调": "blues", "雷鬼": "reggae",
    "中国传统特色": "chinese_traditional", "世界乐器体裁": "world_instrument",
    "拉丁音乐": "latin",
}


def tags_to_en(text: str) -> str:
    return " / ".join(ZH2EN.get(t.strip(), t.strip()) for t in (text or "").split(" / ") if t.strip())


def split_tags(text: str) -> list[str]:
    return [t.strip() for t in (text or "").split(" / ") if t.strip()]


def fetch_playlist(session: requests.Session, playlist_id: str) -> dict:
    cache = RAW_DIR / f"playlist_{playlist_id}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    resp = session.get(PLAYLIST_DETAIL_API, params={"id": playlist_id}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("playlist"):
        raise RuntimeError(f"歌单 {playlist_id} 获取失败: {data.get('code')} {data.get('message')}")
    save_json(cache, data)
    return data


def fetch_song_details(session: requests.Session, ids: list[int], playlist_id: str) -> dict[int, dict]:
    cache = RAW_DIR / f"song_detail_{playlist_id}.json"
    if cache.exists():
        songs = json.loads(cache.read_text(encoding="utf-8")).get("songs", [])
        if len(songs) >= len(ids):
            return {s["id"]: s for s in songs}
    songs: dict[int, dict] = {}
    for start in range(0, len(ids), BATCH_SIZE):
        batch = ids[start : start + BATCH_SIZE]
        payload = {"ids": json.dumps(batch), "c": json.dumps([{"id": i} for i in batch])}
        resp = session.post(SONG_DETAIL_API, data=payload, timeout=30)
        for song in resp.json().get("songs", []):
            songs[song["id"]] = song
    save_json(cache, {"songs": list(songs.values())})
    return songs


def fetch_category_playlists(session: requests.Session, cat: str, genre: str) -> list[dict]:
    cache = RAW_DIR / f"cat_{genre}_playlists.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8")).get("playlists", [])
    resp = session.get(
        PLAYLIST_LIST_API,
        params={"cat": cat, "order": "hot", "offset": 0, "limit": 50, "total": "true"},
        timeout=30,
    )
    playlists = resp.json().get("playlists", [])
    save_json(cache, {"playlists": playlists})
    return playlists


_local = threading.local()


def _session(cookie: str) -> tuple[requests.Session, str]:
    sess = getattr(_local, "s", None)
    if sess is None:
        sess = new_session(cookie)
        _local.s = sess
        _local.csrf = sess.cookies.get("__csrf") or ""
    return sess, _local.csrf


def prefetch_albums(cookie: str, album_ids: list[int], workers: int, delay: float) -> None:
    pending = list(dict.fromkeys(a for a in album_ids if a and not (WIKI_DIR / f"album_{a}.json").exists()))
    if not pending:
        return

    def work(album_id: int) -> bool:
        sess, csrf = _session(cookie)
        cache = WIKI_DIR / f"album_{album_id}.json"
        for attempt in range(3):
            try:
                resp = sess.get(ALBUM_API, params={"albumId": album_id, "csrf_token": csrf}, timeout=30)
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

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(work, pending))


def album_tags_map(album_id: int) -> dict[tuple[str, int], tuple[str, str]]:
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


def scan_playlist(session, cookie, playlist_id, tag, need, workers, delay, seen_ids, seen_names, source):
    """按歌单顺序扫描，返回符合 tag 的曲目（最多 need 首）及统计。"""
    detail = fetch_playlist(session, str(playlist_id))
    pl = detail["playlist"]
    ids = [t["id"] for t in pl.get("trackIds", [])]
    songs = fetch_song_details(session, ids, str(playlist_id))

    out: list[dict] = []
    st = {"扫描曲目数": 0, "类型不符": 0, "无类型信息": 0, "重复跳过": 0}
    tag_cache: dict[int, dict] = {}
    idx = 0
    while len(out) < need and idx < len(ids):
        chunk = ids[idx : idx + CHUNK]
        album_ids = []
        for sid in chunk:
            song = songs.get(sid)
            if song:
                album_ids.append(int((song.get("al") or song.get("album") or {}).get("id") or 0))
        prefetch_albums(cookie, album_ids, workers, delay)

        for off, sid in enumerate(chunk):
            if len(out) >= need:
                break
            st["扫描曲目数"] += 1
            song = songs.get(sid)
            if not song:
                st["无类型信息"] += 1
                continue
            al = song.get("al") or song.get("album") or {}
            album_id = int(al.get("id") or 0)
            if album_id not in tag_cache:
                tag_cache[album_id] = album_tags_map(album_id) if album_id else {}
            hit = pick(tag_cache[album_id], song.get("name", ""), sid) if album_id else None
            if not hit:
                st["无类型信息"] += 1
                continue
            language, tags = hit
            if tag not in split_tags(tags):
                st["类型不符"] += 1
                continue
            artists = song.get("ar") or song.get("artists") or []
            artist_text = " / ".join(a.get("name", "") for a in artists)
            key = ((song.get("name") or "").strip().lower(), artist_text.strip().lower())
            if sid in seen_ids or key in seen_names:
                st["重复跳过"] += 1
                continue
            seen_ids.add(sid)
            seen_names.add(key)
            out.append(
                {
                    "歌曲名称": song.get("name", ""),
                    "song id": sid,
                    "总时长": ms_to_mmss(song.get("dt") or song.get("duration")),
                    "歌手": artist_text,
                    "artist id": " / ".join(str(a.get("id", "")) for a in artists),
                    "专辑": al.get("name", ""),
                    "album id": album_id,
                    "语种": language,
                    "歌曲类型": tags,
                    "歌曲类型_en": tags_to_en(tags),
                    "歌单位置": idx + off + 1,
                    "数据来源": source,
                }
            )
        idx += len(chunk)
        print(f"    扫描 {min(idx, len(ids))}/{len(ids)}，命中 {len(out)}", flush=True)
    return pl, out, st, len(ids)


def collect_genre(session, cookie, cfg, target, workers, delay, max_supplement=20):
    genre, tag = cfg["genre"], cfg["tag"]
    seen_ids: set[int] = set()
    seen_names: set[tuple[str, str]] = set()

    pl, rows, st, total = scan_playlist(
        session, cookie, cfg["playlist_id"], tag, target, workers, delay,
        seen_ids, seen_names, "given_playlist",
    )
    stat = {
        "genre": genre,
        "给定歌单名称": pl.get("name", ""),
        "给定歌单 id": cfg["playlist_id"],
        "给定歌单曲目数": total,
        "扫描曲目数": st["扫描曲目数"],
        "类型不符": st["类型不符"],
        "无类型信息": st["无类型信息"],
        "重复跳过": st["重复跳过"],
        "补充歌单数": 0,
        "补充曲目数": 0,
        "命中数": len(rows),
        "是否满额": "是",
    }
    print(f"  给定歌单命中 {len(rows)}/{target}", flush=True)

    if len(rows) < target:
        print(f"  不足 {target} 首，从「{cfg['cat']}」分类歌单补足 ...", flush=True)
        playlists = fetch_category_playlists(session, cfg["cat"], genre)
        for p in playlists[:max_supplement]:
            if len(rows) >= target:
                break
            if str(p["id"]) == cfg["playlist_id"]:
                continue
            _, got, st2, _ = scan_playlist(
                session, cookie, p["id"], tag, target - len(rows), workers, delay,
                seen_ids, seen_names, f"supplement_playlist:{p['id']}",
            )
            stat["扫描曲目数"] += st2["扫描曲目数"]
            stat["类型不符"] += st2["类型不符"]
            stat["无类型信息"] += st2["无类型信息"]
            stat["重复跳过"] += st2["重复跳过"]
            if got:
                stat["补充歌单数"] += 1
                stat["补充曲目数"] += len(got)
                rows.extend(got)
                print(f"    补充歌单 {p['id']}「{p.get('name','')[:20]}」+{len(got)} 首", flush=True)

    stat["命中数"] = len(rows)
    stat["是否满额"] = "是" if len(rows) >= target else "否（素材不足）"
    for i, r in enumerate(rows, 1):
        r["序号"] = i
        r["genre"] = genre
    return rows, stat


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="按指定歌单构建七流派测试集")
    parser.add_argument("--target", type=int, default=100, help="每类需要的曲目数")
    parser.add_argument("--workers", type=int, default=4, help="专辑 wiki 预取线程数")
    parser.add_argument("--delay", type=float, default=0.2, help="请求间隔秒数")
    parser.add_argument("--max-supplement", type=int, default=20, help="每类最多补充多少个分类歌单")
    args = parser.parse_args()

    cookie = load_cookie_from_file()
    if not cookie:
        raise SystemExit("缺少登录 Cookie，请先运行 python src/get_cookie.py")
    session = new_session(cookie)
    WIKI_DIR.mkdir(parents=True, exist_ok=True)

    fields = ["序号", "歌曲名称", "song id", "总时长", "歌手", "artist id", "专辑", "album id",
              "语种", "歌曲类型", "歌曲类型_en", "genre", "歌单位置", "数据来源"]
    summary = []
    all_rows = []

    for cfg in GENRES:
        print(f"[{cfg['genre']}] 歌单 {cfg['playlist_id']} ...", flush=True)
        rows, stat = collect_genre(session, cookie, cfg, args.target, args.workers, args.delay, args.max_supplement)
        write_csv(OUT_DIR / f"testset_{cfg['genre']}.csv", fields, rows)
        summary.append(stat)
        all_rows.extend(rows)
        print(f"  -> {len(rows)} 首（补充 {stat['补充曲目数']}，{stat['是否满额']}）", flush=True)

    write_csv(OUT_DIR / "testset_all.csv", fields, all_rows)
    write_csv(
        OUT_DIR / "testset_summary.csv",
        ["genre", "给定歌单名称", "给定歌单 id", "给定歌单曲目数", "扫描曲目数", "命中数",
         "类型不符", "无类型信息", "重复跳过", "补充歌单数", "补充曲目数", "是否满额"],
        summary,
    )
    print(f"合计 {len(all_rows)} 首 -> {OUT_DIR}")


if __name__ == "__main__":
    main()
