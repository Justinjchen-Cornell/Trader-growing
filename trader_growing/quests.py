# -*- coding: utf-8 -*-
"""任务系统：每日任务（自动检查）+ 每周任务（手动完成，奖励 XP）

每周任务模板 = 第 9 章因子研究流程：
  提假设 -> 算 IC -> 分组分析 -> 记录结论
"""
import json, os
from datetime import date

DAILY_QUESTS = [
    {"id": "water",    "name": "浇水",     "desc": "完成每日打卡（四维打分）"},
    {"id": "weather",  "name": "看天气",   "desc": "运行四资产看板（tg.py dashboard）"},
    {"id": "reconcile","name": "对账",     "desc": "运行纪律对账（tg.py reconcile）"},
]

WEEKLY_QUESTS = [
    {"id": "factor",    "name": "因子实验", "desc": "提假设->算IC->分组分析->记录结论", "xp": 30},
    {"id": "param",     "name": "参数研究", "desc": "扫一个参数，判断高原型还是山峰型", "xp": 30},
    {"id": "backtest",  "name": "回测复现", "desc": "复现一个书里/论文里的策略回测", "xp": 30},
]


class QuestSystem:
    def __init__(self, data_path=None):
        self.data_path = data_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "data", "quests.json")
        self.done = []      # ["2026-08-09:water", ...]
        self.week_done = []  # ["2026W32:factor", ...]
        self.load()

    def load(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, encoding="utf-8") as f:
                d = json.load(f)
            self.done = d.get("done", [])
            self.week_done = d.get("week_done", [])

    def save(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump({"done": self.done, "week_done": self.week_done},
                      f, ensure_ascii=False, indent=2)

    def complete_daily(self, qid):
        key = "{}:{}".format(date.today(), qid)
        if key not in self.done:
            self.done.append(key)
            self.save()
            return True
        return False

    def daily_done_today(self):
        today = str(date.today())
        return [q["id"] for q in DAILY_QUESTS if "{}:{}".format(today, q["id"]) in self.done]

    def complete_weekly(self, qid, char=None):
        """完成每周任务，返回 XP 奖励（若未完成过）"""
        week = date.today().isocalendar()[:2]
        key = "{}W{}:{}".format(week[0], week[1], qid)
        if key in self.week_done:
            return 0
        self.week_done.append(key)
        self.save()
        q = next((x for x in WEEKLY_QUESTS if x["id"] == qid), None)
        if q and char:
            char.xp += q["xp"]
            char.save()
        return q["xp"] if q else 0
