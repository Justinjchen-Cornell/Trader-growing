<p align="center">
  <img src="https://img.shields.io/badge/version-3.2.0-blue" alt="version">
  <img src="https://img.shields.io/badge/python-3.10%2B-green" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="license">
  <img src="https://img.shields.io/badge/platform-local--first-orange" alt="local-first">
</p>

<h1 align="center">🌱 Trader-growing · The Trader's Garden</h1>

<p align="center">
  <b>Turn your trading life into a garden you can watch grow.</b><br>
  5 minutes of watering a day (discipline check-ins), a basket of fruit a week (factor experiments),
  a pruning every quarter (strategy check-ups) — gamify discipline, and let the real market test your growth.
</p>

---

## 🌟 What Is This?

**Trader-growing** is a local-first tool that gamifies the "trader's cultivation."

You know the feeling: you *know* you should stop-loss, but your hand hovers. You *know* you should stay in cash, but you add one more lot anyway. Then regret, self-blame, repeat. **The problem isn't knowledge — it's that discipline has no feedback loop.** And games are the strongest feedback machines ever built.

We split trading psychology into four RPG-style attributes, and give you instant feedback through levels, XP, streaks, and badges:

```
📐 MATH —— Did you rationally assess probability and odds?
💰 FINANCE —— Did you follow your rules and risk controls?
🧠 PSYCHOLOGY —— Did you control emotion and impulse?
🔮 PHILOSOPHY —— Did you embrace uncertainty and failure?
```

> 🎮 **Not casino-style gamification** (gacha / leaderboards / anxiety) — **cultivation-style gamification**:
> losses are not punished, they are reframed as XP. Daily sessions are capped at 5 minutes;
> go over and the system says — "You've cultivated enough today. Go live."

**🎮 Learning Levels** (turn the book *Everyone Is a Quant Trader* into a dungeon crawler):

```
🌍 9 worlds (one per book chapter) → each level = knowledge card + live-data task + quiz
🧪 Tasks are graded against TODAY's real market data — the answers change every day
✅ First clear: +15~30 XP + attribute +5 + bestiary entry | Daily review: +5 XP
```

**Status (V3.2): all 9 worlds × 4 levels = 36 levels are live.**

| World | Levels (level → BOSS) |
|-------|----------------------|
| W1 新手村 Novice | 定投播种 → 基准对决 → 均线信号 → **过拟合挑战** |
| W2 选什么 Selection | 个股vsETF → 中美锚定 → 相关性探秘 → **标的池挑战** |
| W3 分多少 Sizing | 等权分钱 → 风险平价 → 动量排名 → **盈亏比之战** |
| W4 何时动 Timing | 再平衡 → 止损 → 止盈 → **锯齿效应** |
| W5 体检台 Inspection | 基准对比 → 逐年拆解 → 回撤深度 → **参数敏感性** |
| W6 陷阱迷宫 Overfit Maze | 样本内外 → Walk-forward → 交叉验证 → **规则负担** |
| W7 现实世界 Reality | 整手订单 → 滑点 → 成本层叠 → **执行落差** |
| W8 守护者 Guardian | 监控仪表盘 → 诊断三问 → 假设对照 → **归因总账** |
| W9 研究者 Researcher | 因子初识 → IC 初测 → 因子失效点 → **因子评估总账** |

30+ live-data task types: DCA shares, volatility & return comparisons, correlation, risk parity,
momentum ranking, profit/loss ratio, stop/take prices, max drawdown, excess return, in/out-of-sample,
walk-forward, lot sizing (100-share lots), slippage, cost stacking, attribution math, conditional
hypothesis tests, factor IC (Spearman), and more. Completing a chapter unlocks the next world.

---

## 🏡 The Garden (A Double Meaning of "Growing")

"Growing" means both **leveling up** and **gardening**. Your garden has four plants, one per attribute. Water them daily (check in) and they grow:

```
  Trader-growing · Growth Garden
  ========================================
  -@| Math        [ 65/100]  Young Tree
  -@@ Finance     [ 78/100]  Big Tree
  --| Psychology  [ 52/100]  Sapling
  -@| Philosophy  [ 70/100]  Young Tree
  ========================================
  Tip: water daily (check in) and all four will bloom
```

