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
    "2-1": {
        "chapter": 2, "name": "个股 vs ETF", "dim": "finance", "xp": 15, "figure": "etf",
        "knowledge": (
            "个股 = 单只公司的股票；ETF = 一篮子股票的基金（如沪深300ETF 一次买入 300 家公司）。\n"
            "为什么初学者先选 ETF：① 分散单一公司风险——茅台也可能业绩暴雷、跌停甚至退市；"
            "② 信号质量更稳，不会被单只公司事件带偏；③ 成本低、门槛低、无选股踩雷烦恼。\n"
            "量化视角：个股的波动率通常显著大于 ETF——波动大 = 信号噪音大。"),
        "task": {
            "type": "vol_compare",
            "text": "🧪 实战任务：个股波动通常大于 ETF。对比贵州茅台（600519）vs 沪深300ETF（510300）"
                    "最近一个完整年度（{start} ~ {end}）的年化波动率，谁的波动更大？"
                    "（输入 1=茅台大，-1=ETF大，0=差不多）",
            "hint": "年化波动率 = 日收益标准差 × √252；用两者都有数据的年份（2025 年）",
        },
        "quiz": [
            {"q": "为什么初学者先选 ETF 而不是个股？",
             "opts": ["个股可能暴雷，ETF 分散单一公司风险", "ETF 一定涨", "个股更专业", "没有区别"],
             "ans": 0, "exp": "ETF 一篮子持仓分散暴雷风险，信号质量更稳。"},
            {"q": "ETF 是什么？",
             "opts": ["一只股票", "一篮子股票的基金，可像股票一样交易", "期货合约", "银行存款"],
             "ans": 1, "exp": "ETF = Exchange Traded Fund，场内交易的基金。"},
            {"q": "个股和 ETF 的信号质量谁更稳？",
             "opts": ["个股更稳，因为研究更深入", "ETF 更稳，不被单只公司事件带偏", "一样", "取决于运气"],
             "ans": 1, "exp": "单只公司一个财报/舆情就能砸出大波动，ETF 把噪音平均掉了。"},
        ],
    },
    "2-2": {
        "chapter": 2, "name": "中美锚定", "dim": "finance", "xp": 15, "figure": "gdp",
        "knowledge": (
            "中美经济周期不同步：美国市场长牛慢牛（纳指），中国 A 股波动大、牛短熊长（沪深300）。\n"
            "注意陷阱：中国 GDP 增速比美国高，但 GDP 增速 ≠ 股市收益——股市是'预期差'的游戏，"
            "预期被 price-in 之后，增速再高也不一定涨。\n"
            "配置中美两类资产 = 分散'国家风险'：A 股低迷时美股可能走强，反之亦然。"),
        "task": {
            "type": "ret_compare",
            "text": "🧪 实战任务：中美经济周期不同步。对比纳指100ETF（513100）vs 沪深300ETF（510300）"
                    "最近一年（{window} 个交易日）的涨幅，谁涨得更多？"
                    "（输入 1=纳指100，-1=沪深300，0=差不多）",
            "hint": "区间收益 = 期末价 ÷ 期初价 - 1",
        },
        "quiz": [
            {"q": "为什么要配置中美两类资产？",
             "opts": ["经济周期不同步，分散国家风险", "听起来专业", "越多越好", "没有原因"],
             "ans": 0, "exp": "A股低迷时美股可能走强——两类资产给组合'两条命'。"},
            {"q": "中国 GDP 增速高于美国，A 股收益就一定更高？",
             "opts": ["一定，经济好股市就好", "不一定，GDP增速≠股市收益", "反了，GDP越高跌越多", "无法验证"],
             "ans": 1, "exp": "股市交易的是预期差：好消息提前被 price-in 后，增速再高也难涨。"},
            {"q": "纳指100 主要跟踪哪个市场的资产？",
             "opts": ["A股大盘", "港股", "美股科技龙头", "黄金"],
             "ans": 2, "exp": "纳指100 = 美股纳斯达克100家龙头，代表美国成长股。"},
        ],
    },
    "2-3": {
        "chapter": 2, "name": "相关性探秘", "dim": "finance", "xp": 15, "figure": "correlation",
        "knowledge": (
            "相关性（Correlation）：两只资产涨跌的同步程度，范围 -1（完全反向）到 +1（完全同步）。\n"
            "第 2 章核心认知：分散风险的关键不是'多买几个'，而是'买涨跌不同步的资产'——"
            "买 5 只相关性 +0.9 的 ETF，分散效果约等于买 1 只。\n"
            "黄金 vs 股票：不是永远负相关——股市暴跌时黄金常因避险走强（负相关），"
            "但普涨行情里两者也可能同步上涨（正相关）。关键不是'负相关'，"
            "而是相关性**明显低于同类资产**。答案每天不同，看今天的真实数据说话。"),
        "task": {
            "type": "corr_sign",
            "text": "🧪 实战任务：分散风险的关键是买涨跌不同步的资产。计算黄金ETF（518880）vs "
                    "沪深300ETF（510300）最近一年（{window} 个交易日）日收益的相关性，"
                    "是正相关还是负相关？（输入 1=正相关，-1=负相关，0=接近零相关）",
            "hint": "相关性 = 两只资产日收益序列的相关系数（Pearson）",
        },
        "quiz": [
            {"q": "两只资产相关性 +0.9 意味着什么？",
             "opts": ["涨跌高度同步，分散效果差", "涨跌相反，对冲完美", "与分散无关", "必然同涨同跌到分毫不差"],
             "ans": 0, "exp": "+0.9 ≈ 同一只资产的'影子'，买两只和买一只几乎没区别。"},
            {"q": "分散风险的关键是什么？",
             "opts": ["买的数量多", "买涨跌不同步的资产", "买最便宜的", "全仓一只最强的"],
             "ans": 1, "exp": "组合收益靠涨得好的资产，风险降低靠'不同步'的资产。"},
            {"q": "黄金与股票通常是什么关系？",
             "opts": ["完全同步", "黄金跟着股票涨", "低相关甚至负相关（避险属性）", "正相关 0.9 以上"],
             "ans": 2, "exp": "股市暴跌时资金常涌入黄金避险——但普涨行情也会正相关，实测数据为准。"},
        ],
    },
    "2-BOSS": {
        "chapter": 2, "name": "标的池挑战", "dim": "philosophy", "xp": 30, "figure": "diversify", "boss": True,
        "knowledge": (
            "标的池 = 你长期观察/配置的资产名单。构建原则不是'越多越好'，而是'相关性越低越好'。\n"
            "书中最终标的池：沪深300ETF（A股）+ 纳指100ETF（美股）+ 黄金ETF（避险）——"
            "三只资产相关性低，覆盖中美两大市场 + 一个避险选项。\n"
            "进阶认知：相关性最低 ≠ 一定要选它——相关性矩阵是第一层筛选（谁和谁不同步），"
            "资产'质地'是第二层（原油长期收益差、波动剧烈、不适合配置；黄金有避险价值）。\n"
            "选池流程：先定主资产 → 算相关性 → 踢掉'高同步'候选 → 再从低相关候选中挑质地好的。"),
        "task": {
            "type": "min_corr",
            "text": "🧪 实战任务：BOSS 战！现在轮到你构建标的池——以沪深300ETF（510300）为主资产，"
                    "候选：纳指100ETF(1)、黄金ETF(2)、原油ETF(3)。用最近一年（{window} 个交易日）"
                    "日收益算相关性，哪只与沪深300 的相关性**最低**？（输入 1 / 2 / 3）",
            "hint": "相关性最低 = 最'涨跌不同步' = 放进组合分散效果最好",
        },
        "quiz": [
            {"q": "书中最终标的池是哪三只？",
             "opts": ["沪深300ETF + 纳指100ETF + 黄金ETF", "三只银行股", "只买黄金", "五只同行业ETF"],
             "ans": 0, "exp": "中美两个市场 + 避险资产，相关性低、覆盖广。"},
            {"q": "组合里两只相关性 0.95 的资产，分散效果如何？",
             "opts": ["翻倍分散", "≈ 买一只，几乎没分散", "风险互相抵消", "必然盈利"],
             "ans": 1, "exp": "同涨同跌的两只，就是同一份风险买了两份。"},
            {"q": "构建标的池的核心指标是什么？",
             "opts": ["每只都买一点", "相关性矩阵——谁和谁涨跌不同步", "市值大小", "名字好不好听"],
             "ans": 1, "exp": "先定主资产，把相关性最高的候选踢出局。"},
        ],
    },
}


