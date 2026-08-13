# -*- coding: utf-8 -*-
"""知识卡配图：用真实行情现算现画，让概念有图可看

每个函数返回 matplotlib Figure（数据不足时返回 None，由调用方跳过渲染）。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from trader_growing.fonts import setup as _font_setup
_font_setup()

from trader_growing.dashboard import (load_latest, pair_corr, annualized_vol,
                                      max_drawdown, yearly_returns)


def _guard(fig):
    return fig


def corr_scatter(a="518880.SS", b="510300.SS", label_a="黄金ETF", label_b="沪深300ETF", days=252):
    """两资产日收益散点 + 相关系数"""
    ca, cb = load_latest(a), load_latest(b)
    if ca is None or cb is None or len(ca) < 30:
        return None
    ra, rb = ca.pct_change().tail(days), cb.pct_change().tail(days)
    j = ra.index.intersection(rb.index)
    if len(j) < 30:
        return None
    c = float(ra.loc[j].corr(rb.loc[j]))
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    ax.scatter(ra.loc[j] * 100, rb.loc[j] * 100, s=10, alpha=0.55, color="#2ecc71")
    ax.axhline(0, color="#888", lw=0.7)
    ax.axvline(0, color="#888", lw=0.7)
    ax.set_xlabel("{} 日收益 %".format(label_a))
    ax.set_ylabel("{} 日收益 %".format(label_b))
    ax.set_title("{} × {} 相关性 {:.2f}".format(label_a, label_b, c), fontsize=11)
    fig.tight_layout()
    return fig


def vol_weights(a="510300.SS", b="518880.SS", name_a="沪深300ETF", name_b="黄金ETF"):
    """风险平价：波动率柱状 + 反比权重"""
    va, vb = annualized_vol(load_latest(a)), annualized_vol(load_latest(b))
    if va is None or vb is None:
        return None
    wa = (1 / va) / (1 / va + 1 / vb)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.4, 3.2))
    ax1.bar([name_a, name_b], [va, vb], color=["#3498db", "#f1c40f"])
    ax1.set_title("年化波动率", fontsize=11)
    ax1.set_ylim(0, max(va, vb) * 1.3)
    for i, v in enumerate([va, vb]):
        ax1.text(i, v, "{:.0%}".format(v), ha="center", va="bottom")
    ax2.bar([name_a, name_b], [wa, 1 - wa], color=["#3498db", "#f1c40f"])
    ax2.set_title("风险平价权重（∝1/波动）", fontsize=11)
    ax2.set_ylim(0, 1)
    for i, v in enumerate([wa, 1 - wa]):
        ax2.text(i, v, "{:.0%}".format(v), ha="center", va="bottom")
    fig.tight_layout()
    return fig


def price_path(sym="510300.SS", name="沪深300ETF", days=252):
    """价格路径 + 峰值/谷底标记（锯齿 BOSS）"""
    close = load_latest(sym)
    if close is None or len(close) < 30:
        return None
    s = close.tail(days + 1)
    dd = max_drawdown(close, days)
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    ax.plot(s.index, s.values, color="#3498db", lw=1.2)
    if dd:
        dd_val, hi, lo = dd
        ax.axhline(hi, color="#e74c3c", ls="--", lw=0.8)
        ax.axhline(lo, color="#2ecc71", ls="--", lw=0.8)
        ax.annotate("峰值 {:.3f}".format(hi), xy=(0.02, 0.95), xycoords="axes fraction", fontsize=9, color="#e74c3c")
        ax.annotate("谷底 {:.3f}（回撤 {:.0%}）".format(lo, dd_val), xy=(0.02, 0.1),
                    xycoords="axes fraction", fontsize=9, color="#2ecc71")
    ax.set_title("{} 近一年真实路径".format(name), fontsize=11)
    fig.tight_layout()
    return fig


def yearly_bars(sym="510300.SS", n_years=5):
    """最近 N 个完整年度收益柱状（逐年拆解）"""
    close = load_latest(sym)
    if close is None:
        return None
    yrs = yearly_returns(close)
    yrs = dict(list(sorted(yrs.items()))[-n_years:])
    if not yrs:
        return None
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    colors = ["#e74c3c" if v < 0 else "#2ecc71" for v in yrs.values()]
    ax.bar([str(y) for y in yrs], [v * 100 for v in yrs.values()], color=colors)
    ax.axhline(0, color="#888", lw=0.7)
    ax.set_ylabel("年收益 %")
    ax.set_title("沪深300ETF 逐年收益（整体数字会骗人）", fontsize=11)
    for i, v in enumerate(yrs.values()):
        ax.text(i, v * 100, "{:+.1%}".format(v), ha="center",
                va="bottom" if v > 0 else "top", fontsize=8)
    fig.tight_layout()
    return fig


def underwater(sym="510300.SS", days=252):
    """水下曲线：距历史峰值的回撤深度"""
    close = load_latest(sym)
    if close is None or len(close) < 30:
        return None
    s = close.tail(days + 1)
    roll = s / s.cummax() - 1
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    ax.fill_between(s.index, roll * 100, 0, color="#e74c3c", alpha=0.4)
    ax.plot(s.index, roll * 100, color="#e74c3c", lw=1.0)
    ax.set_ylabel("距峰值回撤 %")
    ax.set_title("水下曲线：在水下潜多深、待多久", fontsize=11)
    ax.set_ylim(roll.min() * 100 * 1.3, 2)
    fig.tight_layout()
    return fig


def in_out_bars(sym="510300.SS"):
    """样本内（最近5个完整年度中的前4年） vs 样本外（最后1年）柱状"""
    close = load_latest(sym)
    if close is None:
        return None
    yrs = yearly_returns(close)
    yrs = dict(list(sorted(yrs.items()))[-5:])
    if len(yrs) < 5:
        return None
    ys = list(sorted(yrs))
    ins = 1.0
    for y in ys[:-1]:
        ins *= (1 + yrs[y])
    in_ret, out_ret = ins - 1, yrs[ys[-1]]
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    vals = [in_ret * 100, out_ret * 100]
    colors = ["#e74c3c" if v < 0 else "#2ecc71" for v in vals]
    ax.bar(["样本内（做作业）", "样本外（闭卷考）"], vals, color=colors)
    ax.axhline(0, color="#888", lw=0.7)
    ax.set_ylabel("累计收益 %")
    ax.set_title("样本内外对比：闭卷考才见真章", fontsize=11)
    for i, v in enumerate(vals):
        ax.text(i, v, "{:+.1%}".format(v / 100), ha="center", va="bottom" if v > 0 else "top")
    fig.tight_layout()
    return fig


def odd_even_bars(sym="510300.SS"):
    """奇偶年切法对比柱状（最近 5 个完整年度）"""
    close = load_latest(sym)
    if close is None:
        return None
    yrs = yearly_returns(close)
    yrs = dict(list(sorted(yrs.items()))[-5:])
    if len(yrs) < 5:
        return None
    ys = list(sorted(yrs))
    odd = 1.0
    for y in ys[::2]:
        odd *= (1 + yrs[y])
    even = 1.0
    for y in ys[1::2]:
        even *= (1 + yrs[y])
    odd, even = odd - 1, even - 1
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    vals = [odd * 100, even * 100]
    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in vals]
    ax.bar(["奇数年（2021/23/25）", "偶数年（2022/24）"], vals, color=colors)
    ax.axhline(0, color="#888", lw=0.7)
    ax.set_ylabel("累计收益 %")
    ax.set_title("同样 5 年，切法不同结论相反", fontsize=11)
    for i, v in enumerate(vals):
        ax.text(i, v, "{:+.1%}".format(v / 100), ha="center", va="bottom" if v > 0 else "top")
    fig.tight_layout()
    return fig


def ic_scatter(syms=None):
    """因子 IC 散点：动量 vs 收益（4 资产标注）"""
    if syms is None:
        syms = [("510300.SS", "沪深300"), ("513100.SS", "纳指100"),
                ("518880.SS", "黄金"), ("501018.SS", "原油")]
    moms, rets = {}, {}
    for sym, name in syms:
        c = load_latest(sym)
        if c is None or len(c) < 22:
            return None
        from trader_growing.dashboard import window_ret
        moms[name] = c.iloc[-1] / c.iloc[-21] - 1
        rets[name] = window_ret(c)
    if any(v is None for v in rets.values()):
        return None
    fig, ax = plt.subplots(figsize=(4.8, 3.6))
    for name in moms:
        ax.scatter(moms[name] * 100, rets[name] * 100, s=60, color="#3498db", zorder=3)
        ax.annotate(name, (moms[name] * 100, rets[name] * 100),
                    textcoords="offset points", xytext=(6, 6), fontsize=9)
    ax.axhline(0, color="#888", lw=0.7)
    ax.axvline(0, color="#888", lw=0.7)
    ax.set_xlabel("20 日动量 %")
    ax.set_ylabel("近一年收益 %")
    ax.set_title("动量因子散点：排名越前，收益越…？", fontsize=11)
    fig.tight_layout()
    return fig


CHART_FNS = {
    "corr_scatter": corr_scatter,
    "vol_weights": vol_weights,
    "price_path": price_path,
    "yearly_bars": yearly_bars,
    "underwater": underwater,
    "in_out_bars": in_out_bars,
    "odd_even_bars": odd_even_bars,
    "ic_scatter": ic_scatter,
}
