# -*- coding: utf-8 -*-
"""Trader-growing · Web 界面（Streamlit）
运行: streamlit run app.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
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

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(
    ["🏠 状态", "🌍 四资产看板", "📜 图鉴", "📊 成长", "📋 任务", "🏅 徽章", "👥 同行榜", "✅ 每日测试", "🧠 知识测试", "🎮 学习关卡"])

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


with tab7:
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
    board = pb.leaderboard(own)
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


with tab8:
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


with tab9:
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

    st.divider()
    st.subheader("📕 错题本（复习）")
    if ks.wrong:
        for w in ks.wrong[-5:][::-1]:
            st.warning("Q: {}（你选了「{}」，正确答案「{}」）".format(
                w["q"], K_QUESTIONS[[q for q in K_QUESTIONS if q["id"]==w["id"]][0]]["opts"][w["picked"]],
                K_QUESTIONS[[q for q in K_QUESTIONS if q["id"]==w["id"]][0]]["opts"][w["correct_ans"]]))
    else:
        st.info("暂无错题——继续保持！")


with tab10:
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
        if "vol_a" in info:
            return "（茅台年化波动 {:.0%} vs ETF {:.0%}）".format(info["vol_a"], info["vol_b"])
        if "ret_a" in info:
            return "（纳指 {:+.1%} vs 沪深300 {:+.1%}）".format(info["ret_a"], info["ret_b"])
        if "corrs" in info:
            return "（{}，最低者 {}）".format(info["corrs"], info["lowest"])
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

    def _render_level(lid_, lvl, review=False):
        """渲染一个关卡：知识卡 → 实战任务 → 测验。review=True 为每日复习（+5 XP）"""
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
            lvl["xp"], "（复习 +5 XP）" if review else "（首通）", lvl["dim"], WORLDS[ch]["title"]))
        st.progress(prog.world_progress(ch)[0] / prog.world_progress(ch)[1])

        with st.expander("📖 知识卡（先学）", expanded=True):
            st.markdown(lvl["knowledge"])

        # ---- 实战任务（真实数据） ----
        st.markdown("### 🧪 实战任务")
        ans_true, info = solve_task(lvl["task"]["type"])
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
                "，复习得 +5 XP" if review else ""))
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
                        # 首通奖励
                        char.xp += lvl["xp"]
                        char.dims[lvl["dim"]] = min(100, char.dims[lvl["dim"]] + 5)
                        char.save()
                        best_ = Bestiary()
                        if lvl["figure"] not in best_.unlocked:
                            best_.unlocked.append(lvl["figure"])
                            best_.save()
                        st.balloons()
                        st.success("🎉 关卡通关！+{} XP | 维度 {} +5 | 图鉴「{}」点亮".format(
                            lvl["xp"], lvl["dim"], lvl["figure"]))
                        _check_level_achievements(prog, char)
                    else:
                        if prog.reviewed_today(lid_):
                            st.info("今日已复习过本关（每日每关限一次）——明天再来")
                        else:
                            prog.mark_reviewed(lid_)
                            char.xp += 5
                            char.dims[lvl["dim"]] = min(100, char.dims[lvl["dim"]] + 1)
                            char.save()
                            st.balloons()
                            st.success("🎉 复习完成！+5 XP | 维度 {} +1".format(lvl["dim"]))
                else:
                    st.warning("测验未通过（{}/3）——重新读知识卡再试".format(sum(ok_list)))

    # ---- 下一个未完成关卡 ----
    lid, cur = prog.next_level()
    if cur is None:
        st.success("🎉 全部关卡已完成！下方复习区可每天再战真实数据任务")
    else:
        _render_level(lid, cur)

    # ---- 已通关关卡 · 每日复习 ----
    st.divider()
    st.subheader("🔄 已通关关卡 · 每日复习（+5 XP，每日每关限一次）")
    if not prog.completed:
        st.info("通关第一个关卡后，这里可以每天复习——市场数据每天在变，答案每天不同")
    else:
        pick = st.selectbox("选择要复习的关卡", prog.completed,
                            format_func=lambda l: "{} · {}".format(l, LEVELS[l]["name"]))
        _render_level(pick, LEVELS[pick], review=True)
