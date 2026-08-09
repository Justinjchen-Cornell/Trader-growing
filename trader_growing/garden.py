# -*- coding: utf-8 -*-
"""成长花园：四维属性 -> 四棵植物（ASCII 可视化）"""
from .character import DIM_NAMES

STAGES = [
    ("...", "种子"), ("..|", "发芽"), ("--|", "幼苗"),
    ("-@|", "小树"), ("-@@", "大树"), ("@@@", "开花结果"),
]


def _stage(score):
    return STAGES[min(5, max(0, int(score / 20)))]


def draw_garden(dims):
    lines = ["  Trader-growing · 成长花园", "  " + "=" * 40]
    for d in ["math", "finance", "psychology", "philosophy"]:
        icon, name = _stage(dims.get(d, 0))
        lines.append("  {} {:8s} [{:>3.0f}/100]  {}".format(icon, DIM_NAMES[d], dims.get(d, 0), name))
    lines.append("  " + "=" * 40)
    lines.append("  提示：每天浇水（打卡），四维才会开花")
    return "\n".join(lines)
