# -*- coding: utf-8 -*-
"""偏差趋势统计：用数据证明'纪律影响成长'

统计：纪律分 vs 红牌数 的相关性（Spearman）
     '纪律分低于 X 的日子，平均红牌 Y 条' 的可视化洞察
"""
import numpy as np
from scipy.stats import spearmanr

from .journal_bridge import load_all


def red_flag_count(tb):
    """统计一天的红牌数"""
    tb = tb or {}
    n = 0
    if tb.get("impulse_trade"):
        n += 1
    if tb.get("moved_stop_loss"):
        n += 1
    if tb.get("traded_today") and tb.get("followed_plan") is False:
        n += 1
    return n


def analyze():
    recs = load_all()
    if not recs:
        return None
    rows = []
    for r in recs:
        if r.mode != "evening":
            continue
        disp = (r.math + r.finance + r.psychology + r.philosophy) / 4.0
        reds = red_flag_count(r.trades_today)
        rows.append({"date": r.date, "discipline": disp, "red_flags": reds})
    if len(rows) < 3:
        return {"rows": rows, "message": "样本太少（<3 天），继续积累"}
    df = rows
    disp = np.array([x["discipline"] for x in df])
    reds = np.array([x["red_flags"] for x in df])
    corr, pval = spearmanr(disp, reds)
    # 分组洞察：纪律分低的日子 vs 高的日子
    med = np.median(disp)
    low = np.mean(reds[disp <= med]) if (disp <= med).any() else 0
    high = np.mean(reds[disp > med]) if (disp > med).any() else 0
    return {
        "rows": df, "corr": corr, "pval": pval,
        "median_discipline": float(med),
        "avg_red_low": float(low), "avg_red_high": float(high),
    }


def report():
    r = analyze()
    if not r:
        print("暂无日记数据——先运行修行日记 daily_check.py --mode evening")
        return
    if "message" in r:
        print(r["message"])
        return
    print("=" * 55)
    print("  偏差趋势统计：纪律分 vs 红牌")
    print("=" * 55)
    print("  样本: {} 天（evening 记录）".format(len(r["rows"])))
    print("  纪律分与红牌数的 Spearman 相关: {:.3f} (p={:.3f})".format(r["corr"], r["pval"]))
    if r["corr"] < -0.3:
        print("  解读: 显著负相关——纪律分低的日子红牌更多，'心性影响纪律'得到数据支持")
    elif r["corr"] < 0:
        print("  解读: 弱负相关——方向正确，继续积累样本")
    else:
        print("  解读: 暂无负相关（样本或指标需进一步观察）")
    print("  纪律分 ≤ 中位数({:.0f})的日子: 平均红牌 {:.2f} 条".format(
        r["median_discipline"], r["avg_red_low"]))
    print("  纪律分 > 中位数({:.0f})的日子: 平均红牌 {:.2f} 条".format(
        r["median_discipline"], r["avg_red_high"]))
    print("=" * 55)
