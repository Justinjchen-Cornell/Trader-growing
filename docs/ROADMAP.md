# Trader-growing · 路线图

## V0.5（当前版本）—— 种子
- [x] 角色系统（等级 / XP / 连击 / 四维属性）
- [x] 成就徽章系统
- [x] 纪律对账核心（计划 vs 实际）
- [x] ASCII 成长花园
- [x] 全流程 Demo

## V1.0 —— 发芽 ✅
- [x] 四资产看板（金 / 油 / 沪深300 / 纳指 每日行情 + 轻信号）—— `tg.py dashboard`
- [x] 真钱分级解锁：L0 观察 → L1 模拟 → L2 小实盘 → L3 组合 —— `tiers.py`
- [x] 对接中庸策略 plan.py（计划 JSON）—— `strategy_bridge.py`
- [x] 对接修行日记 Skill（diary JSON）—— `journal_bridge.py`

## V1.5 —— 幼苗 ✅
- [x] 图鉴系统（24 个书中知识条目，打卡天数驱动解锁）—— `bestiary.py`
- [x] 每周任务（因子实验 / 参数研究 / 回测复现，+30 XP）—— `quests.py`
- [x] 偏差趋势统计（纪律分 vs 红牌的 Spearman 相关）—— `stats.py`

## V2.0 —— 小树 ✅
- [x] Streamlit Web 界面（花园/看板/图鉴/成长曲线/任务/徽章 6 个 tab）—— `app.py`
- [x] 可选匿名同行榜（本地匿名 ID / 导出导入成绩单 / 无服务器）—— `peerboard.py`
- [x] 多语言（中 / 英 README）

## 设计原则
1. 每日 5 分钟上限，超时提醒"今天的修行够了"
2. 亏损不被惩罚，被重新框架为"经验值"
3. 排行榜默认关闭（隐私 + 反焦虑）
4. 纯本地优先，云端可选
