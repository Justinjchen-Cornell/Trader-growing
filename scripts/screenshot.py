# -*- coding: utf-8 -*-
"""README 截图：用系统已有 Edge（无头）截取 Web 界面三个 tab

用法: python scripts/screenshot.py
输出: assets/screenshots/{home,lab,levels}.png
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "screenshots")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
URL = "http://localhost:8501"

os.makedirs(OUT, exist_ok=True)


def shot(page, tab_label, fname):
    tab = page.locator("button[role=tab]", has_text=tab_label).first
    tab.click()
    page.wait_for_timeout(3500)  # Streamlit 渲染
    page.screenshot(path=os.path.join(OUT, fname))
    print("  📸", fname, "<-", tab_label)


def main():
    print("启动 Edge 无头模式（系统已有 Edge，不安装 Chrome）")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=EDGE, headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900},
                                locale="zh-CN")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(6000)
        shot(page, "🏠 今日", "home.png")
        shot(page, "🧪 实验场", "lab.png")
        shot(page, "🎮 学习关卡", "levels.png")
        browser.close()
    print("完成 ->", OUT)


if __name__ == "__main__":
    main()
