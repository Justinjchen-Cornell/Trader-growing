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
    # ---- 学习关卡成就（state 由关卡系统补充：levels_done / worlds_cleared / quiz_correct_total）
    {"id": "first_level",  "name": "初出茅庐",   "desc": "通关第一个学习关卡",
     "check": lambda s: s.get("levels_done", 0) >= 1},
    {"id": "world1_clear", "name": "新手村毕业", "desc": "通关第 1 章世界「新手村」全部关卡",
     "check": lambda s: s.get("worlds_cleared", 0) >= 1},
    {"id": "world2_clear", "name": "选品大师",   "desc": "通关第 2 章世界「选什么」全部关卡",
     "check": lambda s: s.get("worlds_cleared", 0) >= 2},
    {"id": "levels_5",     "name": "章节行者",   "desc": "累计通关 5 个关卡",
     "check": lambda s: s.get("levels_done", 0) >= 5},
    {"id": "quiz_ace",     "name": "闯关学霸",   "desc": "关卡测验累计答对 30 题",
     "check": lambda s: s.get("quiz_correct_total", 0) >= 30},
    {"id": "all_worlds",   "name": "世界征服者", "desc": "通关全部 9 个世界（36 关）",
     "check": lambda s: s.get("worlds_cleared", 0) >= 9},
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
