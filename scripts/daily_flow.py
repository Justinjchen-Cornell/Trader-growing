# -*- coding: utf-8 -*-
"""每日流程 CLI：打卡 -> 看计划 -> 对账 -> 成长
用法: python scripts/daily_flow.py check   # 打卡(输入四维分数)
      python scripts/daily_flow.py status  # 查看角色与花园
      python scripts/daily_flow.py plan    # 查看今日策略计划
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from trader_growing.character import Character
from trader_growing.achievements import AchievementSystem
from trader_growing.garden import draw_garden

def cmd_check():
    char = Character()
    print("每日修行打卡：四维打分（0-100）")
    dims = {}
    for d in ["math", "finance", "psychology", "philosophy"]:
        v = input("  {} 维度分数: ".format(d)).strip()
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
        print("🎉 新徽章: {}".format(", ".join(a["name"] for a in new)))

def cmd_status():
    char = Character()
    s = char.summary()
    print("等级: {} ({}) | XP: {} | 连击: {} 天 | 累计: {} 天".format(
        s["level"], s["level_desc"], s["xp"], s["streak"], s["total_days"]))
    print(draw_garden(s["dims"]))
    ach = AchievementSystem()
    print("徽章: {}".format(", ".join(a["name"] for a in ach.summary()) or "暂无"))

def cmd_plan():
    plan_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "..", "zhongyong_strategy", "plan_today.json")
    if os.path.exists(plan_path):
        import json
        with open(plan_path, encoding="utf-8") as f:
            p = json.load(f)
        print("今日计划: {} ({})".format(p.get("asset"), p.get("date")))
        print("  信号: {} | 动作: {} | 仓位上限: {:.0%} | 止损线: {}".format(
            p.get("signal"), p.get("action"), p.get("cap", 0), p.get("stop_loss_line")))
    else:
        print("未找到 plan_today.json —— 请先在 zhongyong_strategy 运行 plan.py")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"check": cmd_check, "status": cmd_status, "plan": cmd_plan}.get(cmd, cmd_status)()
