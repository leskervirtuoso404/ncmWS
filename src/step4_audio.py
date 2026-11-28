"""阶段 4：按 song id / 歌曲 URL 抓取音频文件。

在歌曲详情页（https://music.163.com/#/song?id=xxx）点击播放时，前端实际请求：
    GET https://music.163.com/api/song/enhance/player/url/v1
        ?ids=[{song_id}]&level=exhigh&encodeType=aac
返回 data[].url 即音频直链（通常是 .m4a，位于 m7xx.music.126.net），
携带登录 Cookie 请求该地址即可下载完整音频文件。

用法：
    python src/step4_audio.py --playlist 697173945 --limit 5
    python src/step4_audio.py --id 1477334 --id 26459609
    python src/step4_audio.py --url "https://music.163.com/#/song?id=1477334"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import requests

from ncm_common import BASE_HEADERS, ROOT, load_cookie_from_file, new_session

PLAY_URL_API = "https://music.163.com/api/song/enhance/player/url/v1"
PLAY_URL_API_LEGACY = "https://music.163.com/api/song/enhance/player/url"
SONG_DETAIL_API = "https://music.163.com/api/song/detail"
PLAYLIST_DETAIL_API = "https://music.163.com/api/v6/playlist/detail"

DEFAULT_OUT = ROOT / "data" / "audio"
CHUNK = 1 << 16
ILLEGAL = re.compile(r'[\\/:*?"<>|\r\n\t]')


def parse_song_id(text: str) -> int:
    """从纯数字或歌曲 URL 中提取 song id。"""
    text = text.strip()
    if text.isdigit():
        return int(text)
    m = re.search(r"[?&#]id=(\d+)", text)
    if not m:
        raise ValueError(f"无法从 {text!r} 解析 song id")
    return int(m.group(1))


def fetch_playlist_ids(session: requests.Session, playlist_id: str, limit: int | None) -> list[int]:
    r = session.get(PLAYLIST_DETAIL_API, params={"id": playlist_id, "n": 1000, "s": 0}, timeout=30)
    r.raise_for_status()
    ids = [t["id"] for t in r.json()["playlist"].get("trackIds", [])]
    return ids[:limit] if limit else ids


def fetch_song_meta(session: requests.Session, song_id: int) -> dict:
    """取歌曲名称与歌手，用于命名文件。"""
    params = {"ids": json.dumps([song_id]), "c": json.dumps([{"id": song_id}])}
    r = session.get(SONG_DETAIL_API, params=params, timeout=30)
    r.raise_for_status()
    songs = r.json().get("songs") or []
    if not songs:
        raise RuntimeError(f"song id {song_id} 不存在或无版权")
    song = songs[0]
    artists = [a.get("name", "") for a in (song.get("ar") or song.get("artists") or []) if a.get("name")]
    return {"name": song.get("name", ""), "artists": artists}


def fetch_play_url(session: requests.Session, song_id: int, level: str) -> dict:
    """返回 {url, type, size, br}；无版权/无音源时 url 为空。"""
    r = session.get(PLAY_URL_API, params={
        "ids": json.dumps([song_id]), "level": level, "encodeType": "aac",
    }, timeout=30)
    item = ((r.json().get("data") or [{}])[0]) if r.ok else {}
    if not item.get("url"):
        r2 = session.get(PLAY_URL_API_LEGACY, params={"ids": json.dumps([song_id]), "br": 320000}, timeout=30)
        item = ((r2.json().get("data") or [{}])[0]) if r2.ok else {}
    return item


def build_filename(meta: dict, url: str) -> str:
    """命名规则与 genre_testset/dataset 一致：`歌手 - 歌曲名称.扩展名`，多歌手用 ` & ` 连接。"""
    singer = " & ".join(meta["artists"]) or "未知歌手"
    stem = ILLEGAL.sub("_", f"{singer} - {meta['name']}").strip().strip(".")
    stem = re.sub(r"\s+", " ", stem)
    suffix = Path(url.split("?")[0]).suffix.lower()
    return stem + (suffix if suffix in {".m4a", ".mp3", ".flac", ".ogg", ".wav"} else ".m4a")


def download(session: requests.Session, url: str, path: Path) -> int:
    """流式下载到临时文件后重命名，返回字节数。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    with session.get(url, headers={**BASE_HEADERS, "Accept": "*/*"}, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(CHUNK):
                if chunk:
                    f.write(chunk)
    size = tmp.stat().st_size
    if size < 100 * 1024:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"文件过小（{size} 字节），可能不是有效音频")
    tmp.replace(path)
    return size


def main() -> int:
    ap = argparse.ArgumentParser(description="按 song id / 歌曲 URL 抓取音频文件")
    ap.add_argument("--id", action="append", default=[], help="song id，可重复")
    ap.add_argument("--url", action="append", default=[], help="歌曲详情页 URL，可重复")
    ap.add_argument("--playlist", help="歌单 id，取歌单内歌曲（可用 --limit 限制数量）")
    ap.add_argument("--limit", type=int, help="配合 --playlist，只取前 N 首")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help=f"输出目录，默认 {DEFAULT_OUT}")
    ap.add_argument("--level", default="exhigh", choices=["standard", "higher", "exhigh", "lossless"],
                    help="音质级别，默认 exhigh（对应 .m4a）")
    ap.add_argument("--overwrite", action="store_true", help="覆盖已存在的同名文件")
    args = ap.parse_args()

    cookie = load_cookie_from_file()
    if not cookie:
        print("提示：未找到 data/cookies.json，未登录状态下部分歌曲拿不到播放地址", file=sys.stderr)
    session = new_session(cookie)

    ids = [parse_song_id(x) for x in args.id + args.url]
    if args.playlist:
        ids += fetch_playlist_ids(session, args.playlist, args.limit)
    if not ids:
        ap.error("请通过 --id / --url / --playlist 指定至少一首歌曲")
    ids = list(dict.fromkeys(ids))

    out_dir = Path(args.out)
    ok, skipped, failed = 0, 0, 0
    for i, sid in enumerate(ids, 1):
        tag = f"[{i}/{len(ids)}] {sid}"
        try:
            meta = fetch_song_meta(session, sid)
            item = fetch_play_url(session, sid, args.level)
            if not item.get("url"):
                print(f"{tag} 无音源（无版权/下架/需付费），跳过")
                failed += 1
                continue
            path = out_dir / build_filename(meta, item["url"])
            if path.exists() and not args.overwrite:
                print(f"{tag} 已存在，跳过：{path.name}")
                skipped += 1
                continue
            size = download(session, item["url"], path)
            print(f"{tag} {path.name}  ({size / 1024 / 1024:.2f} MB, {item.get('type') or '?'})")
            ok += 1
        except (requests.RequestException, RuntimeError, ValueError) as e:
            print(f"{tag} 失败：{e}")
            failed += 1

    print(f"\n完成：成功 {ok}，跳过 {skipped}，失败 {failed}，输出目录 {out_dir}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
