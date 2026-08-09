# -*- coding: utf-8 -*-
"""真钱分级解锁：不是'能不能赚钱'，而是'纪律配不配拿真钱'

L0 旁观者   观察信号，不交易          (解锁: 完成 7 天打卡)
L1 模拟者   模拟盘 + 每日对账          (解锁: 打卡>=21 天 且 纪律分均值 >= 70)
L2 小实盘   每资产小资金              (解锁: 打卡>=60 天 且 纪律 >= 80 且 连续30天零红牌)
L3 组合者   四资产组合                (解锁: L2 保持 60 天无重大偏差)
"""
import json, os
from datetime import date

TIERS = [
    {"id": "L0", "name": "旁观者", "desc": "观察信号，不交易", "min_days": 0},
    {"id": "L1", "name": "模拟者", "desc": "模拟盘 + 每日对账", "min_days": 7,
     "min_discipline": 0.0},
    {"id": "L2", "name": "小实盘", "desc": "每资产小资金（建议 1 万起）", "min_days": 21,
     "min_discipline": 70.0, "clean_days": 0},
    {"id": "L3", "name": "组合者", "desc": "四资产风险平价 + 波动率过滤", "min_days": 60,
     "min_discipline": 80.0, "clean_days": 30, "sustain_days": 60},
]


class TierSystem:
    def __init__(self, data_path=None):
        self.data_path = data_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "data", "tier.json")
        self.clean_days = 0        # 连续零红牌天数
        self.clean_streak_l2 = 0   # L2 后连续无重大偏差天数
        self.load()

    def load(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, encoding="utf-8") as f:
                d = json.load(f)
            self.clean_days = d.get("clean_days", 0)
            self.clean_streak_l2 = d.get("clean_streak_l2", 0)

    def save(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump({"clean_days": self.clean_days, "clean_streak_l2": self.clean_streak_l2},
                      f, ensure_ascii=False, indent=2)

    def record_day(self, has_red_flag, in_l2=False):
        """每日对账后调用：has_red_flag=今日是否有红牌"""
        if has_red_flag:
            self.clean_days = 0
            self.clean_streak_l2 = 0
        else:
            self.clean_days += 1
            if in_l2:
                self.clean_streak_l2 += 1
        self.save()

    def current_tier(self, total_days, avg_discipline):
        """返回当前解锁的最高层级"""
        tier = TIERS[0]
        for t in TIERS[1:]:
            if total_days < t["min_days"]:
                break
            if avg_discipline < t.get("min_discipline", 0):
                break
            if t.get("clean_days") and self.clean_days < t["clean_days"]:
                break
            if t.get("sustain_days") and self.clean_streak_l2 < t["sustain_days"]:
                break
            tier = t
        return tier

    def next_requirements(self, total_days, avg_discipline):
        """返回下一个未解锁层级的条件"""
        for t in TIERS[1:]:
            if self.current_tier(total_days, avg_discipline)["id"] == t["id"]:
                continue
            missing = []
            if total_days < t["min_days"]:
                missing.append("打卡还需 {} 天".format(t["min_days"] - total_days))
            if avg_discipline < t.get("min_discipline", 0):
                missing.append("纪律分还需 {:.0f} 分".format(t["min_discipline"] - avg_discipline))
            if t.get("clean_days") and self.clean_days < t["clean_days"]:
                missing.append("连续零红牌还需 {} 天".format(t["clean_days"] - self.clean_days))
            if t.get("sustain_days") and self.clean_streak_l2 < t["sustain_days"]:
                missing.append("L2 保持还需 {} 天".format(t["sustain_days"] - self.clean_streak_l2))
            return {"tier": t, "missing": missing}
        return None
