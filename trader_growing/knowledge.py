# -*- coding: utf-8 -*-
import os
import json


"""客观知识题库：标准答案，骗不了自己

- 24 题（🐣小白 8 / 🌱进阶 8 / 🎓专业 8），与修行题同步按 XP 解锁
- 主题与图鉴联动：做对解锁图鉴条目
- 错题本：答错进错题本，隔天复习
- 知识分：做对/总题 × 100，独立于修行分
"""

QUESTIONS = [{'id': 'K1',
  'level': 1,
  'topic': '基础',
  'figure': 'backtest',
  'q': 'ETF 是什么？',
  'opts': ['一篮子股票的打包组合', '一种债券', '一种期货合约', '单只公司的股票'],
  'ans': 0,
  'exp': 'ETF 把一篮子资产打包成一份可在交易所买卖的基金。'},
 {'id': 'K2',
  'level': 1,
  'topic': '基础',
  'figure': 'backtest',
  'q': '回测（Backtest）是什么？',
  'opts': ['预测未来走势', '用历史数据模拟策略执行', '实盘下单', '数据清洗'],
  'ans': 1,
  'exp': "回测=在历史数据上'重播'策略，不能预测未来，但能排除站不住脚的想法。"},
 {'id': 'K3',
  'level': 1,
  'topic': '基础',
  'figure': 'ma',
  'q': '均线 MA20 表示什么？',
  'opts': ['20 天成交量', '过去 20 天开盘价总和', '过去 20 天收盘价的平均值', '20 天最高价'],
  'ans': 2,
  'exp': "MA20 = 过去 20 天收盘价的平均，像连续几天的'平均体温'。"},
 {'id': 'K4',
  'level': 1,
  'topic': '基础',
  'figure': 'benchmark',
  'q': '基准（Benchmark）的作用是什么？',
  'opts': ['增加交易量', '保证盈利', '预测收益', "提供'什么都不做'的参照物"],
  'ans': 3,
  'exp': "没有参照物的收益没有意义——先和'买入持有'比，才知道策略好不好。"},
 {'id': 'K5',
  'level': 1,
  'topic': '基础',
  'figure': 'backtest',
  'q': '定投（定期定额）的核心特点是？',
  'opts': ['分散买入时点、摊低成本', '一次性全仓', '只买最贵的', '追涨杀跌'],
  'ans': 0,
  'exp': '价格低多买份额、价格高少买份额——避开一次性买在最高点的风险。'},
 {'id': 'K6',
  'level': 1,
  'topic': '风控',
  'figure': 'stop_loss',
  'q': '止损（Stop Loss）的作用是？',
  'opts': ['锁定利润', '预设底线，跌破自动卖出', '增加仓位', '缩短交易时间'],
  'ans': 1,
  'exp': '止损=先保命再谈收益。但注意：持续阴跌中它可能产生锯齿效应。'},
 {'id': 'K7',
  'level': 1,
  'topic': '指标',
  'figure': 'calmar',
  'q': '年化波动率衡量什么？',
  'opts': ['持仓时间', '赚了多少', '价格波动的剧烈程度', '交易次数'],
  'ans': 2,
  'exp': '波动率大=过山车，小=高铁。波动率小的策略你才拿得住。'},
 {'id': 'K8',
  'level': 1,
  'topic': '指标',
  'figure': 'calmar',
  'q': '最大回撤衡量什么？',
  'opts': ['每天涨跌', '最大成交量', '总收益', '从最高点跌了多少'],
  'ans': 3,
  'exp': '最大回撤=最惨时从峰值跌多少，直接关系到你晚上睡不睡得着。'},
 {'id': 'K9',
  'level': 2,
  'topic': '指标',
  'figure': 'sharpe',
  'q': '夏普比率衡量什么？',
  'opts': ['每承受一份波动换来多少收益', '最大回撤', '胜率', '总收益'],
  'ans': 0,
  'exp': "夏普=收益/波动，'性价比'。简化口径=年化收益/年化波动。"},
 {'id': 'K10',
  'level': 2,
  'topic': '陷阱',
  'figure': 'overfit',
  'q': '过拟合（Overfitting）指什么？',
  'opts': ['代码写错了', '参数在历史数据上表现好、样本外大幅衰减', '数据缺失', '交易太频繁'],
  'ans': 1,
  'exp': "过拟合=把历史噪音当规律。'背答案'不是'真会做'。"},
 {'id': 'K11',
  'level': 2,
  'topic': '配置',
  'figure': 'risk_parity',
  'q': '风险平价（Risk Parity）的核心是？',
  'opts': ['全仓现金', '各买 1/3', '按波动率倒数分配权重', '只买涨得好的'],
  'ans': 2,
  'exp': "波动大的少买、波动小的多买——让每只资产对组合的'影响力'均匀。"},
 {'id': 'K12',
  'level': 2,
  'topic': '配置',
  'figure': 'momentum',
  'q': '动量排名里 filter_negative=True 是什么意思？',
  'opts': ['买满仓', '不做任何过滤', '只买跌的', '动量（趋势）为负的不买'],
  'ans': 3,
  'exp': "'正在跌的不买'——动量排名的硬规则。"},
 {'id': 'K13',
  'level': 2,
  'topic': '验证',
  'figure': 'param_sens',
  'q': "参数敏感性'高原型'（Plateau）指？",
  'opts': ['参数怎么调结果都差不多', '参数一变结果暴跌', '找不到最优参数', '参数越多越好'],
  'ans': 0,
  'exp': '高原型=站在哪都差不多高，好策略不怕参数变。'},
 {'id': 'K14',
  'level': 2,
  'topic': '陷阱',
  'figure': 'whipsaw',
  'q': '锯齿效应（Whipsaw）发生在什么场景？',
  'opts': ['单边上涨', '持续下跌中反复卖出又买回', '横盘不动', '大牛市'],
  'ans': 1,
  'exp': "每轮'卖-买回'都付手续费，回撤反而可能加深。"},
 {'id': 'K15',
  'level': 2,
  'topic': '执行',
  'figure': 'impl_short',
  'q': '执行落差（Implementation Shortfall）指？',
  'opts': ['滑点定义', '策略收益与基准的差', '回测收益与真实交易收益的差', '佣金高低'],
  'ans': 2,
  'exp': '回测用收盘价成交，真实交易有滑点/成本/时点差异——执行落差是常态。'},
 {'id': 'K16',
  'level': 2,
  'topic': '验证',
  'figure': 'oos',
  'q': '样本外测试（Out-of-Sample）是什么？',
  'opts': ['只测一年', '随机抽样本', '用全部数据测试', '用参数从没见过的数据验证'],
  'ans': 3,
  'exp': "闭卷考：训练集选出的'最优'参数，到新数据上重新考一次。"},
 {'id': 'K17',
  'level': 3,
  'topic': '指标',
  'figure': 'sharpe',
  'q': '本书的简化夏普比率公式是？',
  'opts': ['年化收益 / 年化波动率', '年化收益 × 年化波动率', '波动率 / 收益', '年化收益 / 最大回撤'],
  'ans': 0,
  'exp': '简化夏普=年化收益/年化波动（不扣无风险收益）；标准版分子要减无风险利率。'},
 {'id': 'K18',
  'level': 3,
  'topic': '研究',
  'figure': 'ic',
  'q': 'IC（信息系数）衡量什么？',
  'opts': ['策略收益', '因子排名与未来收益排名的相关性', '波动率', '回撤深度'],
  'ans': 1,
  'exp': 'IC=每个截面期因子排名与收益排名的 Spearman 相关，|IC|>0.05 算不错的因子。'},
 {'id': 'K19',
  'level': 3,
  'topic': '验证',
  'figure': 'walkforward',
  'q': 'Walk-forward 分析的作用是？',
  'opts': ['清洗数据', '一次选最优参数', "模拟'定期重新优化参数'并检验稳定性", '画净值图'],
  'ans': 2,
  'exp': '边走边调：参数跨窗口稳定=可信；每折都变=在追噪音。'},
 {'id': 'K20',
  'level': 3,
  'topic': '验证',
  'figure': 'cv',
  'q': '金融数据交叉验证的关键约束是？',
  'opts': ['测试集越长越好', '不需要切分', '可以随机打乱切分', '训练集永远在测试集之前（不偷看未来）'],
  'ans': 3,
  'exp': '时间序列切分：未来绝不能进训练集，否则=考试前偷看答案（数据泄露）。'},
 {'id': 'K21',
  'level': 3,
  'topic': '指标',
  'figure': 'calmar',
  'q': '卡玛比（Calmar Ratio）的公式是？',
  'opts': ['年化收益 / 最大回撤', '年化收益 / 波动率', '收益 × 回撤', '回撤 / 收益'],
  'ans': 0,
  'exp': "卡玛比=每承受 1% 最大回撤换来多少年化收益——'最怕跌得深'的尺子。"},
 {'id': 'K22',
  'level': 3,
  'topic': '陷阱',
  'figure': 'rule_burden',
  'q': '规则负担（Rule Burden）指什么？',
  'opts': ['规则越多策略越好', '每加一条规则=多一个旋钮，越容易过拟合', '规则没用', '规则太少'],
  'ans': 1,
  'exp': "旋钮越多越能'凑'出好看回测——少即是多，能用 2 个参数别用 6 个。"},
 {'id': 'K23',
  'level': 3,
  'topic': '指标',
  'figure': 'sortino',
  'q': '索提诺比（Sortino）与夏普的区别是？',
  'opts': ['用最大回撤做分母', '分子不同', '只把下行波动当风险（上涨颠簸不惩罚）', '没有区别'],
  'ans': 2,
  'exp': '索提诺只用亏损方向的波动做分母——你不在乎涨得猛，只在乎跌得惨。'},
 {'id': 'K24',
  'level': 3,
  'topic': '风控',
  'figure': 'vol_filter',
  'q': '波动率过滤（Vol Filter）的作用是？',
  'opts': ['只买高波动资产', '预测涨跌', '波动大时加仓', '市场波动率超阈值时减仓（多留现金）'],
  'ans': 3,
  'exp': '高波动时减仓躲暴跌——但注意它连高波动中的上涨也躲，防御有代价。'}]

