# -*- coding: utf-8 -*-
"""修行周报：每周自动汇总修行数据（打卡/关卡/复习/复战/任务/知识），给出下周建议

数据全部来自现有存档（diary / progress / quests / knowledge / character），
首次查看自动生成快照，历史周报可回看。
"""
import json
import os
from datetime import date, timedelta

from trader_growing.journal_bridge import load_all
from trader_growing.levels import LEVELS, WORLDS, Progress
from trader_growing.quests import QuestSystem, WEEKLY_QUESTS
from trader_growing.knowledge import KnowledgeSystem
from trader_growing.bestiary import Bestiary
from trader_growing.achievements import AchievementSystem
from trader_growing.character import Character

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "weekly_reports")


def current_week():
    iso = date.today().isocalendar()
    return "{}-W{:02d}".format(iso[0], iso[1])


def week_range():
    """本周 [周一, 周日] 日期列表"""
    iso = date.today().isocalendar()
    monday = date.fromisocalendar(iso[0], iso[1], 1)
    return [monday + timedelta(days=i) for i in range(7)]


class WeeklyReport:
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)

    # ------------------------------------------------------------ 数据采集
    def build(self, char=None):
        char = char or Character()
        prog = Progress()
        qs = QuestSystem()
        ks = KnowledgeSystem()
        best = Bestiary()
        ach = AchievementSystem()
        week = current_week()
        wk_days = set(str(d) for d in week_range())

        # 打卡
        diary_dates = set(r.date for r in load_all() if hasattr(r, "date") and r.date)
        checkin_days = sorted(d for d in diary_dates if d in wk_days)

        # 首通关卡（本周）
        new_levels = [(lid, d["at"]) for lid, d in prog.details.items()
                      if d.get("at") in wk_days]
        new_levels.sort(key=lambda x: x[1])

        # 复习（本周）
        reviews = sum(1 for v in prog.reviews.values() if v in wk_days)

        # BOSS 复战（本周）
        boss_revives = sum(1 for v in prog.boss_revives.values() if v == week)

        # 周任务（本周）
        week_prefix = "{}W{}:".format(date.today().isocalendar()[0], date.today().isocalendar()[1])
        week_quests = [k.split(":")[-1] for k in qs.week_done if k.startswith(week_prefix)]

        # 速通（全部通关用时，天）
        speedrun_days = None
        if len(prog.completed) == len(LEVELS):
            ats = sorted(d.get("at") for d in prog.details.values() if d.get("at"))
            if len(ats) >= 2:
                speedrun_days = (date.fromisoformat(ats[-1]) - date.fromisoformat(ats[0])).days + 1

        s = char.summary()
        report = {
            "week": week,
            "generated_at": str(date.today()),
            "checkin_days": checkin_days,
            "new_levels": [{"lid": lid, "name": LEVELS[lid]["name"]} for lid, _ in new_levels],
            "reviews": reviews,
            "boss_revives": boss_revives,
            "week_quests": week_quests,
            "knowledge": {"correct": ks.correct, "total": ks.total},
            "bestiary": len(best.unlocked),
            "badges": len(ach.summary()),
            "dims": s["dims"],
            "xp": s["xp"],
            "level": s["level"],
            "total_levels": len(prog.completed),
            "total_worlds": prog.worlds_cleared(),
            "speedrun_days": speedrun_days,
        }
        return report

    # ------------------------------------------------------------ 建议
    def suggestions(self, r):
        tips = []
        if not r["checkin_days"]:
            tips.append("本周还没有打卡——修行从今天的 5 分钟开始。")
        elif len(r["checkin_days"]) < 5:
            tips.append("本周打卡 {} 天——目标是一周 ≥5 天，每天 5 分钟就够了。".format(len(r["checkin_days"])))
        if not r["new_levels"]:
            tips.append("本周没有首通新关卡——去 🎮 学习关卡推一关（约 15 分钟）。")
        if r["total_levels"] > 0 and r["boss_revives"] == 0:
            tips.append("BOSS 复战还没打——每周一次 +30 XP，行情每周都在变。")
        if r["knowledge"]["total"] > 0:
            pct = r["knowledge"]["correct"] / r["knowledge"]["total"]
            if pct < 0.6:
                tips.append("知识测试正确率 {:.0%}——去「错题本」把错题过一遍。".format(pct))
        if r["speedrun_days"] is not None:
            tips.append("🏆 你已通关全部 36 关（用时约 {} 天）——恭喜「世界征服者」！".format(r["speedrun_days"]))
        if not tips:
            tips.append("本周节奏全勤——浇水、闯关、复战都完成了，继续保持！")
        return tips

    # ------------------------------------------------------------ 存取
    def save_current(self, report=None):
        report = report or self.build()
        path = os.path.join(self.data_dir, report["week"] + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return path

    def history(self):
        """历史周报列表（最新在前）"""
        import glob
        files = sorted(glob.glob(os.path.join(self.data_dir, "*.json")), reverse=True)
        out = []
        for fp in files:
            try:
                with open(fp, encoding="utf-8") as f:
                    out.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue
        return out

    def load_week(self, week):
        path = os.path.join(self.data_dir, week + ".json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return None


def print_weekly():
    """CLI 输出"""
    wr = WeeklyReport()
    r = wr.build()
    print()
    print("  📅 修行周报 · {}（{}）".format(r["week"], r["generated_at"]))
    print("  " + "=" * 60)
    print("  打卡 {} 天 | 首通 {} 关 | 复习 {} 次 | BOSS 复战 {} 次".format(
        len(r["checkin_days"]), len(r["new_levels"]), r["reviews"], r["boss_revives"]))
    print("  周任务 {}/{} | 知识分 {}/{} | 图鉴 {} 条 | 徽章 {} 枚".format(
        len(r["week_quests"]), len(WEEKLY_QUESTS),
        r["knowledge"]["correct"], r["knowledge"]["total"], r["bestiary"], r["badges"]))
    print("  当前: Lv{} | XP {} | 关卡 {}/{} | 世界 {}/9".format(
        r["level"], r["xp"], r["total_levels"], 36, r["total_worlds"]))
    if r["new_levels"]:
        print("  本周新通关: " + ", ".join("「{}」".format(n["name"]) for n in r["new_levels"]))
    print("  " + "-" * 60)
    print("  💡 下周建议:")
    for t in wr.suggestions(r):
        print("    - " + t)
    print("  " + "=" * 60)
    return r


if __name__ == "__main__":
    print_weekly()
