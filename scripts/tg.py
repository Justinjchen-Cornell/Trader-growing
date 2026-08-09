# -*- coding: utf-8 -*-
"""Trader-growing 主 CLI
用法:
  python scripts/tg.py dashboard   # 四资产看板
  python scripts/tg.py plan        # 今日策略计划（中庸策略）
  python scripts/tg.py reconcile   # 纪律对账（计划 vs 最新日记）
  python scripts/tg.py status      # 角色 / 花园 / 层级
  python scripts/tg.py check       # 每日打卡
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


def cmd_check():
    char = Character()
    print("每日修行打卡：四维打分（0-100，回车默认 50）")
    dims = {}
    for d in ["math", "finance", "psychology", "philosophy"]:
        v = input("  {}: ".format(d)).strip()
        try:
            dims[d] = float(v) if v else 50.0
        except ValueError:
            dims[d] = 50.0
    gain = char.daily_checkin(dims)
    print("打卡完成 +{} XP | 连击 {} 天 | 等级 {}".format(gain, char.streak, char.level[1]))
    s = char.summary()
    print(draw_garden(s["dims"]))
    ach = AchievementSystem()
    new = ach.check_all(s)
    if new:
        print("新徽章: {}".format(", ".join(a["name"] for a in new)))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"dashboard": cmd_dashboard, "plan": cmd_plan, "reconcile": cmd_reconcile,
     "status": cmd_status, "check": cmd_check}.get(cmd, cmd_status)()