TOPIC_FIGURE = {q["topic"]: q["figure"] for q in QUESTIONS}


class KnowledgeSystem:
    """知识分 / 错题本 / 历史记录"""

    def __init__(self, data_path=None):
        self.data_path = data_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "data", "knowledge.json")
        self.correct = 0        # 累计做对
        self.total = 0          # 累计作答
        self.wrong = []         # 错题本 [{q, picked, correct_ans, date}]
        self.history = []       # [{date, correct, total}]
        self.load()

    def load(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, encoding="utf-8") as f:
                d = json.load(f)
            self.correct = d.get("correct", 0)
            self.total = d.get("total", 0)
            self.wrong = d.get("wrong", [])
            self.history = d.get("history", [])

    def save(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump({"correct": self.correct, "total": self.total,
                     "wrong": self.wrong, "history": self.history},
                    f, ensure_ascii=False, indent=2)

    def score(self):
        return round(self.correct / self.total * 100, 1) if self.total else 0.0

    def record(self, q, picked, date):
        """q: 题目 dict; picked: 选项索引 -> 是否答对"""
        self.total += 1
        ok = picked == q["ans"]
        if ok:
            self.correct += 1
        else:
            self.wrong.append({"id": q["id"], "q": q["q"], "picked": picked,
                               "correct_ans": q["ans"], "date": str(date)})
        self.save()
        return ok
