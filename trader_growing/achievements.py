# -*- coding: utf-8 -*-
"""成就徽章系统"""
import json, os

ACHIEVEMENTS = [
    {"id": "first_seed",   "name": "第一颗种子", "desc": "完成第一次每日打卡",
     "check": lambda s: s["total_days"] >= 1},
    {"id": "streak7",      "name": "一周新芽",   "desc": "连续打卡 7 天",
     "check": lambda s: s["streak"] >= 7},
    {"id": "streak30",     "name": "月之常青",   "desc": "连续打卡 30 天",
     "check": lambda s: s["streak"] >= 30},
    {"id": "no_impulse",   "name": "零冲动",     "desc": "连续 14 天无冲动交易",
     "check": lambda s: s.get("no_impulse_days", 0) >= 14},
    {"id": "four_bloom",   "name": "四维开花",   "desc": "四维属性同时 >= 70",
     "check": lambda s: all(v >= 70 for v in s["dims"].values())},
    {"id": "cut_loss",     "name": "割肉勇士",   "desc": "严格执行止损 10 次",
     "check": lambda s: s.get("stop_loss_executed", 0) >= 10},
    {"id": "empty_ok",     "name": "空仓大师",   "desc": "遵守空仓哲学 30 天",
     "check": lambda s: s.get("empty_days", 0) >= 30},
]


class AchievementSystem:
    def __init__(self, data_path=None):
        self.data_path = data_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "data", "achievements.json")
        self.unlocked = []
        self.load()

    def load(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, encoding="utf-8") as f:
                self.unlocked = json.load(f)

    def save(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.unlocked, f, ensure_ascii=False, indent=2)

    def check_all(self, state):
        new = []
        for a in ACHIEVEMENTS:
            if a["id"] not in self.unlocked and a["check"](state):
                self.unlocked.append(a["id"])
                new.append(a)
        if new:
            self.save()
        return new

    def summary(self):
        return [a for a in ACHIEVEMENTS if a["id"] in self.unlocked]
