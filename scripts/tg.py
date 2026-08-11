# -*- coding: utf-8 -*-
"""Trader-growing 主 CLI
用法:
  python scripts/tg.py dashboard   # 四资产看板
  python scripts/tg.py plan        # 今日策略计划（中庸策略）
  python scripts/tg.py reconcile   # 纪律对账（计划 vs 最新日记）
  python scripts/tg.py status      # 角色 / 花园 / 层级 / 图鉴
  python scripts/tg.py check       # 每日打卡
  python scripts/tg.py quests      # 任务清单（每日 + 每周）
  python scripts/tg.py quest-done <id>  # 完成每周任务
  python scripts/tg.py stats       # 偏差趋势统计
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from trader_growing.character import Character
from trader_growing.achievements import AchievementSystem
from trader_growing.garden import draw_garden
from trader_growing.dashboard import print_dashboard
from trader_growing.strategy_bridge import load_plan
from trader_growing.journal_bridge import load_latest
from trader_growing.reconcile import reconcile
from trader_growing.tiers import TierSystem
from trader_growing.models import Plan
from trader_growing.bestiary import Bestiary
from trader_growing.quests import QuestSystem, DAILY_QUESTS, WEEKLY_QUESTS
from trader_growing.stats import report as stats_report
from trader_growing.scoring_guide import show_guide
from trader_growing.questions import QUESTIONS, DIM_NAMES, DIM_EMOJI, SCALE, dim_score, overall_score, grade, red_flags_from_answers
from trader_growing.models import DailyRecord
import json


def plan_from_dict(d):
    if not d:
        return None
    return Plan(date=d.get("date", ""), asset=d.get("asset", ""), symbol=d.get("symbol", ""),
                signal=d.get("signal", ""), cap=d.get("cap", 0), action=d.get("action", ""),
                close=d.get("close", 0), stop_loss_line=d.get("stop_loss_line", 0),
                advice=d.get("advice", ""))


def cmd_dashboard():
    print_dashboard()


def cmd_plan():
    d = load_plan()
    if not d:
        print("未找到 plan_today.json —— 请先在 zhongyong_strategy 目录运行 plan.py")
        return
    print("今日策略计划: {} ({})".format(d.get("asset"), d.get("date")))
    print("  信号: {} | 动作: {} | 仓位上限: {:.0%} | 止损线: {}".format(
        d.get("signal"), d.get("action"), d.get("cap", 0), d.get("stop_loss_line")))
    print("  建议: {}".format(d.get("advice", "")))


def cmd_reconcile():
    rec = load_latest()
    plan = plan_from_dict(load_plan())
    if not rec:
        print("未找到修行日记 —— 请先运行修行日记 daily_check.py --mode evening")
        return
    res = reconcile(plan, rec)
    print(res.to_report())
    # 更新层级红牌统计
    tiers = TierSystem()
    tiers.record_day(not res.clean)


def cmd_status():
    char = Character()
    s = char.summary()
    print("等级: {} ({}) | XP: {} | 连击: {} 天 | 累计: {} 天".format(
        s["level"], s["level_desc"], s["xp"], s["streak"], s["total_days"]))
    print(draw_garden(s["dims"]))
    ach = AchievementSystem()
    print("徽章: {}".format(", ".join(a["name"] for a in ach.summary()) or "暂无"))
    # 层级
    tiers = TierSystem()
    avg = sum(s["dims"].values()) / len(s["dims"]) if s["dims"] else 0
    tier = tiers.current_tier(s["total_days"], avg)
    print("当前层级: {}（{}）".format(tier["name"], tier["desc"]))
    nxt = tiers.next_requirements(s["total_days"], avg)
    if nxt:
        print("下一级 {}: {}".format(nxt["tier"]["name"], "、".join(nxt["missing"] or ["条件已满足，继续观察"])))
    best = Bestiary()
    done, todo = best.summary(s["total_days"])
    print("图鉴: {}/{} 已收集".format(len(done), len(done) + len(todo)))


def _ask_score(q):
    while True:
        v = input("  ➤ [0-4]: ").strip()
        if not v:
            return 2
        try:
            val = int(v)
            if 0 <= val <= 4:
                return val
        except ValueError:
            pass
        print("    请输入 0-4")


def cmd_check():
    char = Character()
    quick = "--quick" in sys.argv
    print()
    print("=" * 55)
    print("  🌱 每日修行测试（20 题客观打分）")
    print("=" * 55)
    print("  每题 0-4 分: " + SCALE)
    print("  维度分自动计算（原始分/满分*100），拒绝拍脑袋")
    print()

    answers = {}
    dims = {}
    for d in ["math", "finance", "psychology", "philosophy"]:
        print("  {} {} 维度（5 题）".format(DIM_EMOJI.get(d, ""), DIM_NAMES[d]))
        print("  " + "-" * 45)
        if quick:
            show_guide(d)
            v = input("  {} 总分 [0-100]: ".format(DIM_NAMES[d])).strip()
            try:
                dims[d] = float(v) if v else 50.0
            except ValueError:
                dims[d] = 50.0
            answers[d] = [2] * 5
        else:
            qs = []
            for i, q in enumerate(QUESTIONS[d], 1):
                print("  Q{}: {}".format(i, q))
                qs.append(_ask_score(q))
            answers[d] = qs
            dims[d] = dim_score(qs)
            print("  → {} {}分 (等级{})".format(DIM_NAMES[d], dims[d], grade(dims[d])))
        print()

    overall = overall_score(dims)
    print("=" * 55)
    print("  今日综合分: {}（等级 {}）".format(overall, grade(overall)))

    # 客观红牌推断
    flags = red_flags_from_answers(answers)
    if flags:
        print("  🔴 今日纪律风险（客观推断）:")
        for f in flags:
            print("    - " + f)
    else:
        print("  ✅ 今日无客观纪律风险")

    # 打卡（有红牌时 XP 减半）
    issue = len(flags) > 0
    gain = char.daily_checkin(dims, has_discipline_issue=issue)
    print("  打卡 +{} XP | 连击 {} 天 | 等级 {}".format(gain, char.streak, char.level[1]))

    # 保存当日记录（data/diary/ 兼容格式）
    rec = DailyRecord(date=str(__import__("datetime").date.today()), mode="evening",
                      math=dims["math"], finance=dims["finance"],
                      psychology=dims["psychology"], philosophy=dims["philosophy"],
                      overall=overall, trades_today=None)
    diary_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "data", "diary")
    os.makedirs(diary_dir, exist_ok=True)
    with open(os.path.join(diary_dir, rec.date + ".json"), "w", encoding="utf-8") as f:
        json.dump(rec.to_dict(), f, ensure_ascii=False, indent=2)

    s = char.summary()
    print(draw_garden(s["dims"]))
    ach = AchievementSystem()
    new = ach.check_all(s)
    if new:
        print("新徽章: {}".format(", ".join(a["name"] for a in new)))


def cmd_quests():
    qs = QuestSystem()
    done_today = qs.daily_done_today()
    print("今日每日任务:")
    for q in DAILY_QUESTS:
        mark = "OK" if q["id"] in done_today else "  "
        print("  [{}] {}：{}".format(mark, q["name"], q["desc"]))
    print("本周每周任务:")
    for q in WEEKLY_QUESTS:
        print("  [  ] {}：{} (+{} XP)".format(q["name"], q["desc"], q["xp"]))
    print()
    print("完成每周任务: python scripts/tg.py quest-done factor|param|backtest")


def cmd_quest_done():
    qid = sys.argv[2] if len(sys.argv) > 2 else ""
    if qid not in [q["id"] for q in WEEKLY_QUESTS]:
        print("未知任务: {}（可选: {}）".format(qid, "/".join(q["id"] for q in WEEKLY_QUESTS)))
        return
    char = Character()
    qs = QuestSystem()
    xp = qs.complete_weekly(qid, char)
    if xp:
        print("完成任务 +{} XP | 当前 XP: {} | 等级: {}".format(xp, char.xp, char.level[1]))
    else:
        print("本周该任务已完成")


def cmd_stats():
    stats_report()

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"dashboard": cmd_dashboard, "plan": cmd_plan, "reconcile": cmd_reconcile,
     "status": cmd_status, "check": cmd_check, "quests": cmd_quests,
     "quest-done": cmd_quest_done, "stats": cmd_stats}.get(cmd, cmd_status)()

