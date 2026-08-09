# -*- coding: utf-8 -*-
"""图鉴系统：把《人人都是量化交易员》的知识点变成可收集的图鉴

解锁机制（进度感）：
  - 打卡天数分档解锁大部分条目
  - 特殊行为解锁特殊条目（看板 / 对账 / 因子实验）
"""
import json, os

# (id, 名称, 一句话, 类别, 解锁档位)
ENTRIES = [
    ("backtest",     "回测",       "用历史数据模拟策略执行，在脑海中重播历史", "基础", 0),
    ("benchmark",    "基准",       "跟谁比？没有参照物的收益没有意义", "基础", 0),
    ("ma",           "均线",       "过去 N 天价格的平均值，像连续几天的平均体温", "基础", 0),
    ("stop_loss",    "止损",       "预设底线：跌了 X% 自动卖出，先保命再谈收益", "风控", 0),
    ("take_profit",  "止盈",       "落袋为安？多数时候是在亲手切断赚钱的持仓", "风控", 0),
    ("overfit",      "过拟合",     "把历史噪音当成规律，背答案不等于真会做", "陷阱", 7),
    ("oos",          "样本外",     "闭卷考：在没见过的数据上重新考一次", "验证", 7),
    ("sharpe",       "夏普比率",   "每承受一份颠簸，能赚多少收益", "指标", 7),
    ("calmar",       "卡玛比",     "每承受 1% 最大回撤，能换多少年化收益", "指标", 7),
    ("sortino",      "索提诺比",   "只关心亏损方向的波动，上涨的颠簸不是风险", "指标", 7),
    ("whipsaw",      "锯齿效应",   "持续下跌里反复卖出买回，每轮都交手续费", "陷阱", 21),
    ("risk_parity",  "风险平价",   "波动大的少买，波动小的多买，让影响力均匀", "配置", 21),
    ("momentum",     "动量",       "涨得好的多买，跌的不买——趋势交易的量化表达", "配置", 21),
    ("param_sens",   "参数敏感性", "好策略不怕参数变：选高原，不选尖峰", "验证", 21),
    ("walkforward",  "Walk-forward", "边走边调：模拟定期重新优化参数", "验证", 21),
    ("cv",           "交叉验证",   "多种切法验证同一个结论，共识强才可信", "验证", 60),
    ("rule_burden",  "规则负担",   "旋钮越多越容易凑出好看回测，少即是多", "陷阱", 60),
    ("slippage",     "滑点",       "下单到成交之间价格漂移，菜市场问价 5 块变 5.1", "执行", 60),
    ("impl_short",   "执行落差",   "回测收益不等于真实交易收益", "执行", 60),
    ("factor",       "因子",       "把投资直觉翻译成可计算变量", "研究", 60),
    ("ic",           "信息系数",   "因子排名和收益排名有多像？", "研究", 60),
    ("regime",       "市场状态",   "市场像天气：高波动是台风天，策略要会看天气", "研究", 60),
    ("vol_filter",   "波动率过滤", "高波动时减仓，躲过暴跌也躲过暴涨", "风控", 60),
    ("reconcile",    "纪律对账",   "计划 vs 实际：把说好的止损和实际砍的价对一对", "修行", 100),
]


class Bestiary:
    def __init__(self, data_path=None):
        self.data_path = data_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "data", "bestiary.json")
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

    def check(self, total_days, extra=None):
        """total_days: 打卡天数; extra: 特殊行为标记集合，如 {'dashboard','reconcile','quest_factor'}"""
        extra = extra or set()
        newly = []
        for eid, name, desc, cat, tier in ENTRIES:
            if eid in self.unlocked:
                continue
            ok = total_days >= tier
            if eid == "reconcile":
                ok = "reconcile" in extra
            if ok:
                self.unlocked.append(eid)
                newly.append((eid, name, desc, cat))
        if newly:
            self.save()
        return newly

    def summary(self, total_days=None):
        if total_days is not None:
            self.check(total_days)
        done = [e for e in ENTRIES if e[0] in self.unlocked]
        todo = [e for e in ENTRIES if e[0] not in self.unlocked]
        return done, todo
