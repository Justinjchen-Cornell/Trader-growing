# -*- coding: utf-8 -*-
"""今日一题：每天 30 秒，用今天的真实行情学一个量化概念

- 题目按日期确定性轮换（8 种题型 × 每日轮换）
- 答案用最新真实数据实时计算——同一个题型每天答案不同
- 首次答对 +3 XP（新手期双倍），可重试
- 分享卡片：生成 PNG（matplotlib），可直接发微信群/朋友圈
"""
import json
import os
from datetime import date
from io import BytesIO

from trader_growing.dashboard import (load_latest, annualized_vol, pair_corr)

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                         "data", "daily_challenge.json")


def today_key():
    return str(date.today())


def q_calc_shares():
    c = load_latest("510300.SS")
    px = float(c.iloc[-1])
    return ("今天沪深300ETF 收盘 {:.3f} 元，定投 1000 元能买多少份（取整）？".format(px),
            "份数 = 1000 ÷ 价格",
            round(1000 / px),
            "今天的真实价格 {:.3f} 元 -> 1000 元 = {} 份。定投不看涨跌，机械执行。".format(px, round(1000 / px)))


def q_ma_direction():
    c = load_latest("510300.SS")
    px = float(c.iloc[-1])
    ma = float(c.rolling(20).mean().iloc[-1])
    ans = 1 if px > ma else -1
    return ("沪深300ETF 收盘 {:.3f} 在 MA20（{:.3f}）上方还是下方？（1=上方，-1=下方）".format(px, ma),
            "收盘价 > MA20 = 上方（多头）",
            ans,
            "收盘 {:.3f} vs MA20 {:.3f} -> {}。均线是滞后指标，看的是过去。".format(
                px, ma, "上方（多头）" if ans == 1 else "下方（空头）"))


def q_vs_benchmark():
    c = load_latest("510300.SS")
    px = float(c.iloc[-1])
    ref = float(c.iloc[-252])
    diff = px / ref - 1
    ans = 1 if diff > 0.005 else -1 if diff < -0.005 else 0
    return ("沪深300ETF 今天比一年前涨了还是跌了？（1=涨，-1=跌，0=差不多）",
            "对比一年前的收盘价",
            ans,
            "一年前 {:.3f} -> 今天 {:.3f}（{:+.1%}）。这就是你的买入持有基准。".format(ref, px, diff))


def q_momentum_top():
    syms = [("1", "510300.SS", "沪深300"), ("2", "513100.SS", "纳指100"),
            ("3", "518880.SS", "黄金"), ("4", "501018.SS", "原油")]
    moms = []
    for idx, s, n in syms:
        c = load_latest(s)
        moms.append((idx, n, float(c.iloc[-1] / c.iloc[-21] - 1)))
    top = max(moms, key=lambda x: x[2])
    return ("四资产 20 日动量谁最强？（1=沪深300，2=纳指100，3=黄金，4=原油）",
            "动量 = 近 20 日涨跌幅",
            int(top[0]),
            "20 日动量：{}。最强的是{}——但注意：动量是滞后指标，最强可能是顶部。".format(
                ", ".join("{}{:+.1%}".format(n, m) for _, n, m in moms), top[1]))


def q_corr_sign():
    c = pair_corr(load_latest("518880.SS"), load_latest("510300.SS"))
    ans = 1 if c > 0.15 else -1 if c < -0.15 else 0
    return ("近一年黄金和沪深300 日收益是正相关还是负相关？（1=正，-1=负，0=约零）",
            "相关系数 > 0 就是正相关",
            ans,
            "实测相关系数 {:.2f} -> {}。分散风险的关键是买涨跌不同步的资产。".format(
                c, "正相关（同涨同跌多）" if ans == 1 else "负相关（反向多）" if ans == -1 else "接近零相关"))


def q_risk_parity():
    va, vb = annualized_vol(load_latest("510300.SS")), annualized_vol(load_latest("518880.SS"))
    wa = (1 / va) / (1 / va + 1 / vb)
    ans = 1 if va < vb else 2
    return ("沪深300 波动 {:.0%}，黄金 {:.0%}。按风险平价谁该分到更多钱？（1=沪深300，2=黄金）".format(va, vb),
            "波动小的一方反而分到更多钱（权重正比 1/波动）",
            ans,
            "权重 = 1/波动：沪深300 {:.0%}，黄金 {:.0%}。平均分钱不等于平均分影响力。".format(wa, 1 - wa))


def q_stop_price():
    c = load_latest("510300.SS")
    px = float(c.iloc[-1])
    return ("按今天收盘价 {:.3f} 买入，-8% 止损价是多少（3 位小数）？".format(px),
            "止损价 = 买入价 × 0.92",
            round(px * 0.92, 3),
            "{:.3f} × 0.92 = {:.3f}。止损把可能 -40% 截断成可控 -8%。".format(px, round(px * 0.92, 3)))


