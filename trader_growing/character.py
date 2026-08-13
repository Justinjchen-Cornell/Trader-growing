# -*- coding: utf-8 -*-
"""角色系统：等级 / 经验值 / 连击 / 四维属性"""
import json, os

LEVELS = [
    (0,    "菜鸟",  "刚埋下种子"),
    (100,  "学徒",  "种子发芽"),
    (300,  "熟练",  "小树初成"),
    (600,  "专家",  "枝繁叶茂"),
    (1000, "大师",  "花果满园"),
]
DIMS = ["math", "finance", "psychology", "philosophy"]
DIM_NAMES = {"math": "数学", "finance": "金融", "psychology": "心理", "philosophy": "哲学"}


class Character:
    def __init__(self, data_path=None):
        self.data_path = data_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "data", "character.json")
        self.xp = 0
        self.streak = 0
        self.last_date = None
        self.first_checkin = None
        self.dims = {d: 0.0 for d in DIMS}
        self.total_days = 0
        self.load()

    def load(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, encoding="utf-8") as f:
                d = json.load(f)
            self.xp = d.get("xp", 0)
            self.streak = d.get("streak", 0)
            self.last_date = d.get("last_date")
            self.first_checkin = d.get("first_checkin")
            self.dims = {**self.dims, **d.get("dims", {})}
            self.total_days = d.get("total_days", 0)

    def save(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump({"xp": self.xp, "streak": self.streak, "last_date": self.last_date,
                       "first_checkin": self.first_checkin,
                       "dims": self.dims, "total_days": self.total_days},
                      f, ensure_ascii=False, indent=2)

    def is_newbie(self):
        """新手上路期：首次打卡起 7 天内 XP 双倍"""
        if not self.first_checkin:
            return False
        try:
            from datetime import date as _d
            days = (_d.today() - _d.fromisoformat(self.first_checkin)).days
            return 0 <= days <= 7
        except ValueError:
            return False

    def gain_xp(self, n, save=True):
        """加 XP（新手上路期双倍），返回实际获得值"""
        n = int(n)
        if self.is_newbie():
            n = n * 2
        self.xp += n
        if save:
            self.save()
        return n

    @property
    def level(self):
        for threshold, name, desc in LEVELS:
            if self.xp >= threshold:
                cur = (threshold, name, desc)
        return cur

    @property
    def next_level_xp(self):
        for threshold, _, _ in LEVELS:
            if self.xp < threshold:
                return threshold
        return None

    def daily_checkin(self, dims, has_discipline_issue=False, checkin_date=None):
        """dims: {math: 0-100, ...}; has_discipline_issue: 今日对账有红牌"""
        from datetime import date as _date
        today = str(checkin_date or _date.today())
        if self.last_date == today:
            return 0
        if self.last_date and (_date.fromisoformat(today) - _date.fromisoformat(self.last_date)).days == 1:
            self.streak += 1
        else:
            self.streak = 1
        base = 10
        if self.streak >= 3:
            base = int(base * 1.5)
        gain = base
        if has_discipline_issue:
            gain = max(1, gain // 2)
        if self.first_checkin is None:
            self.first_checkin = today
        if self.is_newbie():
            gain = gain * 2
        self.xp += gain
        self.total_days += 1
        self.last_date = today
        for d in DIMS:
            if d in dims:
                self.dims[d] = round(self.dims[d] * 0.8 + dims[d] * 0.2, 1)
        self.save()
        return gain

    def summary(self):
        name, desc = self.level[1], self.level[2]
        return {"level": name, "level_desc": desc, "xp": self.xp,
                "next_level_xp": self.next_level_xp, "streak": self.streak,
                "total_days": self.total_days,
                "dims": dict(self.dims)}
