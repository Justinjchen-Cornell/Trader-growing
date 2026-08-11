# -*- coding: utf-8 -*-
"""每日修行测试：分级题库（小白 → 进阶 → 专业）

每题 0-4 分（0=完全否 1=基本否 2=不确定 3=基本是 4=完全是）
难度分级（随角色等级解锁，像 RPG 技能树）:
  🐣 L1 小白题：行为事实（今天做了没有）
  🌱 L2 进阶题：认知理解（懂不懂原理）
  🎓 L3 专业题：专业深化（能不能算出来）

解锁规则：
  菜鸟/学徒(0-299 XP): 只答 L1（8 题，1 分钟）
  熟练(300-599):       L1+L2（16 题，2 分钟）
  专家/大师(600+):     全部（24 题，3 分钟）
"""

LEVEL_META = {
    1: {"badge": "🐣", "name": "小白"},
    2: {"badge": "🌱", "name": "进阶"},
    3: {"badge": "🎓", "name": "专业"},
}

QUESTIONS = {
    "math": [
        # L1 行为事实
        {"level": 1, "text": "今天我看过行情/数据了吗（知道市场大致状态）"},
        {"level": 1, "text": "今天我做的每个决定都有明确依据，不是随手一拍"},
        # L2 认知理解
        {"level": 2, "text": "我使用的因子/信号经过了严格的回测验证（非拍脑袋）"},
        {"level": 2, "text": "我能区分'噪声'与'信号'，不因短期波动推翻统计结论"},
        # L3 专业深化
        {"level": 3, "text": "我能清晰说出当前持仓每笔交易的胜率与赔率预估"},
        {"level": 3, "text": "我对仓位大小的设定基于凯利公式或固定比例，而非感觉"},
    ],
    "finance": [
        {"level": 1, "text": "今天如果持仓，我的止损线挂好了（没手动移开）"},
        {"level": 1, "text": "今天没有满仓梭哈或加杠杆（仓位在可承受范围）"},
        {"level": 2, "text": "我的单笔最大风险不超过总资金的预设比例（如2%）"},
        {"level": 2, "text": "我了解今天交易标的的流动性/基本面风险"},
        {"level": 3, "text": "我今日严格遵守了预设的止损线，未手动移动"},
        {"level": 3, "text": "我的交易费用（佣金+滑点+税费）在策略预算内"},
    ],
    "psychology": [
        {"level": 1, "text": "今天手痒想交易时，我忍住了（或根本没手痒）"},
        {"level": 1, "text": "今天没有因为涨跌而心情大起大落"},
        {"level": 2, "text": "我没有因为上一笔亏损而'报复性加仓'"},
        {"level": 2, "text": "我没有因为浮盈而过早止盈（破坏原定计划）"},
        {"level": 3, "text": "我未被社交媒体/群聊情绪裹挟做出冲动决策"},
        {"level": 3, "text": "开盘前/决策前我感到平静，无焦虑或亢奋"},
    ],
    "philosophy": [
        {"level": 1, "text": "今天接受'不懂就不做'了吗（空仓也是持仓）"},
        {"level": 1, "text": "今天没有把亏损怪到市场/消息/别人头上"},
        {"level": 2, "text": "我承认自己的模型/判断可能出错，并预留了安全边际"},
        {"level": 2, "text": "我对今日可能的最大连续亏损有心理准备"},
        {"level": 3, "text": "我能接受'做了正确决策却依然亏损'的结果"},
        {"level": 3, "text": "我相信概率会随样本增大而收敛，不因短期运气否定系统"},
    ],
}

DIM_NAMES = {"math": "数学", "finance": "金融", "psychology": "心理", "philosophy": "哲学"}
DIM_EMOJI = {"math": "📐", "finance": "💰", "psychology": "🧠", "philosophy": "🔮"}
SCALE = "0=完全否  1=基本否  2=不确定  3=基本是  4=完全是"


def max_level_for_xp(xp):
    """角色 XP -> 解锁的题目级别"""
    if xp >= 600:
        return 3
    if xp >= 300:
        return 2
    return 1


def questions_for(level):
    """按级别过滤题库 -> {dim: [text,...]}"""
    out = {}
    for d, qs in QUESTIONS.items():
        out[d] = [q["text"] for q in qs if q["level"] <= level]
    return out


def level_badges(level):
    return " ".join("{} {}".format(LEVEL_META[l]["badge"], LEVEL_META[l]["name"])
                    for l in sorted(LEVEL_META) if l <= level)


def dim_score(answers):
    raw = sum(answers)
    return round(raw / (4 * len(answers)) * 100, 1)


def overall_score(dim_scores):
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
    f = answers.get("finance", [5] * 6)
    p = answers.get("psychology", [5] * 6)
    if len(f) > 0 and f[0] <= 1:
        flags.append("金融: 止损线没挂好/被移开")
    if len(p) > 0 and p[0] <= 1:
        flags.append("心理: 手痒没忍住/情绪波动")
    if len(p) > 1 and p[1] <= 1:
        flags.append("心理: 因涨跌情绪大起大落")
    if len(f) > 3 and f[3] <= 1:
        flags.append("金融: 未评估标的流动性/基本面风险")
    return flags