| Game Stage | Garden | Trader Stage |
|-----------|--------|--------------|
| 🌱 Seed | Investment idea | Form a hypothesis |
| 🌿 Sprout | Backtest validation | spec → backtest |
| 🌳 Sapling | Paper trading | Execute trades |
| 🌲 Tree | Small real capital | Monitor & iterate |
| 🍎 Fruit | Factor research | Harvest consistently |
| ✂️ Pruning | Strategy iteration | Cut the overfit branches |

---

## 🎮 Game Mechanics

| Mechanic | Rule | Philosophy |
|----------|------|------------|
| **XP / Levels** | Rookie → Apprentice → Skilled → Expert → Master | Growth you can see |
| **Streak bonus** | Check in ≥3 days straight, XP ×1.5 | Persistence pays |
| **Gentle penalty** | Days with discipline issues: XP halved (never zeroed) | Failure is experience |
| **Achievements** | No-Impulse / Loss-Cutter / Cash-Master / Four-Bloom… | Even admitting mistakes becomes an honor |
| **5-minute cap** | "You've cultivated enough today" | Moderation is the highest discipline |

7 starter badges included, e.g.:

- 🏅 **Loss Cutter**: execute stop-loss 10 times — turn the hardest "admitting a mistake" into something worth showing off
- 🏅 **Cash Master**: honor "being in cash is also a position" for 30 days — doing nothing is also cultivation
- 🏅 **Four-Bloom**: all four attributes ≥ 70 — no lopsided growth allowed

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/Justinjchen-Cornell/Trader-growing.git
cd Trader-growing

# 2. One-click environment setup (deps + Wind data source + API key + first data)
python scripts/setup.py

# 3. Run the full demo (3 simulated days: check-in → reconcile → growth)
python scripts/demo.py

# 4. Refresh market data (levels & dashboard depend on it)
python scripts/update_data.py

# 5. Begin your practice
streamlit run app.py              # 🌐 Web UI (recommended! 10 tabs incl. 🎮 Learning Levels)
python scripts/tg.py check        # daily check-in (enter 4 attribute scores)
python scripts/tg.py status       # character / garden / tier
python scripts/tg.py dashboard    # four-asset dashboard (gold/oil/CSI300/Nasdaq)
python scripts/tg.py plan         # today's strategy plan (Zhongyong)
python scripts/tg.py reconcile    # discipline reconciliation (plan vs diary)
python scripts/tg.py quests       # quest list (daily + weekly, +XP)
python scripts/tg.py stats        # discipline trend stats (score vs red flags)
```

Demo output (the day with discipline issues):

```
【2026-08-08】check-in +5 XP | streak 2 | 4 issues
    🔴 Off-plan trade: strategy said "HOLD", but a trade happened today
    🔴 Impulse trade: unplanned position (violates MATH discipline)
    🔴 Manually moved stop-loss (violates FINANCE discipline)
    🔴 Trade not strictly executed per plan
