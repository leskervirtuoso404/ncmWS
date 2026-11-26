"""网易云音乐歌单爬虫 - 公共配置与工具。"""

from __future__ import annotations

import json
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

PLAYLIST_ID = "565910665"
PLAYLIST_URL = f"https://music.163.com/playlist?id={PLAYLIST_ID}"

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://music.163.com/",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

COOKIE_FILE = DATA_DIR / "cookies.json"


def new_session(cookie: str | None = None) -> requests.Session:
    """创建会话；cookie 形如 'MUSIC_U=xxx; __csrf=yyy'。"""
    s = requests.Session()
    s.headers.update(BASE_HEADERS)
    if cookie:
        for part in cookie.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                s.cookies.set(k.strip(), v.strip(), domain="music.163.com")
    return s


def load_cookie_from_file() -> str | None:
    """从 data/cookies.json 读取 cookie 字符串（若存在）。"""
    if not COOKIE_FILE.exists():
        return None
    try:
        obj = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        if isinstance(obj.get("cookie"), str):
            return obj["cookie"]
        items = obj.get("cookies")
        if isinstance(items, list):
            return "; ".join(f"{c['name']}={c['value']}" for c in items)
    return None


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def ms_to_mmss(ms: int | float | None) -> str:
    """毫秒转 mm:ss。"""
    if not ms:
        return "00:00"
    total = int(round(float(ms) / 1000))
    return f"{total // 60:02d}:{total % 60:02d}"


def parse_precache_song_links(html: str) -> list[dict]:
    """解析页面服务端预缓存的歌曲链接（f-hide 列表，仅前若干首）。"""
    block = re.search(r'<ul class="f-hide">(.*?)</ul>', html, re.S)
    if not block:
        return []
    return [
        {"name": name, "song_id": int(sid)}
        for sid, name in re.findall(r'<a href="/song\?id=(\d+)">(.*?)</a>', block.group(1))
    ]


def parse_playlist_meta(html: str) -> dict:
    """从歌单页面 HTML 提取歌单标题与歌曲总数。"""
    title = re.search(r'<h2 class="f-ff2 f-brk"[^>]*>(.*?)</h2>', html, re.S)
    count = re.search(r'id="playlist-track-count">(\d+)<', html)
    return {
        "title": title.group(1) if title else None,
        "track_count": int(count.group(1)) if count else None,
    }
