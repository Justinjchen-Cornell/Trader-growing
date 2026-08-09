<p align="center">
  <img src="https://img.shields.io/badge/version-0.5.0-blue" alt="version">
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
git clone https://github.com/<your-username>/Trader-growing.git
cd Trader-growing

# 2. Install
pip install -r requirements.txt

# 3. Run the full demo (3 simulated days: check-in → reconcile → growth)
python scripts/demo.py

# 4. Begin your practice
python scripts/daily_flow.py check    # daily check-in (enter 4 attribute scores)
python scripts/daily_flow.py status   # view character & garden
python scripts/daily_flow.py plan     # view today's strategy plan
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
├── trader_growing/           # core package
│   ├── character.py          # level / XP / streak / four attributes
│   ├── achievements.py       # badge system
│   ├── models.py             # data models (diary / plan / reconcile)
│   ├── reconcile.py          # discipline reconciliation (plan vs actual)
│   └── garden.py             # ASCII growth garden
├── scripts/
│   ├── demo.py               # end-to-end demo
│   └── daily_flow.py         # daily CLI
├── assets/
│   └── assets.yaml           # four assets (gold / oil / CSI300 / Nasdaq)
├── data/                     # runtime data (gitignored)
├── docs/
│   └── ROADMAP.md            # roadmap
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

- **V0.5 (now)**: character / badges / reconcile / garden / demo ✅
- **V1.0**: four-asset dashboard + tiered real-money unlocking + strategy plan integration
- **V1.5**: bestiary system (knowledge entries from the book) + weekly factor experiment quests
- **V2.0**: web UI + optional anonymous peer board

See [docs/ROADMAP.md](docs/ROADMAP.md).

---

## 🤝 Contributing

Issues, PRs, and "garden screenshots" are all welcome. (CONTRIBUTING.md planned)

## ⚠️ Disclaimer

For education and research only — not investment advice. Past performance does not guarantee future results; any strategy can lose money. **Plant first, harvest later. Cultivate first, trade later.**

## 📄 License

MIT License