```

---

## 📁 Structure

```
Trader-growing/
├── app.py                    # 🌐 Web UI (Streamlit, 10 tabs)
├── trader_growing/           # core package
│   ├── character.py          # level / XP / streak / four attributes
│   ├── achievements.py       # badge system (13 badges)
│   ├── models.py             # data models (diary / plan / reconcile)
│   ├── reconcile.py          # discipline reconciliation (plan vs actual)
│   ├── garden.py             # ASCII growth garden
│   ├── dashboard.py          # four-asset dashboard + data helpers (vol/corr/drawdown/yearly)
│   ├── levels.py             # 🎮 learning levels: 9 worlds / 36 levels + live-data task engine
│   ├── questions.py          # daily cultivation test bank (tiered)
│   ├── knowledge.py          # objective knowledge test bank
│   ├── bestiary.py           # 📜 knowledge bestiary (34 entries)
│   ├── quests.py             # daily / weekly quests
│   ├── tiers.py              # tiered real-money unlocking (L0-L3)
│   ├── stats.py              # discipline trend stats
│   ├── peerboard.py          # anonymous peer board (local-first)
│   ├── journal_bridge.py     # cultivation journal Skill integration
│   ├── strategy_bridge.py    # Zhongyong strategy plan integration
│   └── scoring_guide.py      # four-attribute scoring reference
├── scripts/
│   ├── setup.py              # one-click environment setup
│   ├── update_data.py        # refresh market data (levels & dashboard depend on it)
│   ├── demo.py               # end-to-end demo
│   ├── daily_flow.py         # daily CLI
│   └── tg.py                 # main CLI (check/status/dashboard/plan/reconcile/quests/stats)
├── assets/
│   └── assets.yaml           # four assets (gold / oil / CSI300 / Nasdaq)
├── data/                     # runtime data (gitignored, personal privacy)
├── docs/
│   ├── ROADMAP.md            # roadmap
│   ├── DAILY_RITUAL.md       # daily practice flow
│   └── WIND_SETUP.md         # Wind data source setup
├── README.md                 # Chinese
├── README.en.md              # this file (English)
└── requirements.txt
```

---

## 🌍 Connecting to the Real World (in progress)

The end goal: **let the garden grow in the real market.**

| Asset | Code | One-liner |
|-------|------|-----------|
| 🟥 CSI 300 ETF | 510300.SS | Core Chinese equities |
| 🟦 Nasdaq 100 ETF | 513100.SS | US tech leaders (A-share QDII, buyable in CNY) |
| 🟨 Gold ETF | 518880.SS | The "anchor" that doesn't move with stocks |
| 🟫 Crude Oil LOF | 501018.SS | High-volatility commodity |

**Tiered real-money unlocking** (risk control as a game — the question isn't "can you make money", it's "does your discipline deserve real money"):

```
L0 Observer   Watch signals, don't trade        (unlock: 7 days of check-ins)
L1 Simulator  Paper trade + daily reconcile      (unlock: avg discipline ≥ 70)
L2 Small real Small capital per asset            (unlock: discipline ≥ 80 & zero red flags)
L3 Portfolio  Four-asset risk parity + vol filter (unlock: 60 clean days at L2)
```

---

## 🔗 Ecosystem

| Component | Role |
|-----------|------|
| 📚 "Everyone Is a Quant Trader" (open-source book, Chinese) | Methodology: spec / 4 phases / do-see-doubt |
| ⚙️ Zhongyong Strategy (multi-timeframe MACD) | Hard system: generates trade plans (plan.py) |
| 📓 Trader Cultivation Journal Skill | Soft power: daily scoring records (diary JSON) |

Data models are JSON-compatible with these components for direct integration.

---

## 🗺️ Roadmap

- **V0.5**: character / badges / reconcile / garden / demo ✅
- **V1.0**: four-asset dashboard + tiered real-money unlocking + strategy plan integration ✅
- **V1.5**: bestiary system (knowledge entries from the book) + weekly factor experiment quests ✅
- **V2.0**: web UI (10 tabs) + optional anonymous peer board ✅
- **V2.5-V2.9**: learning levels — chapters 1-6 (24 levels) + daily review + level achievements ✅
- **V3.0-V3.2**: chapters 7-9 — **all 9 worlds / 36 levels complete** ✅

See [docs/ROADMAP.md](docs/ROADMAP.md).

---

## 🤝 Contributing

Issues, PRs, and "garden screenshots" are all welcome. (CONTRIBUTING.md planned)

## ⚠️ Disclaimer

For education and research only — not investment advice. Past performance does not guarantee future results; any strategy can lose money. **Plant first, harvest later. Cultivate first, trade later.**

## 💼 Commercial Licensing

The source code is released under the **MIT License** (free forever for personal / educational / research use — including learning, academic research, and non-commercial projects).

However, the following situations are **NOT covered by the free MIT grant** and require a separate commercial license:

- Using this project (or its core logic) in a **commercial product**: SaaS / cloud-hosted service / enterprise deployment
- Selling this project as part of a **paid product or service**
- Using this project in **production systems** within a company or team

For commercial licensing, custom development, or partnerships, please open a [GitHub Issue](https://github.com/Justinjchen-Cornell/Trader-growing/issues) or contact us via the sponsorship links in the README (optional, supports ongoing maintenance).

> Commercial licensing process: ① Describe your use case in an Issue → ② Confirm scope & fee (one-time / annual / revenue-share) → ③ Sign the license agreement. Personal and educational use is always free — use it with confidence.

## 📄 License

- **Code**: MIT License (free for personal/educational/research use; commercial products require a separate license)
- **Docs & Design**: CC BY-NC-SA 4.0 (Attribution-NonCommercial-ShareAlike)