def q_min_corr():
    base = load_latest("510300.SS")
    cands = [("1", "513100.SS", "纳指100"), ("2", "518880.SS", "黄金"), ("3", "501018.SS", "原油")]
    corrs = []
    for idx, s, n in cands:
        c = pair_corr(base, load_latest(s))
        corrs.append((int(idx), n, c))
    best = min(corrs, key=lambda x: x[2])
    return ("与沪深300 相关性最低的是谁？（1=纳指100，2=黄金，3=原油）",
            "相关性最低 = 涨跌最不同步",
            best[0],
            "相关性：{}。最低的是{}——放进组合分散效果最好。".format(
                ", ".join("{}{:+.2f}".format(n, c) for _, n, c in corrs), best[1]))


TYPES = [
    ("calc_shares", "定投份数", q_calc_shares),
    ("ma_direction", "均线方向", q_ma_direction),
    ("vs_benchmark", "基准对比", q_vs_benchmark),
    ("momentum_top", "动量最强", q_momentum_top),
    ("corr_sign", "相关性", q_corr_sign),
    ("risk_parity", "风险平价", q_risk_parity),
    ("stop_price", "止损价", q_stop_price),
    ("min_corr", "标的池", q_min_corr),
]


def today_type():
    key = today_key()
    seed = int(key.replace("-", ""))
    return TYPES[seed % len(TYPES)]


def today_question():
    tid, label, fn = today_type()
    text, hint, answer, evidence = fn()
    return {"type": tid, "label": label, "text": text, "hint": hint,
            "answer": answer, "evidence": evidence}


# ------------------------------------------------------------ 作答记录
class ChallengeRecord:
    def __init__(self, data_path=None):
        self.data_path = data_path or DATA_PATH
        self.records = {}
        self.load()

    def load(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, encoding="utf-8") as f:
                self.records = json.load(f)

    def save(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def done_today(self):
        return self.records.get(today_key(), {}).get("correct", False)

    def attempts_today(self):
        return self.records.get(today_key(), {}).get("attempts", 0)

    def record(self, correct):
        k = today_key()
        r = self.records.get(k, {"attempts": 0, "correct": False, "xp": 0})
        r["attempts"] += 1
        first_correct = correct and not r["correct"]
        r["correct"] = r["correct"] or correct
        if first_correct:
            r["xp"] = 3
        self.records[k] = r
        self.save()
        return first_correct


# ------------------------------------------------------------ 分享卡片 PNG
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "STHeiti"]
plt.rcParams["axes.unicode_minus"] = False

import textwrap


def _wrap(text, width):
    lines = []
    for seg in text.split("\n"):
        lines.extend(textwrap.wrap(seg, width=width) or [""])
    return lines


def make_card(question, user_answer, correct, char_summary, levels_done, worlds_done):
    s = char_summary
    fig = plt.figure(figsize=(6.2, 3.8), dpi=160)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    ax.add_patch(plt.Rectangle((0, 0.86), 1, 0.14, color="#27ae60"))
    ax.text(0.05, 0.925, "Trader-growing · 今日一题", fontsize=17,
            color="white", va="center")
    ax.text(0.95, 0.925, date.today().strftime("%Y-%m-%d"), fontsize=12,
            color="white", va="center", ha="right")

    q_lines = _wrap("Q · [{}] {}".format(question["label"], question["text"]), 34)
    y = 0.78
    for ln in q_lines[:4]:
        ax.text(0.05, y, ln, fontsize=10.5, va="center")
        y -= 0.055

    mark = "【答对了】" if correct else "【再想想】"
    color = "#27ae60" if correct else "#e74c3c"
    ax.text(0.05, y - 0.015, "你的答案: {}    {}".format(user_answer, mark),
            fontsize=14, color=color, va="center")

    ev_lines = _wrap("今日市场教学: " + question["evidence"], 34)
    yy = y - 0.075
    for ln in ev_lines[:3]:
        ax.text(0.05, yy, ln, fontsize=9, color="#555555", va="center")
        yy -= 0.045

    ax.axhline(0.18, color="#dddddd", lw=1)
    status = "Lv.{} · XP {} · 连击 {} 天 · 关卡 {}/36 · 世界 {}/9".format(
        s["level"], s["xp"], s["streak"], levels_done, worlds_done)
    ax.text(0.05, 0.115, status, fontsize=10.5, color="#333333", va="center")
    ax.text(0.95, 0.115, "每天一题 · 用真实行情学量化", fontsize=9,
            color="#888888", va="center", ha="right")

    buf = BytesIO()
    fig.savefig(buf, format="png", facecolor="white", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf
