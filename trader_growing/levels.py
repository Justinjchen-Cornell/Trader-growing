# -*- coding: utf-8 -*-
"""学习关卡系统：把《人人都是量化交易员》的实验变成每日升级的关卡

结构：9 个世界（章）× 关卡（每章 4-6 关），每关 = 知识卡 + 实战任务 + 测验
实战任务用「今天的真实市场数据」自动取材判分——每天答案都不同。

当前 MVP：第 1 章「新手村」4 关（模板可扩展）
"""
import json
import os
from datetime import date

WORLDS = {
    1: {"name": "新手村", "title": "跑通第一个策略",
        "boss_desc": "过拟合挑战：参数扫描冠军在样本外现原形"},
    2: {"name": "选什么", "title": "先选买什么（从 3 只 ETF 开始）", "boss_desc": "构建你的标的池"},
    3: {"name": "分多少", "title": "决定各买多少", "boss_desc": "三种分法实测"},
    4: {"name": "何时动", "title": "决定何时买卖", "boss_desc": "再平衡/止损/止盈"},
    5: {"name": "体检台", "title": "判断策略好不好", "boss_desc": "4 个关键视角"},
    6: {"name": "陷阱迷宫", "title": "防止过拟合", "boss_desc": "四个检查工具"},
    7: {"name": "现实世界", "title": "执行交易", "boss_desc": "从回测到实盘"},
    8: {"name": "守护者", "title": "监控诊断迭代", "boss_desc": "三步 SOP"},
    9: {"name": "研究者", "title": "因子研究入门", "boss_desc": "IC 评估与改进"},
}

LEVELS = {
    "1-1": {
        "chapter": 1, "name": "定投播种", "dim": "math", "xp": 15, "figure": "backtest",
        "knowledge": (
            "定投（定期定额）= 每月固定金额买入，不看涨跌机械执行。\n"
            "核心机制：价格低时同样 1000 元买到更多份额，价格高时买得更少——"
            "像菜市场菜贵少买、菜便宜多买，分散了买入时点，避开一次性买在最高点的风险。\n"
            "量化定义：规则明确（每月第一个交易日买固定金额）+ 执行可重复。"),
        "task": {
            "type": "calc_shares",
            "text": "🧪 实战任务：今天是 {date}，沪深300ETF 收盘价 {price} 元。"
                    "如果今天定投 1000 元，能买多少份？（保留整数，四舍五入）",
            "hint": "份数 = 金额 ÷ 价格（保留整数）",
        },
        "quiz": [
            {"q": "定投的核心特点是？",
             "opts": ["追涨杀跌", "分散买入时点、摊低成本", "一次性全仓", "只买最贵的"],
             "ans": 1, "exp": "价格低多买、价格高少买，避开单点买入风险。"},
            {"q": "回测（Backtest）是什么？",
             "opts": ["预测未来", "用历史数据模拟策略执行", "实盘下单", "数据清洗"],
             "ans": 1, "exp": "回测=在历史数据上'重播'策略。"},
            {"q": "一个收益率数字本身能说明策略好坏吗？",
             "opts": ["能，越高越好", "不能，需要和基准（参照物）对比", "看心情", "数字大就对"],
             "ans": 1, "exp": "没有参照物的收益没有意义——80 分要对比全班平均分。"},
        ],
    },
    "1-2": {
        "chapter": 1, "name": "基准对决", "dim": "math", "xp": 15, "figure": "benchmark",
        "knowledge": (
            "基准（Benchmark）= 用来比较的参照物，最自然的基准是'买入持有'（什么都不做）。\n"
            "判断策略好不好：先和'什么都不做'比。忙活半天跑不赢买入持有，策略就没有意义。\n"
            "注意：定投赢基准≠策略优秀——可能只是恰好躲过了一段下跌，还需要更多检验。"),
        "task": {
            "type": "vs_benchmark",
            "text": "🧪 实战任务：看今天的四资产看板。判断沪深300ETF 今天收盘价相比一年前（{ref}）"
                    "是涨了还是跌了？（输入 +1 表示涨，-1 表示跌，0 表示差不多）",
            "hint": "对比今天收盘价和一年前同期收盘价",
        },
        "quiz": [
            {"q": "为什么策略要和'买入持有'对比？",
             "opts": ["显得专业", "因为'什么都不做'是最简单的可行方案", "书里要求的", "没有原因"],
             "ans": 1, "exp": "连'什么都不做'都赢不了，策略就失去了存在的意义。"},
            {"q": "相对基准收益差是什么？",
             "opts": ["策略收益", "策略收益 - 基准收益", "基准收益", "最大回撤"],
             "ans": 1, "exp": "比及格线高多少或低多少，才是策略的真实贡献。"},
            {"q": "定投跑赢买入持有就一定说明策略好吗？",
             "opts": ["一定", "不一定，可能只是恰好躲过下跌", "绝对不好", "无法判断"],
             "ans": 1, "exp": "一段数据上的跑赢可能是巧合，需要更多检验（第 5/6 章）。"},
        ],
    },
    "1-3": {
        "chapter": 1, "name": "均线信号", "dim": "math", "xp": 15, "figure": "ma",
        "knowledge": (
            "均线（Moving Average）= 过去 N 天收盘价的平均值，抹平每日噪音留下趋势方向。\n"
            "MA20 = 20 天平均；收盘价在 MA20 上方 = 短期强于近月平均（多头），下方 = 空头。\n"
            "注意：均线是滞后指标，看的是过去不预测未来；窗口越短越灵敏也越容易被骗。"),
        "task": {
            "type": "ma_direction",
            "text": "🧪 实战任务：看今天的四资产看板。沪深300ETF 今天收盘价在 MA20 上方还是下方？"
                    "（输入 1 表示上方/多头，-1 表示下方/空头）",
            "hint": "看板'趋势'列直接告诉你",
        },
        "quiz": [
            {"q": "MA20 表示什么？",
             "opts": ["20 天开盘价总和", "过去 20 天收盘价平均值", "20 天最高价", "20 天成交量"],
             "ans": 1, "exp": "MA20 = 过去 20 天收盘价的平均。"},
            {"q": "为什么均线是'滞后指标'？",
             "opts": ["它预测未来", "它基于过去数据，涨跌确认后才反应", "它总是错的", "它太快了"],
             "ans": 1, "exp": "像'这周天气都不错'不代表明天一定晴天。"},
            {"q": "均线窗口越短，信号的特点是？",
             "opts": ["越稳定", "越灵敏也越容易被骗（假信号多）", "没区别", "越迟钝"],
             "ans": 1, "exp": "MA10 灵敏但假信号多，MA60 稳定但迟钝。"},
        ],
    },
    "1-BOSS": {
        "chapter": 1, "name": "过拟合挑战", "dim": "philosophy", "xp": 30, "figure": "overfit", "boss": True,
        "knowledge": (
            "过拟合（Overfitting）= 策略在历史数据上'背答案'，把噪音当规律。\n"
            "经典现场：参数扫描选出的'冠军'在训练集上很漂亮，换到样本外（没见过的数据）就现原形。\n"
            "铁律：历史数据上的'最优'不等于未来的'可用'——看到漂亮回测先问'是规律还是巧合？'"),
        "task": {
            "type": "overfit_choice",
            "text": "🧪 实战任务：假设你扫描了 24 个均线参数，MA30 在历史回测中收益最高（+25%）。"
                    "但用它跑 2024-2025 年没见过的数据，收益只有 +2%，而简单定投 +8%。"
                    "这说明什么？（输入 1=策略很优秀，2=这是过拟合，3=数据错了，4=运气好继续用）",
            "hint": "回忆第 1 章实验 7 的结论",
        },
        "quiz": [
            {"q": "过拟合是指？",
             "opts": ["代码写错", "参数历史表现好但样本外大幅衰减", "数据缺失", "交易太频繁"],
             "ans": 1, "exp": "背答案≠真会做，换考卷就露馅。"},
            {"q": "样本外测试（Out-of-Sample）是什么？",
             "opts": ["用全部数据", "用参数从没见过的数据验证", "只测一年", "随机抽样"],
             "ans": 1, "exp": "闭卷考：训练集选出的最优参数去新数据重新考。"},
            {"q": "如果 24 个参数里总有一个历史表现最好，这说明？",
             "opts": ["你找到了圣杯", "统计必然——射 24 支箭总有一支靠近靶心", "策略失效", "数据有问题"],
             "ans": 1, "exp": "选得越多，'碰巧最好'的假象越强——选择偏差。"},
        ],
    },
}


class Progress:
    """关卡进度：完成记录 + 世界通关状态"""

    def __init__(self, data_path=None):
        self.data_path = data_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "data", "progress.json")
        self.completed = []   # ["1-1", ...]
        self.load()

    def load(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, encoding="utf-8") as f:
                self.completed = json.load(f).get("completed", [])

    def save(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump({"completed": self.completed}, f, ensure_ascii=False, indent=2)

    def done(self, lid):
        return lid in self.completed

    def complete(self, lid):
        if lid not in self.completed:
            self.completed.append(lid)
            self.save()
            return True
        return False

    def next_level(self):
        """返回下一个未完成的关卡（按世界顺序）"""
        for ch in sorted(WORLDS):
            for lid in LEVELS:
                if int(lid.split("-")[0]) == ch and not self.done(lid):
                    return LEVELS[lid]
        return None

    def world_progress(self, chapter):
        ids = [l for l in LEVELS if int(l.split("-")[0]) == chapter]
        return sum(1 for l in ids if self.done(l)), len(ids)
