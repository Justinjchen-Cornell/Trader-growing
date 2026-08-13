# 给《人人都是量化交易员》仓库的提案（Issue 文案）

> 发布地址：https://github.com/xingwudao/xquant-beginner/issues/new
> 状态：待发布（需要登录 GitHub 后复制粘贴）

## 标题

配套练习系统 Trader-growing：把书里的实验做成"每天答案都在变"的闯关游戏

## 正文

我是本书的读者，按照书里"做 → 看 → 疑"的方法论，把全书实验做成了一个开源配套练习系统 **Trader-growing**，想请作者和读者们看看，是否值得作为书的配套练习挂载。

**它解决什么问题**：读一章书，懂了；一周后忘一半。这个系统把每章的实验变成**关卡**——知识卡（书中概念提炼）+ 实战任务 + 测验，通关一章才解锁下一章。

**和普通题库的区别**：实战任务用**当天的真实行情**判分。比如"今天沪深300ETF 收盘 4.728 元，定投 1000 元能买多少份？"——答案每天随行情变化，背不了，只能真的去看数据。

### 功能清单

- 🎮 **9 世界 36 关**：对应全书 9 章，每章 4 关（3 小关 + 1 BOSS）
  - 例：第 6 章"陷阱迷宫"BOSS 关用真实 5 年数据做交叉验证（奇数年 vs 偶数年切法，结论直接相反）
- ⚡ **今日一题**：每天 30 秒真实数据挑战 + 分享卡片 PNG（可发微信群）
- 🧪 **实验场**：定投/均线择时/等权/风险平价/动量轮动 5 种策略，真实数据一键回测
  （净值曲线 + 夏普 + 最大回撤 + 水下曲线）
- 🎯 **今日操作台**：四资产看板 + 策略计划 + 30 秒纪律对账
- 📜 图鉴 39 条（书中知识点）· 🏅 成就 13 枚 · 📅 修行周报 · 每日复习/BOSS 复战
- 🔒 本地优先（数据全在本地，无服务器），数据源 akshare 免费获取（Wind skill 可选）

### 截图

| 今日一题 | 实验场 | 学习关卡 |
|:---:|:---:|:---:|
| <img src="https://raw.githubusercontent.com/Justinjchen-Cornell/Trader-growing/master/assets/screenshots/home.png" width="330"> | <img src="https://raw.githubusercontent.com/Justinjchen-Cornell/Trader-growing/master/assets/screenshots/lab.png" width="330"> | <img src="https://raw.githubusercontent.com/Justinjchen-Cornell/Trader-growing/master/assets/screenshots/levels.png" width="330"> |

### 仓库

https://github.com/Justinjchen-Cornell/Trader-growing

- 代码 MIT 许可（个人/教育免费）
- 知识卡内容为书中概念的转述提炼，遵循原书 CC BY-NC-SA 4.0 的精神（非商业）
- 如果内容上有与书本不符或理解偏差的地方，非常欢迎指出，这正是"疑"的练习

### 提议

如果作者觉得合适，可以考虑在书 README 的"配套资源/练习"位置挂一个链接，让读者读完一章就闯一关；如果内容有偏差，也欢迎随时反馈，我会持续按书修订。

## 发布步骤

1. 登录 GitHub，打开：https://github.com/xingwudao/xquant-beginner/issues/new
2. 粘贴上面的标题和正文
3. （可选）加 labels：`enhancement` / `documentation`