class Progress:
    """关卡进度：首通记录 + 测验统计 + 每日复习打卡"""

    def __init__(self, data_path=None):
        self.data_path = data_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "data", "progress.json")
        self.completed = []          # ["1-1", ...] 兼容旧数据
        self.details = {}            # lid -> {"at": 首通日期, "quiz": 测验得分, "attempts": 尝试次数}
        self.reviews = {}            # lid -> 最近复习日期（每日限一次）
        self.quiz_correct_total = 0  # 累计答对测验题数
        self.load()

    def load(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, encoding="utf-8") as f:
                d = json.load(f)
            self.completed = d.get("completed", [])
            self.details = d.get("details", {})
            self.reviews = d.get("reviews", {})
            self.quiz_correct_total = d.get("quiz_correct_total", 0)

    def save(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump({"completed": self.completed, "details": self.details,
                       "reviews": self.reviews, "quiz_correct_total": self.quiz_correct_total},
                      f, ensure_ascii=False, indent=2)

    def done(self, lid):
        return lid in self.completed

    def complete(self, lid, quiz_ok, attempts=1):
        """记录一次测验成绩；返回 True 表示本关首通"""
        self.quiz_correct_total += quiz_ok
        self.details.setdefault(lid, {"at": str(date.today()), "quiz": 0, "attempts": 0})
        self.details[lid]["quiz"] = quiz_ok
        self.details[lid]["attempts"] = self.details[lid].get("attempts", 0) + attempts
        if lid not in self.completed:
            self.completed.append(lid)
            self.details[lid]["at"] = str(date.today())
            self.save()
            return True
        self.save()
        return False

    def reviewed_today(self, lid):
        return self.reviews.get(lid) == str(date.today())

    def mark_reviewed(self, lid):
        self.reviews[lid] = str(date.today())
        self.save()

    def next_level(self):
        """返回下一个未完成关卡 (lid, level)；全部完成返回 (None, None)"""
        for ch in sorted(WORLDS):
            for lid in sorted(LEVELS):
                if int(lid.split("-")[0]) == ch and not self.done(lid):
                    return lid, LEVELS[lid]
        return None, None

    def world_progress(self, chapter):
        ids = [l for l in LEVELS if int(l.split("-")[0]) == chapter]
        return sum(1 for l in ids if self.done(l)), len(ids)

    def worlds_cleared(self):
        """已通关的世界数（有关卡内容的世界）"""
        return sum(1 for ch in WORLDS
                   if self.world_progress(ch)[1] > 0
                   and self.world_progress(ch)[0] == self.world_progress(ch)[1])


# ---------------------------------------------------------------- 任务求解引擎
# 每种 task type 用「今天的真实市场数据」计算标准答案——每天题目一样、答案不同，
# 逼着玩家真的去看数据，而不是背答案。

def solve_task(ttype):
    """计算实战任务的真实答案。返回 (answer, info) 或 (None, error)。

    info 是任务文本格式化参数（date/price/window/start/end/数值等），
    app 用它渲染题目，也用于答后展示真实数据依据。
    """
    from trader_growing.dashboard import (load_latest, common_close,
                                          window_ret, annualized_vol, pair_corr)
    today = date.today()

    if ttype == "calc_shares":
        close = load_latest("510300.SS")
        if close is None:
            return None, "本地数据缺失"
        px = float(close.iloc[-1])
        return round(1000 / px), {"date": str(today), "price": round(px, 3)}

    if ttype == "ma_direction":
        close = load_latest("510300.SS")
        if close is None:
            return None, "本地数据缺失"
        px = float(close.iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])
        return (1 if px > ma20 else -1), {"date": str(today), "price": round(px, 3),
                                          "ma20": round(ma20, 3)}

    if ttype == "vs_benchmark":
        close = load_latest("510300.SS")
        if close is None:
            return None, "本地数据缺失"
        px = float(close.iloc[-1])
        ref = close.iloc[-252] if len(close) > 252 else close.iloc[0]
        diff = px / float(ref) - 1
        ans = 1 if diff > 0.005 else -1 if diff < -0.005 else 0
        ref_date = close.index[-(252 + 1)].date() if len(close) > 252 else close.index[0].date()
        return ans, {"date": str(today), "price": round(px, 3),
                     "ref": str(ref_date)}

    if ttype == "overfit_choice":
        return 2, {"date": str(today)}

    if ttype == "vol_compare":
        cc = common_close(["600519.SS", "510300.SS"])
        if not cc:
            return None, "个股数据缺失"
        ca = cc["600519.SS"].tail(253)
        cb = cc["510300.SS"].tail(253)
        va, vb = annualized_vol(ca), annualized_vol(cb)
        if va is None or vb is None:
            return None, "个股数据不足"
        ans = 1 if va > vb * 1.03 else -1 if vb > va * 1.03 else 0
        return ans, {"date": str(today),
                     "start": str(ca.index[0].date()),
                     "end": str(ca.index[-1].date()),
                     "vol_a": va, "vol_b": vb}

    if ttype == "ret_compare":
        close_a, close_b = load_latest("513100.SS"), load_latest("510300.SS")
        if close_a is None or close_b is None:
            return None, "本地数据缺失"
        ra, rb = window_ret(close_a), window_ret(close_b)
        if ra is None or rb is None:
            return None, "数据不足"
        ans = 1 if ra > rb * 1.01 + 0.005 else -1 if rb > ra * 1.01 + 0.005 else 0
        n = min(252, len(close_a), len(close_b))
        return ans, {"date": str(today), "window": n,
                     "start": str(close_a.index[-n - 1].date()), "end": str(close_a.index[-1].date()),
                     "ret_a": ra, "ret_b": rb}

    if ttype == "corr_sign":
        c = pair_corr(load_latest("518880.SS"), load_latest("510300.SS"))
        if c is None:
            return None, "数据不足"
        ans = 1 if c > 0.15 else -1 if c < -0.15 else 0
        n = 252
        return ans, {"date": str(today), "window": n, "corr": round(c, 3)}

    if ttype == "min_corr":
        base = load_latest("510300.SS")
        cands = [(1, "513100.SS", "纳指100"), (2, "518880.SS", "黄金"), (3, "501018.SS", "原油")]
        corrs = []
        for idx, sym, name in cands:
            c = pair_corr(base, load_latest(sym))
            if c is None:
                return None, "数据不足"
            corrs.append((idx, name, c))
        best = min(corrs, key=lambda x: x[2])
        return best[0], {"date": str(today), "window": 252,
                         "corrs": ", ".join("{}={:+.2f}".format(n, c) for _, n, c in corrs),
                         "lowest": best[1]}
