"""按流派 CSV 批量下载音频文件（country / hiphop）。

复用 ncmWS/src/step4_audio.py 的抓取方式：
1. 从 genre_testset/data/testset_<genre>.csv 读取 song id；
2. 批量取歌曲名称与歌手（/api/song/detail）；
3. 逐首请求播放直链（/api/song/enhance/player/url/v1?level=exhigh&encodeType=aac，需登录 Cookie）；
4. 下载直链文件，按「歌手 - 歌曲名称.扩展名」命名（多歌手用 ` & ` 连接），
   保存到 genre_testset/dataset/<genre>/ 下。

用法：
    python genre_testset/src/download_audio.py                       # 默认 country + hiphop
    python genre_testset/src/download_audio.py --genres country      # 只下某一流派
    python genre_testset/src/download_audio.py --genres country --limit 2   # 先试 2 首

已存在的同名文件默认跳过，`--overwrite` 可覆盖；无音源（直链为空）的歌曲计入失败。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
TESTSET_DIR = HERE.parent
DATA_DIR = TESTSET_DIR / "data"
DATASET_DIR = TESTSET_DIR / "dataset"
sys.path.insert(0, str(HERE.parents[1] / "src"))

from ncm_common import load_cookie_from_file, new_session  # noqa: E402
from step4_audio import build_filename, download, fetch_play_url  # noqa: E402

SONG_DETAIL_API = "https://music.163.com/api/song/detail"
BATCH_SIZE = 200

COOKIE = load_cookie_from_file()
_local = threading.local()
_print_lock = threading.Lock()


def session() -> requests.Session:
    """每个线程一个会话，避免共享连接。"""
    if not hasattr(_local, "s"):
        _local.s = new_session(COOKIE)
    return _local.s


def read_rows(genre: str, limit: int | None = None) -> list[dict]:
    path = DATA_DIR / f"testset_{genre}.csv"
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    return rows[:limit] if limit else rows


def fetch_metas(ids: list[int]) -> dict[int, dict]:
    """批量获取歌名与歌手（用于命名）。"""
    metas: dict[int, dict] = {}
    s = session()
    for i in range(0, len(ids), BATCH_SIZE):
        batch = ids[i:i + BATCH_SIZE]
        payload = {"ids": json.dumps(batch), "c": json.dumps([{"id": x} for x in batch])}
        r = s.post(SONG_DETAIL_API, data=payload, timeout=30)
        r.raise_for_status()
        for song in r.json().get("songs") or []:
            metas[song["id"]] = {
                "name": song.get("name", ""),
                "artists": [a.get("name", "") for a in (song.get("ar") or song.get("artists") or [])
                            if a.get("name")],
            }
    return metas


def run_one(task: dict, meta: dict, overwrite: bool, delay: float) -> dict:
    """抓取并下载单曲，返回结果状态。"""
    sid, genre = task["song_id"], task["genre"]
    try:
        item = fetch_play_url(session(), sid, "exhigh")
        if item.get("url"):
            time.sleep(delay)
        if not item.get("url"):
            return {**task, "status": "失败", "reason": "无音源（无版权/下架/需付费）"}
        path = DATASET_DIR / genre / build_filename(meta, item["url"])
        if path.exists() and not overwrite:
            return {**task, "status": "跳过", "reason": "同名文件已存在", "file": str(path)}
        size = download(session(), item["url"], path)
        return {**task, "status": "成功", "file": str(path), "size": size}
    except (requests.RequestException, RuntimeError, ValueError) as e:
        return {**task, "status": "失败", "reason": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description="按流派 CSV 批量下载音频到 genre_testset/dataset/<genre>/")
    ap.add_argument("--genres", nargs="+", default=["country", "hiphop"], help="流派名，对应 data/testset_<genre>.csv")
    ap.add_argument("--limit", type=int, help="每个流派只处理前 N 首（验证用）")
    ap.add_argument("--workers", type=int, default=4, help="下载并发数，默认 4")
    ap.add_argument("--delay", type=float, default=0.2, help="每首播放地址请求后的间隔秒数")
    ap.add_argument("--overwrite", action="store_true", help="覆盖已存在的同名文件")
    args = ap.parse_args()

    if not COOKIE:
        print("提示：未找到 data/cookies.json，未登录时部分歌曲拿不到播放地址", file=sys.stderr)

    tasks: list[dict] = []
    for genre in args.genres:
        rows = read_rows(genre, args.limit)
        for r in rows:
            tasks.append({"genre": genre, "no": int(r["序号"]), "song_id": int(r["song id"]),
                          "csv_name": r["歌曲名称"], "csv_artists": r["歌手"]})
        print(f"[{genre}] 待处理 {len(rows)} 首")

    ids = sorted({t["song_id"] for t in tasks})
    print(f"共 {len(tasks)} 首，{len(ids)} 个不同 song id，开始批量获取歌曲信息 ...")
    metas = fetch_metas(ids)

    total = len(tasks)
    done = 0
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = []
        for t in tasks:
            meta = metas.get(t["song_id"]) or {
                "name": t["csv_name"],
                "artists": [a.strip() for a in t["csv_artists"].split(" / ") if a.strip()],
            }
            futures.append(pool.submit(run_one, t, meta, args.overwrite, args.delay))
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            done += 1
            name = Path(res.get("file", "")).name or res["csv_name"]
            if res["status"] == "成功":
                msg = f"{name}  ({res['size'] / 1024 / 1024:.2f} MB)"
            else:
                msg = f"{name}  [{res['status']}] {res.get('reason', '')}"
            with _print_lock:
                print(f"[{done}/{total}] {res['genre']} #{res['no']} {res['song_id']} {msg}", flush=True)

    print("\n统计：")
    for genre in args.genres:
        sub = [r for r in results if r["genre"] == genre]
        ok = sum(1 for r in sub if r["status"] == "成功")
        skip = sum(1 for r in sub if r["status"] == "跳过")
        fail = [r for r in sub if r["status"] == "失败"]
        mb = sum(r.get("size", 0) for r in sub) / 1024 / 1024
        print(f"  {genre}: 成功 {ok}，跳过 {skip}，失败 {len(fail)}，新增 {mb:.1f} MB")
        for r in sorted(fail, key=lambda x: x["no"]):
            print(f"    失败 #{r['no']} {r['song_id']} {r['csv_name']} — {r['reason']}")
    print(f"\n输出目录：{DATASET_DIR}")
    return 0 if not any(r["status"] == "失败" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
