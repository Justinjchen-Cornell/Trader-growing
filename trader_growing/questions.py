# -*- coding: utf-8 -*-
"""每日修行测试：20 题客观题库（数学/金融/心理/哲学 各 5 题）

每题 0-4 分（0=完全否 1=基本否 2=不确定 3=基本是 4=完全是）
维度分 = 原始分 / (4*5) * 100 —— 自动计算，避免主观拍脑袋
"""

QUESTIONS = {
    "math": [
        "我能清晰说出当前持仓每笔交易的胜率与赔率预估",
        "我使用的因子/信号经过了严格的回测验证（非拍脑袋）",
        "我理解今日策略在大数定律下的长期期望是否为正",
        "我对仓位大小的设定基于凯利公式或固定比例，而非感觉",
        "我能区分'噪声'与'信号'，不因短期波动推翻统计结论",
    ],
    "finance": [
        "我今日严格遵守了预设的止损线，未手动移动",
        "我的单笔最大风险不超过总资金的预设比例（如2%）",
        "我了解今天交易标的的基本面/流动性风险",
        "我没有在保证金不足/杠杆过高的情况下开仓",
        "我的交易费用（佣金+滑点）在可接受范围内",
    ],
    "psychology": [
        "开盘前我感到平静，心率正常，无焦虑或亢奋",
        "我没有因为上一笔亏损而'报复性加仓'",
        "我没有因为浮盈而过早止盈（破坏原定计划）",
        "我未被社交媒体/群聊情绪裹挟做出冲动决策",
        "我能接受'今天不交易'也是一种正确的交易",
    ],
    "philosophy": [
        "我承认自己的模型/判断可能出错，并为此预留了安全边际",
        "我对今日可能的最大连续亏损有心理准备",
        "我不追求每笔都赢，只追求长期期望值正确",
        "我能接受'做了正确决策却依然亏损'的结果",
        "我相信概率会随样本增大而收敛，不因短期运气否定系统",
    ],
}

DIM_NAMES = {"math": "数学", "finance": "金融", "psychology": "心理", "philosophy": "哲学"}
DIM_EMOJI = {"math": "📐", "finance": "💰", "psychology": "🧠", "philosophy": "🔮"}

SCALE = "0=完全否  1=基本否  2=不确定  3=基本是  4=完全是"


def dim_score(answers):
    """answers: list[int] 长度 5 -> 0-100 分"""
    raw = sum(answers)
    return round(raw / (4 * len(answers)) * 100, 1)


def overall_score(dim_scores):
    """四维平均"""
    return round(sum(dim_scores.values()) / len(dim_scores), 1)


def grade(score):
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 50:
        return "C"
    return "D"


def red_flags_from_answers(answers):
    """从答案推断今日纪律红牌（客观）"""
    flags = []
    if answers.get("finance", [5, 5, 5, 5, 5])[0] <= 1:
        flags.append("金融F1: 未严格遵守止损线（可能移动过止损）")
    if answers.get("finance", [5, 5, 5, 5, 5])[3] <= 1:
        flags.append("金融F4: 杠杆/保证金风险敞口")
    if answers.get("psychology", [5, 5, 5, 5, 5])[1] <= 1:
        flags.append("心理P2: 报复性加仓倾向")
    if answers.get("psychology", [5, 5, 5, 5, 5])[3] <= 1:
        flags.append("心理P4: 被情绪裹挟的冲动决策")
    return flags
