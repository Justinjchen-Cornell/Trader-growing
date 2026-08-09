# -*- coding: utf-8 -*-
"""Trader-growing · Web 界面（Streamlit）
运行: streamlit run app.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from trader_growing.character import Character, DIM_NAMES, DIMS
from trader_growing.achievements import AchievementSystem
from trader_growing.bestiary import Bestiary, ENTRIES
from trader_growing.quests import QuestSystem, DAILY_QUESTS, WEEKLY_QUESTS
from trader_growing.tiers import TierSystem
from trader_growing.dashboard import build_dashboard
from trader_growing.journal_bridge import load_all
from trader_growing.stats import analyze, red_flag_count

plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "STHeiti"]
plt.rcParams["axes.unicode_minus"] = False

st.set_page_config(page_title="Trader-growing", page_icon="🌱", layout="wide")

char = Character()
ach = AchievementSystem()
best = Bestiary()
qs = QuestSystem()
tiers = TierSystem()
s = char.summary()


# ---------- 工具 ----------
def radar_chart(dims):
    labels = [DIM_NAMES[d] for d in DIMS]
    vals = [dims.get(d, 0) for d in DIMS]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    vals += vals[:1]
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.fill(angles, vals, color="#2ecc71", alpha=0.3)
    ax.plot(angles, vals, color="#27ae60", linewidth=2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylim(0, 100)
    ax.set_title("四维属性雷达", fontsize=13)
    return fig


def growth_curve():
    recs = [r for r in load_all() if r.mode == "evening"]
    if len(recs) < 2:
        return None
    df = pd.DataFrame([{"date": r.date, "discipline": (r.math + r.finance + r.psychology + r.philosophy) / 4,
                        "red_flags": red_flag_count(r.trades_today)} for r in recs])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["date"], df["discipline"], color="#3498db", marker="o", label="纪律分")
    ax2 = ax.twinx()
    ax2.bar(df["date"], df["red_flags"], color="#e74c3c", alpha=0.3, label="红牌数")
    ax.set_ylabel("纪律分", color="#3498db")
    ax2.set_ylabel("红牌数", color="#e74c3c")
    ax.set_title("成长曲线：纪律分 vs 红牌")
    fig.legend(loc="upper right")
    return fig


# ---------- 页面 ----------
st.title("🌱 Trader-growing · 交易者成长花园")
st.caption("把交易人生变成一座花园。每天 5 分钟浇水，每周一篮果实，每季度一次修剪。")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["🏠 状态", "🌍 四资产看板", "📜 图鉴", "📊 成长", "📋 任务", "🏅 徽章"])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("等级", "{}".format(s["level"]))
    c2.metric("XP", "{} / {}".format(s["xp"], s["next_level_xp"] or "MAX"))
    c3.metric("连击", "{} 天".format(s["streak"]))
    st.progress(min(1.0, s["xp"] / (s["next_level_xp"] or 1)))
    st.caption(s["level_desc"])

    avg = sum(s["dims"].values()) / len(s["dims"]) if s["dims"] else 0
    tier = tiers.current_tier(s["total_days"], avg)
    st.info("当前层级: **{}**（{}）| 累计打卡 {} 天".format(tier["name"], tier["desc"], s["total_days"]))

    left, right = st.columns(2)
    with left:
        st.pyplot(radar_chart(s["dims"]))
    with right:
        st.subheader("成长花园")
        for d in DIMS:
            v = s["dims"].get(d, 0)
            stage = "🌱" if v < 20 else "🌿" if v < 40 else "🌳" if v < 60 else "🌲" if v < 80 else "🌸"
            st.write("{} **{}** [{:.0f}/100] {}".format(stage, DIM_NAMES[d], v, "开花!" if v >= 80 else ""))
            st.progress(min(1.0, v / 100))

with tab2:
    st.subheader("🌍 四资产看板")
    df = build_dashboard()
    if len(df) == 0:
        st.warning("未找到本地数据（~/.oxq/data/market/*.parquet）")
    else:
        st.dataframe(df, width='stretch')

with tab3:
    st.subheader("📜 知识图鉴（{} 条）".format(len(ENTRIES)))
    done_ids = set(best.unlocked)
    cats = sorted(set(e[3] for e in ENTRIES))
    for cat in cats:
        st.markdown("**{}**".format(cat))
        items = [e for e in ENTRIES if e[3] == cat]
        cols = st.columns(2)
        for i, e in enumerate(items):
            with cols[i % 2]:
                if e[0] in done_ids:
                    st.markdown("✅ **{}**：{}".format(e[1], e[2]))
                else:
                    st.markdown("🔒 ~~**{}**~~：解锁需打卡 {} 天".format(e[1], e[4] if e[4] > 0 else "（特殊行为）"))

with tab4:
    st.subheader("📊 成长数据")
    fig = growth_curve()
    if fig:
        st.pyplot(fig)
    else:
        st.info("日记数据不足 2 天——先做几天盘后复盘（修行日记 evening）")
    st.subheader("纪律 vs 红牌")
    r = analyze()
    if r and "message" not in r:
        st.write("Spearman 相关: **{:.3f}** (p={:.3f})".format(r["corr"], r["pval"]))
        st.write("纪律分 ≤ 中位数({:.0f})：平均红牌 {:.2f} 条".format(r["median_discipline"], r["avg_red_low"]))
        st.write("纪律分 > 中位数({:.0f})：平均红牌 {:.2f} 条".format(r["median_discipline"], r["avg_red_high"]))
    else:
        st.info("样本不足 3 天，继续积累")

with tab5:
    st.subheader("📋 每日任务")
    done_today = qs.daily_done_today()
    for q in DAILY_QUESTS:
        st.write("{} **{}**：{}".format("✅" if q["id"] in done_today else "⬜", q["name"], q["desc"]))
    st.subheader("本周每周任务（+30 XP）")
    for q in WEEKLY_QUESTS:
        st.write("⬜ **{}**：{}".format(q["name"], q["desc"]))

with tab6:
    st.subheader("🏅 已解锁徽章")
    unlocked = ach.summary()
    if not unlocked:
        st.info("暂无徽章——完成每日打卡解锁第一枚")
    else:
        for a in unlocked:
            st.write("🏅 **{}**：{}".format(a["name"], a["desc"]))
    st.subheader("🔒 待解锁")
    from trader_growing.achievements import ACHIEVEMENTS
    for a in ACHIEVEMENTS:
        if a["id"] not in ach.unlocked:
            st.write("🔒 **{}**：{}".format(a["name"], a["desc"]))
