# -*- coding: utf-8 -*-
"""Trader-growing 全流程演示：打卡 -> 计划 -> 对账 -> 成长"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from trader_growing.character import Character
from trader_growing.achievements import AchievementSystem
from trader_growing.models import DailyRecord, Plan
from trader_growing.reconcile import reconcile
from trader_growing.garden import draw_garden

# 1. 角色
char = Character()
ach = AchievementSystem()

print("=" * 50)
print("  Trader-growing · 全流程演示")
print("=" * 50)

# 2. 模拟 3 天：第 1 天无偏差，第 2 天有偏差（冲动交易），第 3 天良好
days = [
    DailyRecord(date="2026-08-07", math=75, finance=80, psychology=70, philosophy=65,
                overall=72.5, trades_today={"traded_today": False, "followed_plan": True,
                "impulse_trade": False, "moved_stop_loss": False}),
    DailyRecord(date="2026-08-08", math=55, finance=40, psychology=60, philosophy=70,
                overall=56.25, notes="没忍住加仓了",
                trades_today={"traded_today": True, "followed_plan": False,
                "impulse_trade": True, "moved_stop_loss": True, "max_drawdown_pct": 3.2}),
    DailyRecord(date="2026-08-09", math=80, finance=85, psychology=75, philosophy=80,
                overall=80, trades_today={"traded_today": False, "followed_plan": True,
                "impulse_trade": False, "moved_stop_loss": False}),
]

# 策略计划：中庸策略输出（HOLD 空仓建议）
plan = Plan(date="2026-08-08", asset="沪深300ETF", symbol="510300.SS",
            signal="HOLD", cap=0.5, action="持有不动", close=4.633,
            stop_loss_line=3.9381)

for rec in days:
    # 打卡
    dims = {"math": rec.math, "finance": rec.finance, "psychology": rec.psychology,
            "philosophy": rec.philosophy}
    issue = bool(rec.trades_today and (rec.trades_today.get("impulse_trade")
                or rec.trades_today.get("moved_stop_loss")))
    gain = char.daily_checkin(dims, has_discipline_issue=issue, checkin_date=rec.date)
    # 对账（仅第 2 天有计划）
    res = reconcile(plan if rec.date == plan.date else None, rec)
    print()
    print("【{}】打卡 +{} XP | 连击 {} | 偏差 {} 条".format(
        rec.date, gain, char.streak, len(res.issues)))
    if res.issues:
        for it in res.issues:
            print("    🔴 " + it)

# 3. 成就检查
state = char.summary()
new_achs = ach.check_all(state)

# 4. 展示
print()
print("=" * 50)
print("  角色状态")
print("=" * 50)
s = char.summary()
print("  等级: {}（{}）".format(s["level"], s["level_desc"]))
print("  XP: {}（下一级 {}）".format(s["xp"], s["next_level_xp"]))
print("  连击: {} 天 | 累计打卡: {} 天".format(s["streak"], s["total_days"]))
print()
print(draw_garden(s["dims"]))
print()
print("  已解锁徽章: {}".format([a["name"] for a in ach.summary()] or "暂无"))
if new_achs:
    print("  🎉 新徽章: {}".format(", ".join(a["name"] for a in new_achs)))
print()
print("=" * 50)
print("  演示完毕。真实使用：python scripts/daily_flow.py")
print("=" * 50)
