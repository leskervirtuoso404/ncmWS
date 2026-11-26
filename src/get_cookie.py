"""打开浏览器扫码登录网易云音乐，并把登录 Cookie 保存到 data/cookies.json。

用法：python src/get_cookie.py
登录完成后窗口会自动关闭（或按提示手动关闭）。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ncm_common import COOKIE_FILE, DATA_DIR  # noqa: E402

LOGIN_URL = "https://music.163.com/#/login"
TIMEOUT_SECONDS = 300


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            )
        )
        page = context.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

        print("请在打开的浏览器窗口中扫码登录（或手机号登录），最长等待 5 分钟 ...")
        deadline = time.time() + TIMEOUT_SECONDS
        cookies = []
        while time.time() < deadline:
            cookies = context.cookies("https://music.163.com")
            if any(c["name"] == "MUSIC_U" and c["value"] for c in cookies):
                break
            time.sleep(2)

        if not any(c["name"] == "MUSIC_U" and c["value"] for c in cookies):
            print("未检测到登录状态，已超时退出。")
            browser.close()
            return

        # 等待页面把剩余 cookie 写入
        time.sleep(3)
        cookies = context.cookies("https://music.163.com")
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
        COOKIE_FILE.write_text(
            json.dumps({"cookie": cookie_str, "cookies": cookies}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (DATA_DIR / "storage_state.json").write_text(
            json.dumps(context.storage_state(), ensure_ascii=False), encoding="utf-8"
        )
        print(f"登录 Cookie 已保存 -> {COOKIE_FILE}")
        print(f"Cookie 名称：{', '.join(sorted(c['name'] for c in cookies))}")
        browser.close()


if __name__ == "__main__":
    main()
