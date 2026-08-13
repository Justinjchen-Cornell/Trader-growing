# -*- coding: utf-8 -*-
"""中文字体探测：本地 Windows 用雅黑/黑体，云端 Linux 用 Noto Sans CJK

matplotlib 找不到字体时中文会显示方块——本模块按平台探测可用字体，
全部缺失则回退 matplotlib 默认（不崩溃）。
"""
import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager

CANDIDATES = [
    "Microsoft YaHei", "SimHei", "STHeiti",          # Windows
    "PingFang SC", "Arial Unicode MS",               # macOS
    "Noto Sans CJK SC", "Noto Sans SC",              # Linux 云端
    "WenQuanYi Micro Hei", "Droid Sans Fallback",
]

_configured = False


def setup():
    global _configured
    if _configured:
        return
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in CANDIDATES:
        if name in installed:
            matplotlib.rcParams["font.sans-serif"] = [name] + list(
                matplotlib.rcParams.get("font.sans-serif", []))
            break
    matplotlib.rcParams["axes.unicode_minus"] = False
    _configured = True
