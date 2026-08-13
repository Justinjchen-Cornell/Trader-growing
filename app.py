# -*- coding: utf-8 -*-
"""Trader-growing · Web 界面（Streamlit）
运行: streamlit run app.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
from datetime import date as _date
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
from trader_growing.peerboard import PeerBoard
from trader_growing.models import DailyRecord
from trader_growing.knowledge import QUESTIONS as K_QUESTIONS, KnowledgeSystem
from trader_growing.levels import LEVELS, WORLDS, Progress, solve_task
from trader_growing.dashboard import load_latest
from trader_growing.weekly import WeeklyReport
from trader_growing.questions import (QUESTIONS, DIM_NAMES, DIM_EMOJI, SCALE,
    dim_score, overall_score, grade, red_flags_from_answers,
    questions_for, max_level_for_xp, level_badges)

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

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs(
    ["🏠 今日", "🎯 操作台", "🧪 实验场", "🎮 学习关卡", "📜 图鉴", "📊 成长", "📋 任务", "🏅 徽章", "👥 同行榜", "✅ 每日测试", "🧠 知识测试", "📅 周报"])

today = str(_date.today())

with tab1:
    # ---- ⚡ 今日一题（30 秒，用今天的真实行情学量化） ----
    st.subheader("⚡ 今日一题（30 秒 · 用今天的真实行情学量化）")
    from trader_growing.daily_challenge import today_question, ChallengeRecord, make_card
    q = today_question()
    cr = ChallengeRecord()
    if char.is_newbie():
        st.info("🌱 新手上路期（首次打卡 7 天内）：所有 XP 双倍！")
    if cr.done_today():
        st.success("今日已答对（+3 XP 已入账）——明天 0 点换新题，答案随行情变")
    else:
        st.markdown("**Q · [{}]** {}".format(q["label"], q["text"]))
        st.caption("提示: " + q["hint"])
        ans_in = st.text_input("你的答案", key="challenge_ans")
        if st.button("提交答案", key="challenge_btn", type="primary"):
            try:
                val = int(ans_in.strip())
            except ValueError:
                st.error("请输入数字")
                st.stop()
            correct = (val == q["answer"])
            first = cr.record(correct)
            st.session_state["challenge_last_ans"] = ans_in.strip()
            if correct:
                got = char.gain_xp(3) if first else 0
                if got:
                    st.balloons()
                    st.success("✅ 答对了！+{} XP{}".format(got, "（新手双倍）" if got != 3 else ""))
                else:
                    st.success("✅ 答对了！（今天已经拿过 XP 了）")
            else:
                st.error("❌ 不对——正确答案是 {}。".format(q["answer"]))
    st.markdown("**今日市场教学**: " + q["evidence"])
    if cr.done_today() or cr.attempts_today() > 0:
        prog_snap = Progress()
        card = make_card(q, st.session_state.get("challenge_last_ans", ""),
                         cr.done_today(), s, len(prog_snap.completed),
                         prog_snap.worlds_cleared())
        st.download_button("📤 下载今日分享卡片（发微信群/朋友圈）",
                           data=card, file_name="trader_card_{}.png".format(today),
                           mime="image/png")

    # ---- 今日全勤 ----
    ks_h = KnowledgeSystem().history
    check_done = char.last_date == today
    know_done = any(h.get("date") == today for h in ks_h)
    full = check_done and cr.done_today()
    st.caption("今日进度：{} 每日测试 · {} 今日一题 · {} 知识测试{}".format(
        "✅" if check_done else "⬜", "✅" if cr.done_today() else "⬜",
        "✅" if know_done else "⬜", "  —— 🎉 全勤！" if full else ""))
    st.divider()

    # ---- 新手路径引导 ----
    with st.expander("🚀 新手路径（每天 5 分钟，第 1 天从这里开始）", expanded=False):
        from trader_growing.dashboard import load_latest as _ll
        has_data = _ll("510300.SS") is not None
        if not has_data:
            st.warning("⚠️ 还没找到行情数据——学习关卡和看板都需要它。"
                       "请先运行: `python scripts/update_data.py --source akshare`（免费，无需注册）")
        prog_ = Progress()
        done1 = char.last_date == str(_date.today())
        done2 = len(prog_.completed) > 0
        done3 = s["total_days"] >= 1
        st.markdown("**{} 每日测试**：完成今天的 20 题修行测试（约 3 分钟）".format("✅" if done1 else "①"))
        st.markdown("**{} 闯学习关卡**：去「🎮 学习关卡」通关 W1 第 1 关「定投播种」（约 10 分钟）".format(
            "✅" if done2 else "②"))
        st.markdown("**{} 看周报**：每周一看「📅 周报」，复盘本周并读建议".format("✅" if done3 else "③"))
        if not (done1 and done2):
            st.info("今天的目标：完成上面 {} 项，然后就可以去生活了——修行是每天 5 分钟，不是熬夜刷分。".format(
                "2" if not done1 and not done2 else "1"))

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
    st.subheader("🎯 今日操作台：看天气 → 定计划 → 对账")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🌍 四资产看板**")
        df = build_dashboard()
        if len(df) == 0:
            st.warning("未找到本地数据（~/.oxq/data/market/*.parquet）")
        else:
            st.dataframe(df, width='stretch')
        st.caption("趋势 = 轻信号(MA20)；重信号见右侧策略计划")
        if st.button("📥 更新行情数据（akshare · 约 1 分钟）", use_container_width=True):
            import subprocess as _sp
            root = os.path.dirname(os.path.abspath(__file__))
            with st.spinner("正在从 akshare 拉取 9 只资产日线……"):
                try:
                    r = _sp.run([sys.executable, os.path.join(root, "scripts", "update_data.py"),
                                 "--source", "akshare"], capture_output=True, text=True,
                                timeout=300, cwd=root)
                    out = (r.stdout or "")[-1200:]
                    st.code(out)
                except Exception as e:
                    st.error("更新失败: {}".format(str(e)[:200]))
    with c2:
        st.markdown("**📋 今日策略计划（中庸策略）**")
        from trader_growing.strategy_bridge import load_plan
        from trader_growing.models import Plan
        plan_d = load_plan()
        if not plan_d:
            st.info("还没有今日计划——运行中庸策略 plan.py 后刷新，或先按看板轻信号观察")
            plan_obj = None
        else:
            st.markdown("**{}**（{}）".format(plan_d.get("action", "—"), plan_d.get("asset", "—")))
            for k in ["signal", "cap", "close", "stop_loss_line", "advice"]:
                v = plan_d.get(k)
                if v:
                    st.write("- {}: {}".format({"signal": "信号", "cap": "建议仓位", "close": "收盘",
                                                "stop_loss_line": "止损线", "advice": "建议"}.get(k, k), v))
            plan_obj = Plan(date=plan_d.get("date", ""), asset=plan_d.get("asset", ""),
                            symbol=plan_d.get("symbol", ""), signal=plan_d.get("signal", ""),
                            cap=plan_d.get("cap", 0), action=plan_d.get("action", ""),
                            close=plan_d.get("close", 0), stop_loss_line=plan_d.get("stop_loss_line", 0),
                            advice=plan_d.get("advice", ""))
        st.divider()
        st.markdown("**⚖️ 纪律对账（计划 vs 实际，每天 30 秒）**")
        from trader_growing.reconcile import reconcile as _reconcile
        rec_key = "reconcile_done_" + today
        if st.session_state.get(rec_key):
            st.success("今日已对账 ✅（见下方结果）")
        else:
            with st.form("reconcile_form"):
                traded = st.checkbox("今天有交易吗？")
                followed = st.checkbox("严格按计划执行了吗？")
                impulse = st.checkbox("有计划外开仓/加仓？")
                moved = st.checkbox("手动移动过止损线？")
                submitted = st.form_submit_button("提交对账")
            if submitted:
                if not traded and not impulse and not moved:
                    st.info("今天没交易、没违规——空仓/不动也是一种纪律 ✅")
                tb = {"traded_today": traded, "followed_plan": followed if traded else None,
                      "impulse_trade": impulse, "moved_stop_loss": moved}
                # 写入今日日记
                from trader_growing.models import DailyRecord
                _d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "diary")
                os.makedirs(_d, exist_ok=True)
                fp = os.path.join(_d, today + ".json")
                if os.path.exists(fp):
                    with open(fp, encoding="utf-8") as f:
                        rec = DailyRecord(**json.load(f))
                    rec.trades_today = tb
                else:
                    rec = DailyRecord(date=today, mode="evening", math=0, finance=0,
                                      psychology=0, philosophy=0, overall=0,
                                      notes="操作台对账", trades_today=tb)
                with open(fp, "w", encoding="utf-8") as f:
                    json.dump(rec.to_dict(), f, ensure_ascii=False, indent=2)
                st.session_state[rec_key] = True
                qs.complete_daily("reconcile")
                st.rerun()
        if st.session_state.get(rec_key):
            from trader_growing.journal_bridge import load_latest as _jl
            rec = _jl()
            if rec:
                res = _reconcile(plan_obj, rec)
                if res.clean:
                    st.success("✅ 对账干净：今天的执行与计划一致")
                else:
                    st.warning("发现 {} 条纪律问题:".format(len(res.issues)))
                    for i in res.issues:
                        st.write("- 🔴 " + i)

with tab3:
    st.subheader("🧪 实验场：真实数据回测沙盒（书里实验的可玩版）")
    from trader_growing.backtest import run as run_bt, STRATEGIES as _BTS, ASSETS as _BASSETS
    _sid = st.selectbox("策略模板", [s[0] for s in _BTS],
                        format_func=lambda x: next(s[1] for s in _BTS if s[0] == x))
    _default = next(s[2] for s in _BTS if s[0] == _sid)
    _syms = st.multiselect("资产池", list(_BASSETS.keys()), default=_default,
                           format_func=lambda x: _BASSETS[x])
    c1, c2, c3 = st.columns(3)
    _win = c1.slider("参数窗口（MA/动量回看）", 5, 120, 20)
    _cost = c2.slider("单边成本 %", 0.0, 0.5, 0.05) / 100.0
    if _sid == "dca":
        _monthly = int(c3.number_input("每月定投金额", 100, 100000, 1000, step=100))
    else:
        _monthly = 1000
        c3.caption("组合策略每月再平衡")
    st.caption("指标对比 = 策略 vs 基准（买入持有）。回测是'背答案'的第一现场——漂亮的结果要先怀疑（第 6 章）。")
    if st.button("🚀 跑回测（真实数据）", type="primary", use_container_width=True):
        if not _syms:
            st.error("请至少选择一只资产")
        else:
            with st.spinner("回测中……"):
                res = run_bt(_sid, syms=tuple(_syms), window=int(_win), cost=_cost, monthly=_monthly)
            if res is None:
                st.error("数据不足——先运行 python scripts/update_data.py --source akshare")
            else:
                m, bm = res["metrics"], res["bench_metrics"]
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("策略总收益", "{:+.1%}".format(m["total"]))
                r2.metric("夏普", "{:.2f}".format(m["sharpe"]))
                r3.metric("最大回撤", "{:.1%}".format(m["max_dd"]))
                r4.metric("卡玛比", "{:.2f}".format(m["calmar"]))
                st.caption("基准对照：总收益 {:+.1%} | 夏普 {:.2f} | 回撤 {:.1%} | {}".format(
                    bm["total"], bm["sharpe"], bm["max_dd"], res["meta"]))
                # 净值曲线
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(res["equity"].index, res["equity"].values, label="策略", lw=1.5, color="#27ae60")
                ax.plot(res["bench"].index, res["bench"].values, label="基准（买入持有）", lw=1.2, color="#95a5a6")
                ax.set_title("净值曲线（初始 1 元）")
                ax.legend()
                st.pyplot(fig)
                # 水下曲线
                uw = res["equity"] / res["equity"].cummax() - 1
                fig2, ax2 = plt.subplots(figsize=(10, 2.6))
                ax2.fill_between(uw.index, uw * 100, 0, color="#e74c3c", alpha=0.4)
                ax2.set_title("水下曲线（回撤深度）")
                st.pyplot(fig2)
                # 保存实验
                if st.button("💾 保存到修行日记（+30 XP 周任务「回测复现」）"):
                    exp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
                    exp_path = os.path.join(exp_dir, "experiments.json")
                    exp = {"date": today, "strategy": _sid,
                           "assets": list(_syms), "window": int(_win), "cost": _cost,
                           "metrics": {k: round(v, 4) for k, v in m.items()}}
                    existing = []
                    if os.path.exists(exp_path):
                        with open(exp_path, encoding="utf-8") as f:
                            existing = json.load(f)
                    existing.append(exp)
                    with open(exp_path, "w", encoding="utf-8") as f:
                        json.dump(existing, f, ensure_ascii=False, indent=2)
                    wk = qs.complete_weekly("backtest", char)
                    st.success("✅ 实验已存档 | 周任务「回测复现」+{} XP".format(wk))


with tab5:
    st.subheader("📜 知识图鉴（{} 条）".format(len(ENTRIES)))
    # 打卡天数分档解锁（Web 端补钩子：解锁后显示新条目）
    newly = best.check(char.total_days)
    if newly:
        st.success("📜 图鉴新解锁（打卡 {:.0f} 天）: ".format(char.total_days) +
                   ", ".join("「{}」".format(n[1]) for n in newly))
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

with tab6:
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

with tab7:
    st.subheader("📋 每日任务")
    done_today = qs.daily_done_today()
    for q in DAILY_QUESTS:
        st.write("{} **{}**：{}".format("✅" if q["id"] in done_today else "⬜", q["name"], q["desc"]))
    st.subheader("本周每周任务（各 +30 XP）")
    week_done = qs.week_done
    week_key_prefix = "{}W{}:".format(_date.today().isocalendar()[0], _date.today().isocalendar()[1])
    for q in WEEKLY_QUESTS:
        done = any(k.startswith(week_key_prefix) and k.endswith(":" + q["id"]) for k in week_done)
        st.write("{} **{}**：{}".format("✅" if done else "⬜", q["name"], q["desc"]))

with tab8:
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


with tab9:
    st.subheader("👥 匿名同行榜（隐私优先）")
    st.caption("无服务器 · 匿名 ID · 数据全在本地 · 随时可删")
    pb = PeerBoard()
    own = pb.export_card(char, ach, best, tier["name"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("匿名 ID", own["id"])
    c2.metric("等级", own["level"])
    c3.metric("XP", own["xp"])
    c4.metric("连击", "{} 天".format(own["streak"]))
    st.download_button("📤 导出我的匿名成绩单（分享给朋友）",
                       data=json.dumps(own, ensure_ascii=False, indent=2),
                       file_name="trader_card_{}.json".format(own["id"]),
                       mime="application/json")
    st.divider()
    st.subheader("📥 导入同行成绩单")
    up = st.file_uploader("上传朋友导出的 trader_card_*.json", type=["json"])
    if up is not None:
        card, err = pb.import_card_data(up.getvalue())
        if err:
            st.warning(err)
        else:
            st.success("已导入同行: {}（{} 级，XP {}）".format(card["id"], card["level"], card["xp"]))
    st.divider()
    st.subheader("🏆 本地排行榜")
    sort_by = st.selectbox("排行榜排序", ["按 XP", "按通关关卡", "按通关世界"], index=0)
    sort_key = {"按 XP": "xp", "按通关关卡": "levels", "按通关世界": "worlds"}[sort_by]
    board = pb.leaderboard(own, sort_by=sort_key)
    if len(board) <= 1:
        st.info("目前只有你自己——导出成绩单发给朋友，或导入朋友的成绩单")
    else:
        import pandas as _pd
        rows = []
        for r in board:
            avg = sum(r.get("dims", {}).values()) / len(r.get("dims", {})) if r.get("dims") else 0
            rows.append({
                "排名": r.get("rank"), "匿名ID": r.get("id"),
                "等级": r.get("level"), "XP": r.get("xp"),
                "连击": r.get("streak"), "四维均值": round(avg, 0),
                "徽章": r.get("badges"), "图鉴": r.get("bestiary"),
                "关卡": r.get("levels", 0), "世界": r.get("worlds", 0),
                "层级": r.get("tier"),
            })
        st.dataframe(_pd.DataFrame(rows), width="stretch")
    st.caption("🔒 隐私说明：ID 为本地随机码，不含邮箱/姓名/设备信息。删除 data/peers/ 目录即可彻底清除。")

    # ---- 关卡进度对比 ----
    st.divider()
    st.subheader("⚔️ 关卡进度对比（谁先通关世界）")
    peers_n = [r for r in board if r.get("id") != own.get("id")]
    if not peers_n:
        st.info("导入朋友的成绩单后，这里会显示你们的世界/关卡进度差距")
    else:
        import pandas as _pd2
        my_lv, my_wd = own.get("levels", 0), own.get("worlds", 0)
        cmp_rows = []
        for r in peers_n:
            cmp_rows.append({
                "匿名ID": r.get("id"),
                "同行关卡": r.get("levels", 0), "同行世界": r.get("worlds", 0),
                "我的关卡": my_lv, "我的世界": my_wd,
                "关卡差": r.get("levels", 0) - my_lv,
                "世界差": r.get("worlds", 0) - my_wd,
            })
        st.dataframe(_pd2.DataFrame(cmp_rows), width="stretch")
        st.caption("🟢 正数 = 同行领先你 | 🔴 负数 = 你领先同行 | 关卡 = 36 关总数，世界 = 9 世界总数")


with tab10:
    st.subheader("✅ 每日修行测试（20 题客观打分）")
    from datetime import date as _date
    today = str(_date.today())
    if char.last_date == today:
        st.success("今日已打卡（{}）".format(today))
        s_now = char.summary()
        st.pyplot(radar_chart(s_now["dims"]))
        if st.button("🔄 重新测试（覆盖今日）"):
            char.last_date = None
            char.save()
            st.rerun()
    else:
        unlock = max_level_for_xp(char.xp)
        st.info("难度：{} | 每题 0-4 分（{}）".format(level_badges(unlock), SCALE))
        qbank = questions_for(unlock)
        answers = {}
        st.markdown("### 📝 逐题回答（每维 {} 题）".format(len(qbank["math"])))
        for d in ["math", "finance", "psychology", "philosophy"]:
            st.markdown("**{} {} 维度**".format(DIM_EMOJI[d], DIM_NAMES[d]))
            answers[d] = []
            for i, q in enumerate(qbank[d], 1):
                st.markdown("**Q{}: {}**".format(i, q))
                val = st.selectbox("选择你的回答", ["— 请选择 —", "0 完全否", "1 基本否", "2 不确定", "3 基本是", "4 完全是"],
                                   key="q_{}_{}".format(d, i))
                answers[d].append(None if val == "— 请选择 —" else int(val[0]))
        if st.button("提交今日测试", type="primary", use_container_width=True):
            if any(a is None for v in answers.values() for a in v):
                st.error("还有题目未选择——请逐题选择你的真实状态（选择'2 不确定'也算一种回答）")
            else:
                dims = {d: dim_score(answers[d]) for d in answers}
                overall = overall_score(dims)
                flags = red_flags_from_answers(answers)
                gain = char.daily_checkin(dims, has_discipline_issue=len(flags) > 0)
                # 保存记录
                rec = DailyRecord(date=today, mode="evening", math=dims["math"],
                                  finance=dims["finance"], psychology=dims["psychology"],
                                  philosophy=dims["philosophy"], overall=overall,
                                  notes="Web 测试提交", trades_today=None)
                import os as _os
                _d = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data", "diary")
                _os.makedirs(_d, exist_ok=True)
                with open(_os.path.join(_d, today + ".json"), "w", encoding="utf-8") as f:
                    json.dump(rec.to_dict(), f, ensure_ascii=False, indent=2)
                st.success("打卡完成 +{} XP！今日综合分 {}（等级 {}）".format(gain, overall, grade(overall)))
                for d, v in dims.items():
                    st.write("{}: {}分".format(DIM_NAMES[d], v))
                if flags:
                    st.warning("今日纪律风险（客观推断）:")
                    for f in flags:
                        st.write("- " + f)
                else:
                    st.success("无客观纪律风险")
                s_new = char.summary()
                st.pyplot(radar_chart(s_new["dims"]))
                # 任务标记
                qs.complete_daily("water")
                # 成就检查（Web 端补钩子：打卡/连击/纪律类徽章）
                new_ach = ach.check_all(s_new)
                if new_ach:
                    st.success("🏅 新成就解锁: " + ", ".join("「{}」".format(a["name"]) for a in new_ach))


with tab11:
    st.subheader("🧠 客观知识测试（标准答案，骗不了自己）")
    ks = KnowledgeSystem()
    unlock = max_level_for_xp(char.xp)
    pool = [q for q in K_QUESTIONS if q["level"] <= unlock]
    st.info("当前解锁：{}（{} 题）| 知识分：**{}**（做对 {}/{}）".format(
        level_badges(unlock), len(pool), ks.score(), ks.correct, ks.total))

    # 今日题目固定（session 缓存，选择不换题；隔天自动换新）
    import random
    cache_key = "kq_daily_" + today
    if cache_key not in st.session_state:
        st.session_state[cache_key] = random.sample(pool, min(5, len(pool)))
    daily = st.session_state[cache_key]

    picks = {}
    for i, q in enumerate(daily, 1):
        st.markdown("**Q{}（{}·{}级）: {}**".format(i, q["topic"], "🐣" if q["level"]==1 else "🌱" if q["level"]==2 else "🎓", q["q"]))
        picks[q["id"]] = st.selectbox(
            "选择答案", ["— 请选择 —"] + q["opts"], key="k_{}".format(q["id"]))
        st.caption("提示：答对解锁图鉴「{}」".format(q["figure"]))

    if st.button("提交知识测试", type="primary", use_container_width=True):
        n_ok = 0
        results = []
        for q in daily:
            picked = picks[q["id"]]
            if picked == "— 请选择 —":
                results.append((q, None))
                continue
            idx = q["opts"].index(picked)
            ok = ks.record(q, idx, today)
            n_ok += ok
            results.append((q, idx))
        for q, idx in results:
            mark = "✅" if idx == q["ans"] else "❌"
            st.markdown("{} **{}**".format(mark, q["q"]))
            if idx is not None and idx != q["ans"]:
                st.error("你的答案: {} | 正确答案: {} | {}".format(
                    q["opts"][idx], q["opts"][q["ans"]], q["exp"]))
            elif idx == q["ans"]:
                st.success(q["exp"])
        st.success("本次 {}/{} 题正确 | 累计知识分 {}（{}/{}）".format(
            n_ok, len(daily), ks.score(), ks.correct, ks.total))
        # 图鉴联动：答对的题解锁图鉴
        if n_ok > 0:
            best_ = Bestiary()
            done_ids = set(best_.unlocked)
            newly = []
            for q in daily:
                fid = q["figure"]
                if fid not in done_ids:
                    best_.unlocked.append(fid)
                    done_ids.add(fid)
                    newly.append(fid)
            best_.save()
            if newly:
                st.success("📜 图鉴新解锁: {}".format(", ".join(newly)))
        # 成就检查（Web 端补钩子）
        new_ach = ach.check_all(char.summary())
        if new_ach:
            st.success("🏅 新成就解锁: " + ", ".join("「{}」".format(a["name"]) for a in new_ach))

    st.divider()
    st.subheader("📕 错题本（复习）")
    if ks.wrong:
        for w in ks.wrong[-5:][::-1]:
            st.warning("Q: {}（你选了「{}」，正确答案「{}」）".format(
                w["q"], K_QUESTIONS[[q for q in K_QUESTIONS if q["id"]==w["id"]][0]]["opts"][w["picked"]],
                K_QUESTIONS[[q for q in K_QUESTIONS if q["id"]==w["id"]][0]]["opts"][w["correct_ans"]]))
    else:
        st.info("暂无错题——继续保持！")


with tab4:
    st.subheader("🎮 学习关卡：把书变成游戏，把市场变成教材")
    prog = Progress()

    # ---- 世界地图 ----
    cols = st.columns(9)
    for i, ch in enumerate(sorted(WORLDS)):
        done_n, total_n = prog.world_progress(ch)
        with cols[i]:
            mark = "✅" if done_n == total_n else "🔒" if ch > 1 and done_n == 0 else "🌍"
            st.markdown("{} W{} {}".format(mark, ch, WORLDS[ch]["name"]))
    st.caption("已通关 {} / {} 关 · 完成前一章全部关卡解锁下一章世界".format(
        len(prog.completed), len(LEVELS)))

    def _evidence(ttype, info):
        """答后展示真实数据依据"""
        if "corr" in info:
            return "（黄金×沪深300 相关系数 {:.2f}）".format(info["corr"])
        if "weight_a" in info:
            return "（风险平价权重：{} {:.0%} vs {} {:.0%}）".format(
                info.get("name_a", "A"), info["weight_a"], info.get("name_b", "B"), 1 - info["weight_a"])
        if "vol_a" in info and "weight_a" not in info:
            return "（茅台年化波动 {:.0%} vs ETF {:.0%}）".format(info["vol_a"], info["vol_b"])
        if "ret_a" in info:
            return "（纳指 {:+.1%} vs 沪深300 {:+.1%}）".format(info["ret_a"], info["ret_b"])
        if "corrs" in info:
            return "（{}，最低者 {}）".format(info["corrs"], info["lowest"])
        if "moms" in info and "weak" in info:
            return "（20日动量：{}，最弱 {}）".format(info["moms"], info["weak"])
        if "moms" in info:
            return "（20日动量：{}，最强 {}）".format(info["moms"], info["best"])
        if "ic" in info:
            return "（Spearman IC = {ic:+.2f}）".format(**info)
        if "g_mom" in info:
            return "（动量 黄金 {g_mom:+.1%} vs 原油 {o_mom:+.1%}；收益 黄金 {g_ret:+.1%} vs 原油 {o_ret:+.1%}）".format(**info)
        if "agree" in info:
            return "（完全一致 {agree}/4 只——IC 体检结论）".format(**info)
        if "plr" in info:
            return "（盈亏比 {:.2f} = 平均盈利 {:.2%} ÷ 平均亏损 {:.2%}）".format(
                info["plr"], info.get("gain", 0), info.get("loss", 0))
        if "dd" in info and "hi" in info:
            return "（真实路径：峰值 {hi:.3f} → 谷底 {lo:.3f}，最大回撤 {dd:.0%}，全年 {ret:+.1%}）".format(
                **info)
        if "dd" in info:
            return "（真实最大回撤 {dd:.0%}，本金 {wan:.0f} 万）".format(**info)
        if "ret" in info and "strat" in info:
            return "（基准 {ret:+.1%} vs 策略 {strat:.0%}，超额 {:.0f} 个百分点）".format(
                (info["strat"] - info["ret"]) * 100, **info)
        if "years" in info:
            return "（{}）".format(info["years"])
        if "ma20" in info:
            return "（信号：MA20 {} / MA60 {} / MA120 {}，收盘 {}）".format(
                info["sigs"][0], info["sigs"][1], info["sigs"][2], info["price"])
        if "in" in info and "out" in info:
            return "（样本内 {in:+.1%} vs 样本外 {out:+.1%}——闭卷考翻盘？）".format(**info)
        if "total" in info:
            return "（三段累乘 {total:+.1%} = (1+2023)(1+2024)(1+2025)-1）".format(**info)
        if "odd" in info:
            return "（奇数年 {odd:+.1%} vs 偶数年 {even:+.1%}——切法一变就翻脸）".format(**info)
        if "hs" in info:
            return "（真实锚点：沪深300 {hs:+.1%} / 纳指 {nq:+.1%} / 黄金 {gold:+.1%}）".format(**info)
        if "shares" in info:
            max_shares = int(info["shares"] // info["lot"]) * info["lot"]
            gap = info["target"] - max_shares * info["price"]
            return "（{target:,} 元 ÷ {price} 元 = {shares:.0f} 份 → 整手 {lot} 取整 → {max_shares:.0f} 份，缺口 {gap:.0f} 元）".format(
                max_shares=max_shares, gap=gap, **info)
        if "commission" in info:
            return "（佣金 {commission:.2f}（最低 5 元生效）+ 滑点 {slippage:.2f} = {total:.2f} 元）".format(**info)
        if "pct" in info and "price" in info and "date" in info:
            return "（滑点 +{pct:.1%}：{price} → {:.3f}）".format(info["price"] * (1 + info["pct"]), **info)
        if "real" in info and "cost" in info:
            alpha = info["real"] + info["cost"] - info["ret"]
            return "（{real:+.1%} = 市场 {ret:+.1%} + 超额 {:+.1%} - 成本 {cost:.1%}）".format(
                alpha, **info)
        if "gap" in info:
            return "（差额 {gap:.1%} = 交易成本 → 问题在执行层）".format(**info)
        if "cond" in info:
            return "（{n} 个大跌日黄金平均 {cond:+.2%} vs 全年 {all:+.2%}）".format(**info)
        if "v60" in info:
            return "（60日 {v60:.0%} vs 一年 {v252:.0%}）".format(**info)
        if "cost" in info and "ret" in info:
            return "（回测 {ret:+.1%} - 年成本 {cost:.1%} = {:+.1%}）".format(
                info["ret"] - info["cost"], **info)
        if "ret" in info and "dd" not in info:
            return "（近一年真实涨幅 {ret:+.1%}）".format(**info)
        return ""

    def _check_level_achievements(prog_, char_):
        """关卡完成后的成就检查（补充关卡统计进 state）"""
        state = dict(char_.summary())
        state["levels_done"] = len(prog_.completed)
        state["worlds_cleared"] = prog_.worlds_cleared()
        state["quiz_correct_total"] = prog_.quiz_correct_total
        new = ach.check_all(state)
        if new:
            st.success("🏅 新成就解锁: " + ", ".join("「{}」".format(a["name"]) for a in new))

    def _render_level(lid_, lvl, review=False, boss_revive=False):
        """渲染一个关卡：知识卡 → 实战任务 → 测验。
        review=True 为每日复习（+5 XP）；boss_revive=True 为每周 BOSS 复战（+5 XP + 周任务 +30 XP）"""
        ch = lvl["chapter"]
        if ch > 1:
            prev_done, prev_total = prog.world_progress(ch - 1)
            if prev_done < prev_total:
                st.warning("🔒 世界 {} 尚未解锁——先完成世界 {} 的全部关卡".format(
                    WORLDS[ch]["name"], WORLDS[ch - 1]["name"]))
                return

        st.markdown("### {} · {} {}".format(
            WORLDS[ch]["name"], "BOSS" if lvl.get("boss") else "关卡", lvl["name"]))
        st.caption("奖励: +{} XP{} | 训练维度: {} | {}".format(
            lvl["xp"],
            "（复战 +5 XP + 周任务 +30 XP）" if boss_revive else "（复习 +5 XP）" if review else "（首通）",
            lvl["dim"], WORLDS[ch]["title"]))
        st.progress(prog.world_progress(ch)[0] / prog.world_progress(ch)[1])

        with st.expander("📖 知识卡（先学）", expanded=True):
            st.markdown(lvl["knowledge"])
            # 真实数据配图（概念有图可看）
            if lvl.get("chart"):
                from trader_growing.charts import CHART_FNS
                fig = CHART_FNS.get(lvl["chart"])
                if fig:
                    try:
                        f = fig()
                        if f is not None:
                            st.pyplot(f)
                    except Exception:
                        pass  # 图渲染失败不阻塞关卡

        # ---- 实战任务（真实数据） ----
        st.markdown("### 🧪 实战任务")
        ans_true, info = solve_task(lvl["task"]["type"], lvl["task"].get("args", {}))
        if ans_true is None:
            st.error("{}——先运行 python scripts/update_data.py".format(info))
            return
        st.markdown(lvl["task"]["text"].format(**info))
        st.caption("提示: " + lvl["task"].get("hint", ""))

        task_key = "task_done_" + lid_
        if prog.done(lid_) and not review:
            st.success("本关已通关 ✅（下方复习区可每日再战）")
        else:
            user_input = st.text_input("你的答案", key="task_in_" + lid_)
            if st.button("提交任务答案", key="task_btn_" + lid_):
                try:
                    val = int(user_input.strip())
                except ValueError:
                    st.error("请输入数字")
                    st.stop()
                if val == ans_true:
                    st.session_state[task_key] = True
                    st.success("✅ 任务正确！真实答案就是 {}{}".format(ans_true, _evidence(lvl["task"]["type"], info)))
                else:
                    st.session_state[task_key] = False
                    st.error("❌ 不对，再想想。真实答案是 {}{}".format(ans_true, _evidence(lvl["task"]["type"], info)))

        # ---- 测验 ----
        if st.session_state.get(task_key):
            st.markdown("### 🧠 关卡测验（答对 2/3 通关{}）".format(
                "，复战得 +5 XP + 周任务 +30 XP" if boss_revive else "，复习得 +5 XP" if review else ""))
            for i, q in enumerate(lvl["quiz"], 1):
                st.selectbox("Q{}: {}".format(i, q["q"]), ["— 请选择 —"] + q["opts"],
                             key="quiz_{}_{}".format(lid_, i))
            if st.button("提交测验", key="quiz_btn_" + lid_):
                ok_list = []
                for i, q in enumerate(lvl["quiz"], 1):
                    pick = st.session_state.get("quiz_{}_{}".format(lid_, i))
                    ok = pick is not None and pick != "— 请选择 —" and q["opts"].index(pick) == q["ans"]
                    ok_list.append(ok)
                    if ok:
                        st.success("Q{} ✅ {}".format(i, q["exp"]))
                    else:
                        st.error("Q{} ❌ 正确答案: {} | {}".format(i, q["opts"][q["ans"]], q["exp"]))
                if sum(ok_list) >= 2:
                    prog.complete(lid_, sum(ok_list), attempts=1)
                    if not review:
                        # 首通奖励（新手期双倍）
                        got = char.gain_xp(lvl["xp"])
                        char.dims[lvl["dim"]] = min(100, char.dims[lvl["dim"]] + 5)
                        char.save()
                        best_ = Bestiary()
                        if lvl["figure"] not in best_.unlocked:
                            best_.unlocked.append(lvl["figure"])
                            best_.save()
                        st.balloons()
                        st.success("🎉 关卡通关！+{} XP{} | 维度 {} +5 | 图鉴「{}」点亮".format(
                            got, "（新手双倍）" if got != lvl["xp"] else "", lvl["dim"], lvl["figure"]))
                        _check_level_achievements(prog, char)
                    elif boss_revive:
                        if prog.boss_revive_done_this_week(lid_):
                            st.info("本周已复战过这个 BOSS（每周限一次）——下周再来")
                        else:
                            prog.mark_boss_revive(lid_)
                            got = char.gain_xp(5)
                            wk_xp = qs.complete_weekly("boss_revive", char)
                            st.balloons()
                            st.success("🎉 BOSS 复战成功！+{} XP{} | 周任务「BOSS 复战」+{} XP".format(
                                got, "（新手双倍）" if got != 5 else "", wk_xp))
                    else:
                        if prog.reviewed_today(lid_):
                            st.info("今日已复习过本关（每日每关限一次）——明天再来")
                        else:
                            prog.mark_reviewed(lid_)
                            got = char.gain_xp(5)
                            char.dims[lvl["dim"]] = min(100, char.dims[lvl["dim"]] + 1)
                            char.save()
                            st.balloons()
                            st.success("🎉 复习完成！+{} XP{} | 维度 {} +1".format(
                                got, "（新手双倍）" if got != 5 else "", lvl["dim"]))
                else:
                    st.warning("测验未通过（{}/3）——重新读知识卡再试".format(sum(ok_list)))

    # ---- 当前关卡（主线） ----
    with st.expander("🎯 当前关卡 · 推主线（首通 +15~30 XP）", expanded=True):
        lid, cur = prog.next_level()
        if cur is None:
            st.success("🎉 全部关卡已完成！下方复习区可每天再战真实数据任务")
        else:
            _render_level(lid, cur)

    # ---- 已通关关卡 · 每日复习 ----
    with st.expander("🔄 每日复习（+5 XP/关/天，答案随行情变）", expanded=False):
        if not prog.completed:
            st.info("通关第一个关卡后，这里可以每天复习——市场数据每天在变，答案每天不同")
        else:
            pick = st.selectbox("选择要复习的关卡", prog.completed,
                                format_func=lambda l: "{} · {}".format(l, LEVELS[l]["name"]))
            _render_level(pick, LEVELS[pick], review=True)

    # ---- BOSS 复战（每周） ----
    with st.expander("⚔️ BOSS 复战（每周 +30 XP，用本周行情再战 BOSS）", expanded=False):
        st.caption("已通关的 BOSS 每周可复战一次：复战 +5 XP + 周任务「BOSS 复战」+30 XP（每周限一次）")
        boss_ids = [l for l in prog.completed if l.endswith("-BOSS")]
        if not boss_ids:
            st.info("先通关任意一个 BOSS 关（如 W1 的「过拟合挑战」），即可解锁每周复战")
        else:
            done_this_week = [l for l in boss_ids if prog.boss_revive_done_this_week(l)]
            if done_this_week:
                st.success("本周已复战: " + ", ".join("「{}」".format(LEVELS[l]["name"]) for l in done_this_week))
            else:
                st.info("本周还未复战任何 BOSS——选一个开打！")
            pick = st.selectbox("选择要复战的 BOSS", boss_ids,
                                format_func=lambda l: "W{} · {}".format(l.split("-")[0], LEVELS[l]["name"]))
            _render_level(pick, LEVELS[pick], review=True, boss_revive=True)


with tab12:
    st.subheader("📅 修行周报（每周自动汇总）")
    wr = WeeklyReport()
    cur = wr.build(char)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("打卡", "{} 天".format(len(cur["checkin_days"])))
    c2.metric("首通关卡", "{} 关".format(len(cur["new_levels"])))
    c3.metric("复习", "{} 次".format(cur["reviews"]))
    c4.metric("BOSS 复战", "{} 次".format(cur["boss_revives"]))
    c5.metric("周任务", "{}/{}".format(len(cur["week_quests"]), 4))

    c6, c7, c8 = st.columns(3)
    c6.metric("知识分", "{}/{}".format(cur["knowledge"]["correct"], cur["knowledge"]["total"]))
    c7.metric("图鉴 / 徽章", "{} 条 / {} 枚".format(cur["bestiary"], cur["badges"]))
    c8.metric("关卡进度", "{}/{} · 世界 {}/9".format(cur["total_levels"], 36, cur["total_worlds"]))

    st.markdown("**本周打卡日历**")
    wk_cal = ["✅" if d in cur["checkin_days"] else "⬜" for d in
              ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]]
    st.write(" ".join("{} {}".format(d, m) for d, m in zip(
        ["周一", "周二", "周三", "周四", "周五", "周六", "周日"], wk_cal)))

    if cur["new_levels"]:
        st.markdown("**本周新通关**")
        st.write(" → ".join("「{}」".format(n["name"]) for n in cur["new_levels"]))

    st.divider()
    st.markdown("**💡 下周建议**")
    for tip in wr.suggestions(cur):
        st.info(tip)

    st.divider()
    st.markdown("**📚 历史周报**")
    hist = wr.history()
    if not hist:
        st.info("还没有历史周报——每周一自动生成新的一期")
    else:
        weeks = [h["week"] for h in hist]
        pick_w = st.selectbox("查看历史周报", weeks, index=0)
        h = wr.load_week(pick_w)
        if h:
            st.caption("{} · 打卡 {} 天 | 首通 {} 关 | 复战 {} 次 | 知识 {}/{}".format(
                h.get("generated_at", ""), len(h.get("checkin_days", [])),
                len(h.get("new_levels", [])), h.get("boss_revives", 0),
                h.get("knowledge", {}).get("correct", 0), h.get("knowledge", {}).get("total", 0)))

    # 自动生成本周快照（仅当还没有）
    import os as _os
    snap_path = _os.path.join(os.path.dirname(_os.path.abspath(__file__)), "data",
                              "weekly_reports", cur["week"] + ".json")
    if not _os.path.exists(snap_path):
        wr.save_current(cur)
        st.caption("📸 本周周报已自动保存快照")
