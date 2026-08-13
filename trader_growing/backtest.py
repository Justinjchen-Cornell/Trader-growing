# -*- coding: utf-8 -*-
"""实验场：真实数据上的策略回测沙盒（书中实验的可玩版）

五种策略模板（对应书的前 3 章实验）：
  dca          定投（每月固定金额 vs 一次性买入）
  ma_timing    均线择时（价格 > MA 持有，否则空仓）
  equal_weight 等权组合（每月再平衡）
  risk_parity  风险平价（权重 ∝ 1/波动，每月再平衡）
  momentum     动量轮动（每月持有 20 日动量最强的一只）

输出：净值曲线（策略 vs 基准）+ 指标（总收益/年化/波动/夏普/最大回撤/卡玛）
"""
import os

import numpy as np
import pandas as pd

from trader_growing.dashboard import load_latest

ASSETS = {
    "510300.SS": "沪深300ETF",
    "513100.SS": "纳指100ETF",
    "518880.SS": "黄金ETF",
    "501018.SS": "原油LOF",
    "600519.SS": "贵州茅台",
}


def _aligned(syms):
    closes = {}
    for s in syms:
        c = load_latest(s)
        if c is None:
            return None
        closes[s] = c
    idx = closes[syms[0]].index
    for s in syms[1:]:
        idx = idx.intersection(closes[s].index)
    return pd.DataFrame({s: closes[s].loc[idx] for s in syms})


def metrics(equity):
    ret = equity.pct_change().dropna()
    total = float(equity.iloc[-1] / equity.iloc[0] - 1)
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)
    cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1)
    vol = float(ret.std() * np.sqrt(252))
    sharpe = float(cagr / vol) if vol > 0 else 0.0
    dd = float((equity / equity.cummax() - 1).min())
    calmar = float(cagr / abs(dd)) if dd < 0 else 0.0
    return {"total": total, "cagr": cagr, "vol": vol,
            "sharpe": sharpe, "max_dd": dd, "calmar": calmar}


def _month_change(idx):
    return idx.to_period("M") != idx.to_period("M").to_series().shift(1).values


# ---------------------------------------------------------------- 单资产策略
def backtest_dca(sym="510300.SS", monthly=1000):
    close = load_latest(sym)
    if close is None:
        return None
    g = close.groupby([close.index.year, close.index.month])
    mdates = pd.DatetimeIndex([grp.index[0] for _, grp in g])
    if len(mdates) < 2:
        return None
    n = len(mdates)
    total_cash = monthly * n
    events = pd.Series(monthly / close.loc[mdates], index=mdates)
    shares = events.cumsum().reindex(close.index, method="ffill").fillna(0)
    equity = close * shares
    # 从第一次买入日起计（避免首日份额为 0 导致收益率除零）
    equity = equity.loc[equity.index >= mdates[0]]
    bench = close / float(close.loc[mdates[0]]) * total_cash
    bench = bench.loc[bench.index >= mdates[0]]
    return equity, bench, {"总投入": int(total_cash), "定投次数": n}


def backtest_ma(sym="510300.SS", window=20, cost=0.0005):
    close = load_latest(sym)
    if close is None or len(close) < window + 5:
        return None
    sig = (close > close.rolling(window).mean()).astype(float)
    pos = sig.shift(1).fillna(0)
    r = close.pct_change().fillna(0)
    strat = pos * r
    turnover = pos.diff().abs().fillna(pos.abs())
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = close / float(close.iloc[0])
    return equity, bench, {"换手次数": int(turnover.sum()), "单边成本": cost}


# ---------------------------------------------------------------- 组合策略
def backtest_combo(syms, weight_fn, cost=0.0005):
    df = _aligned(syms)
    if df is None or len(df) < 70:
        return None
    r = df.pct_change().fillna(0)
    mc = _month_change(df.index)
    w = pd.DataFrame(0.0, index=df.index, columns=df.columns)
    prev = None
    for i in range(len(df)):
        d = df.index[i]
        if i == 0 or mc[i]:
            hist = df.iloc[max(0, i - 65):i + 1]
            wi = weight_fn(hist, r.iloc[max(0, i - 65):i + 1])
            wi = wi / wi.sum()
            w.iloc[i] = wi
            prev = wi
        else:
            drifted = prev * (1 + r.iloc[i])
            prev = drifted / drifted.sum()
            w.iloc[i] = prev
    strat = (w.shift(1) * r).sum(axis=1)
    turnover = w.diff().abs().sum(axis=1)
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = (df / df.iloc[0]).mean(axis=1)
    return equity, bench, {"再平衡次数": int(mc.sum()), "单边成本": cost}


def _w_equal(hist, r):
    return pd.Series(1.0 / len(hist.columns), index=hist.columns)


def _w_risk_parity(hist, r):
    vol = hist.pct_change().dropna().std()
    vol = vol.replace(0, np.nan)
    if vol.isna().all():      # 窗口太短（数据起点附近）→ 回退等权
        return pd.Series(1.0, index=hist.columns)
    inv = 1.0 / vol
    if inv.isna().any():
        inv = inv.fillna(inv.median())
    return inv


def backtest_macd(sym="510300.SS", fast=12, slow=26, cost=0.0005):
    """MACD 金叉：快线 MA 上穿慢线 MA 持多，下穿空仓（忠实移植 je-suis-tm/quant-trading）"""
    close = load_latest(sym)
    if close is None or len(close) < slow + 5:
        return None
    ma_f = close.rolling(int(fast)).mean()
    ma_s = close.rolling(int(slow)).mean()
    pos = (ma_f >= ma_s).astype(float).fillna(0)
    pos = pos.shift(1).fillna(0)
    r = close.pct_change().fillna(0)
    strat = pos * r
    turnover = pos.diff().abs().fillna(pos)
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = close / float(close.iloc[0])
    return equity, bench, {"快线": int(fast), "慢线": int(slow), "单边成本": cost}


def backtest_rsi(sym="510300.SS", window=14, oversold=30, overbought=70, cost=0.0005):
    """RSI 超买超卖：RSI < 超卖线买入，> 超买线卖出（Wilder RSI，低吸高抛）"""
    close = load_latest(sym)
    if close is None or len(close) < int(window) * 3:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1.0 / int(window), min_periods=int(window)).mean()
    avg_loss = loss.ewm(alpha=1.0 / int(window), min_periods=int(window)).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    pos = pd.Series(np.nan, index=close.index)
    pos[rsi < oversold] = 1.0
    pos[rsi > overbought] = 0.0
    pos = pos.ffill().fillna(0).shift(1).fillna(0)
    r = close.pct_change().fillna(0)
    strat = pos * r
    turnover = pos.diff().abs().fillna(pos)
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = close / float(close.iloc[0])
    return equity, bench, {"RSI 周期": int(window), "超买/超卖": "{}/{}".format(int(overbought), int(oversold)),
                           "单边成本": cost}


def backtest_bollinger(sym="510300.SS", window=20, n_std=2.0, cost=0.0005):
    """布林带均值回归：触下轨买入（低吸），触上轨卖出（高抛）"""
    close = load_latest(sym)
    if close is None or len(close) < int(window) * 2:
        return None
    mid = close.rolling(int(window)).mean()
    std = close.rolling(int(window)).std()
    upper = mid + n_std * std
    lower = mid - n_std * std
    pos = pd.Series(np.nan, index=close.index)
    pos[close < lower] = 1.0
    pos[close > upper] = 0.0
    pos = pos.ffill().fillna(0).shift(1).fillna(0)
    r = close.pct_change().fillna(0)
    strat = pos * r
    turnover = pos.diff().abs().fillna(pos)
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = close / float(close.iloc[0])
    return equity, bench, {"窗口": int(window), "标准差": n_std, "单边成本": cost}


def backtest_dual_thrust(sym="510300.SS", lookback=10, k=0.5, cost=0.0005):
    """双推力突破（日线版）：开盘 ± K×区间(近 N 日 HH/LC/HC/LL)，突破追入，反向离场"""
    df = _ohlcv(sym)
    if df is None or len(df) < int(lookback) + 5:
        return None
    hh = df["high"].rolling(int(lookback)).max()
    lc = df["low"].rolling(int(lookback)).min()
    hc = df["close"].rolling(int(lookback)).max()
    ll = df["low"].rolling(int(lookback)).min()
    rng = np.maximum(hh - lc, hc - ll)
    upper = df["open"] + k * rng.shift(1)
    lower = df["open"] - (1 - k) * rng.shift(1)
    pos = pd.Series(np.nan, index=df.index)
    pos[df["close"] > upper] = 1.0
    pos[df["close"] < lower] = 0.0
    pos = pos.ffill().fillna(0).shift(1).fillna(0)
    r = df["close"].pct_change().fillna(0)
    strat = pos * r
    turnover = pos.diff().abs().fillna(pos)
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = df["close"] / float(df["close"].iloc[0])
    return equity, bench, {"回看": int(lookback), "K": k, "单边成本": cost}


def backtest_awesome(sym="510300.SS", fast=5, slow=34, cost=0.0005):
    """神奇振荡器（Awesome Oscillator）：EMA 双均线 + AO 双均线（中价 5/34）双确认"""
    df = _ohlcv(sym)
    if df is None or len(df) < int(slow) * 2:
        return None
    med = (df["high"] + df["low"]) / 2
    ema_f = df["close"].ewm(span=int(fast)).mean()
    ema_s = df["close"].ewm(span=int(slow)).mean()
    ao_f = med.rolling(int(fast)).mean()
    ao_s = med.rolling(int(slow)).mean()
    pos = ((ema_f >= ema_s) & (ao_f >= ao_s)).astype(float)
    pos = pos.shift(1).fillna(0)
    r = df["close"].pct_change().fillna(0)
    strat = pos * r
    turnover = pos.diff().abs().fillna(pos)
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = df["close"] / float(df["close"].iloc[0])
    return equity, bench, {"快线": int(fast), "慢线": int(slow), "单边成本": cost}


def backtest_heikin_ashi(sym="510300.SS", cost=0.0005):
    """Heikin-Ashi 趋势蜡烛：HA 四条件进场 / 三条件出场（忠实移植源仓库逻辑）"""
    df = _ohlcv(sym)
    if df is None or len(df) < 20:
        return None
    ha_c = (df["open"] + df["close"] + df["high"] + df["low"]) / 4
    ha_o = ha_c.copy()
    ha_o.iloc[0] = df["open"].iloc[0]
    for i in range(1, len(df)):
        ha_o.iloc[i] = (ha_o.iloc[i - 1] + ha_c.iloc[i - 1]) / 2
    combo = pd.concat([ha_o, ha_c, df["high"], df["low"]], axis=1)
    ha_h = combo.max(axis=1)
    ha_l = combo.min(axis=1)
    body = (ha_o - ha_c).abs()
    entry = ((ha_o > ha_c) & np.isclose(ha_o, ha_h) &
             (body > body.shift(1)) & (ha_o.shift(1) > ha_c.shift(1)))
    ex = ((ha_o < ha_c) & np.isclose(ha_o, ha_l) & (ha_o.shift(1) < ha_c.shift(1)))
    pos = pd.Series(np.nan, index=df.index)
    pos[entry] = 1.0
    pos[ex] = 0.0
    pos = pos.ffill().fillna(0).shift(1).fillna(0)
    r = df["close"].pct_change().fillna(0)
    strat = pos * r
    turnover = pos.diff().abs().fillna(pos)
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = df["close"] / float(df["close"].iloc[0])
    return equity, bench, {"进场次数": int(entry.sum()), "单边成本": cost}


def backtest_london_breakout(sym="510300.SS", lookback=5, cost=0.0005):
    """伦敦突破（日线版）：开盘 ± 前 N 日平均振幅，突破追入"""
    df = _ohlcv(sym)
    if df is None or len(df) < int(lookback) + 5:
        return None
    rng = (df["high"] - df["low"]).rolling(int(lookback)).mean().shift(1)
    upper = df["open"] + rng
    lower = df["open"] - rng
    pos = pd.Series(np.nan, index=df.index)
    pos[df["close"] > upper] = 1.0
    pos[df["close"] < lower] = 0.0
    pos = pos.ffill().fillna(0).shift(1).fillna(0)
    r = df["close"].pct_change().fillna(0)
    strat = pos * r
    turnover = pos.diff().abs().fillna(pos)
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = df["close"] / float(df["close"].iloc[0])
    return equity, bench, {"区间回看": int(lookback), "单边成本": cost}


def backtest_sar(sym="510300.SS", af_start=0.02, af_step=0.02, af_max=0.2, cost=0.0005):
    """抛物线 SAR：Wilder 加速因子（0.02 起步，每创新高 +0.02，上限 0.2）趋势跟踪"""
    df = _ohlcv(sym)
    if df is None or len(df) < 10:
        return None
    high, low, close = df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    sar = np.zeros(n)
    ep = np.zeros(n)
    af = np.zeros(n)
    trend = np.zeros(n)
    trend[0] = 1
    sar[0] = low[0]
    ep[0] = high[0]
    af[0] = af_start
    for i in range(1, n):
        sar[i] = sar[i - 1] + af[i - 1] * (ep[i - 1] - sar[i - 1])
        if trend[i - 1] > 0:
            if i >= 2:
                sar[i] = min(sar[i], low[i - 1], low[i - 2])
            if high[i] > ep[i - 1]:
                ep[i], af[i] = high[i], min(af[i - 1] + af_step, af_max)
            else:
                ep[i], af[i] = ep[i - 1], af[i - 1]
            if low[i] < sar[i]:
                trend[i] = -1
                sar[i] = ep[i - 1]
                ep[i], af[i] = low[i], af_start
            else:
                trend[i] = 1
        else:
            if i >= 2:
                sar[i] = max(sar[i], high[i - 1], high[i - 2])
            if low[i] < ep[i - 1]:
                ep[i], af[i] = low[i], min(af[i - 1] + af_step, af_max)
            else:
                ep[i], af[i] = ep[i - 1], af[i - 1]
            if high[i] > sar[i]:
                trend[i] = 1
                sar[i] = ep[i - 1]
                ep[i], af[i] = high[i], af_start
            else:
                trend[i] = -1
    pos = pd.Series((trend > 0).astype(float), index=df.index).shift(1).fillna(0)
    r = df["close"].pct_change().fillna(0)
    strat = pos * r
    turnover = pos.diff().abs().fillna(pos)
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = df["close"] / float(df["close"].iloc[0])
    return equity, bench, {"加速因子": "{}/{}（上限 {}）".format(af_start, af_step, af_max), "单边成本": cost}


def backtest_shooting_star(sym="510300.SS", ratio=2.0, cost=0.0005):
    """射击之星：上影线 ≥ ratio×实体 → 反转离场，突破星形高点后恢复持仓"""
    df = _ohlcv(sym)
    if df is None or len(df) < 10:
        return None
    body = (df["close"] - df["open"]).abs()
    upper_wick = df["high"] - np.maximum(df["open"], df["close"])
    star = (upper_wick >= ratio * body) & (body > 0)
    exit_high = df["high"].where(star).ffill()
    pos = ((~star) | (df["close"] > exit_high)).astype(float)
    pos[star] = 0.0
    pos = pos.shift(1).fillna(1.0)
    r = df["close"].pct_change().fillna(0)
    strat = pos * r
    turnover = pos.diff().abs().fillna(pos)
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = df["close"] / float(df["close"].iloc[0])
    return equity, bench, {"上影/实体比": ratio, "星形次数": int(star.sum()), "单边成本": cost}


def backtest_pair(a="510300.SS", b="513100.SS", window=60, entry_z=2.0, exit_z=0.0, cost=0.0005):
    """配对交易（简化版）：滚动 β 构建价差 + z 分数均值回归，含做空对冲（纸面回测）
    源仓库用 Engle-Granger 协整检验；这里用滚动回归近似，教学为主"""
    df = _aligned([a, b])
    if df is None or len(df) < int(window) + 10:
        return None
    ra = df[a].pct_change()
    rb = df[b].pct_change()
    beta = ra.rolling(int(window)).cov(rb) / rb.rolling(int(window)).var()
    spread = df[a] - beta * df[b]
    mu = spread.rolling(int(window)).mean()
    sd = spread.rolling(int(window)).std().replace(0, np.nan)
    z = (spread - mu) / sd
    pos_a = pd.Series(np.nan, index=df.index)
    pos_a[z < -entry_z] = 1.0
    pos_a[z > entry_z] = -1.0
    pos_a[z.abs() < exit_z] = 0.0
    pos_a = pos_a.ffill().fillna(0).shift(1).fillna(0)
    pos_b = -pos_a
    strat = pos_a * ra.fillna(0) + pos_b * rb.fillna(0)
    turnover = pos_a.diff().abs().fillna(pos_a.abs()) + pos_b.diff().abs().fillna(pos_b.abs())
    strat = strat - turnover * cost
    equity = (1 + strat).cumprod()
    bench = (df / df.iloc[0]).mean(axis=1)
    return equity, bench, {"回归窗口": int(window), "进场z": entry_z, "出场z": exit_z,
                           "含做空对冲（纸面）": True, "单边成本": cost}


def _ohlcv(sym):
    close = load_latest(sym)
    if close is None:
        return None
    df = close.to_frame(name="close")
    p = os.path.join(os.path.expanduser("~"), ".oxq", "data", "market", sym + ".parquet")
    if os.path.exists(p):
        import pandas as _pd
        raw = _pd.read_parquet(p)
        for col in ["open", "high", "low"]:
            if col in raw.columns:
                df[col] = raw[col].reindex(close.index)
    for col in ["open", "high", "low"]:
        if col not in df.columns:
            df[col] = close
    return df


def _w_momentum(hist, r, lookback=20):
    mom = hist.iloc[-1] / hist.iloc[-min(lookback, len(hist))] - 1
    w = pd.Series(0.0, index=hist.columns)
    w[mom.idxmax()] = 1.0
    return w


def _default_params(strategy):
    spec = next(s[4] for s in STRATEGIES if s[0] == strategy)
    out = {}
    for k, v in spec.items():
        out[k] = v[4]  # default
    return out


def run(strategy, syms=("510300.SS",), params=None, cost=0.0005):
    """统一入口：返回 dict(equity, bench, metrics, meta) 或 None(数据不足)
    params: 策略参数 dict（缺省用默认值）"""
    p = _default_params(strategy)
    if params:
        p.update({k: v for k, v in params.items() if v is not None})
    try:
        if strategy == "dca":
            equity, bench, meta = backtest_dca(syms[0], monthly=int(p.get("monthly", 1000)))
        elif strategy == "ma_timing":
            equity, bench, meta = backtest_ma(syms[0], window=int(p.get("window", 20)), cost=cost)
        elif strategy == "macd":
            equity, bench, meta = backtest_macd(syms[0], fast=p.get("fast", 12),
                                                slow=p.get("slow", 26), cost=cost)
        elif strategy == "rsi":
            equity, bench, meta = backtest_rsi(syms[0], window=p.get("window", 14),
                                               oversold=p.get("oversold", 30),
                                               overbought=p.get("overbought", 70), cost=cost)
        elif strategy == "bollinger":
            equity, bench, meta = backtest_bollinger(syms[0], window=p.get("window", 20),
                                                     n_std=p.get("n_std", 2.0), cost=cost)
        elif strategy == "dual_thrust":
            equity, bench, meta = backtest_dual_thrust(syms[0], lookback=p.get("lookback", 10),
                                                       k=p.get("k", 0.5), cost=cost)
        elif strategy == "awesome":
            equity, bench, meta = backtest_awesome(syms[0], fast=p.get("fast", 5),
                                                   slow=p.get("slow", 34), cost=cost)
        elif strategy == "heikin_ashi":
            equity, bench, meta = backtest_heikin_ashi(syms[0], cost=cost)
        elif strategy == "london_breakout":
            equity, bench, meta = backtest_london_breakout(syms[0], lookback=p.get("lookback", 5), cost=cost)
        elif strategy == "sar":
            equity, bench, meta = backtest_sar(syms[0], af_start=0.02, af_step=0.02, af_max=0.2, cost=cost)
        elif strategy == "shooting_star":
            equity, bench, meta = backtest_shooting_star(syms[0], ratio=p.get("ratio", 2.0), cost=cost)
        elif strategy == "pair_trading":
            equity, bench, meta = backtest_pair(syms[0], syms[1] if len(syms) > 1 else "513100.SS",
                                                window=p.get("window", 60),
                                                entry_z=p.get("entry_z", 2.0),
                                                exit_z=p.get("exit_z", 0.0), cost=cost)
        elif strategy == "equal_weight":
            equity, bench, meta = backtest_combo(list(syms), _w_equal, cost=cost)
        elif strategy == "risk_parity":
            equity, bench, meta = backtest_combo(list(syms), _w_risk_parity, cost=cost)
        elif strategy == "momentum":
            equity, bench, meta = backtest_combo(
                list(syms), lambda h, r: _w_momentum(h, r, int(p.get("window", 20))), cost=cost)
        else:
            return None
        if equity is None or len(equity) < 30:
            return None
        m = metrics(equity)
        if strategy == "dca" and meta.get("总投入"):
            # DCA 的总收益 = 终值/总投入 - 1（分母是累计投入而非首期金额）
            total2 = float(equity.iloc[-1] / meta["总投入"] - 1)
            years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)
            m["total"] = total2
            m["cagr"] = float((1 + total2) ** (1 / years) - 1)
            m["sharpe"] = float(m["cagr"] / m["vol"]) if m["vol"] > 0 else 0.0
            m["calmar"] = float(m["cagr"] / abs(m["max_dd"])) if m["max_dd"] < 0 else 0.0
        bm = metrics(bench)
        return {"equity": equity, "bench": bench, "metrics": m,
                "bench_metrics": bm, "meta": meta}
    except Exception:
        return None


# 参数规格: (标签, 类型, min, max, 默认)
# ---------------------------------------------------------------- 策略系列课
# 每个策略配一张知识卡：是什么 / 怎么调参 / 何时失效
STRATEGY_GUIDES = {
    "dca": {
        "desc": "定投：每月固定金额买入，不看涨跌机械执行。最简单的策略，也是第 1 章实验 1。",
        "logic": "价格低时同样金额买到更多份额，价格高时买得更少——摊平成本，避开一次性买在最高点。",
        "params": "每月金额：量力而行，实验场里对比 500/1000/5000 的差异不大（比例一样）。",
        "weakness": "长期单边下跌市场会持续亏损；大牛市里跑输一次性买入（因为子弹分月打出去了）。",
    },
    "ma_timing": {
        "desc": "均线择时：收盘价在均线上方持有，下方空仓。第 1 章实验 3 的机械化。",
        "logic": "MA20 抹平噪音留下趋势方向——价格在均线上=短期强于近月平均。",
        "params": "窗口越小越灵敏也越容易被骗（假信号多）；越大越迟钝但信号稳。",
        "weakness": "震荡市反复'卖出→买回'被锯齿；趋势反转时信号滞后（均线是滞后指标）。",
    },
    "macd": {
        "desc": "MACD 金叉：快线 MA 上穿慢线 MA 买入，下穿卖出。经典动量指标，移植自 quant-trading。",
        "logic": "快线代表近期动量，慢线代表中期趋势——金叉=动量转强。",
        "params": "经典 12/26（两周 vs 一月）；周期越短越灵敏。",
        "weakness": "震荡市假金叉多；慢线太长反应迟钝，大跌初期还在持仓。",
    },
    "rsi": {
        "desc": "RSI 超买超卖：RSI 低于超卖线买入（低吸），高于超买线卖出（高抛）。",
        "logic": "RSI 衡量近期涨跌力度，30/70 是经典分界——超卖=跌过头，超买=涨过头。",
        "params": "周期 14 是 Wilder 经典；超卖/超买线可放宽（20/80 更保守）。",
        "weakness": "强趋势中 RSI 长期超买还继续涨（钝化）——低吸高抛在趋势市里是接飞刀。",
    },
    "bollinger": {
        "desc": "布林带均值回归：价格触下轨买入、触上轨卖出——赌价格回到均值。",
        "logic": "布林带 = 均线 ± 2σ，约 95% 的价格落带内——触轨=偏离均值过多。",
        "params": "窗口 20 经典；标准差倍数越大带越宽，触发越少。",
        "weakness": "趋势市里触轨后继续走（'落刀'效应）——均值回归只在震荡市有效。",
    },
    "dual_thrust": {
        "desc": "双推力突破：今日开盘 ± K×前 N 日区间，突破追入。经典日内突破策略的日线版。",
        "logic": "区间 = 前 N 日最高/最低/收盘的组合振幅；价格突破上沿=多方发力。",
        "params": "K 越大阈值越宽触发越少；回看越大区间越稳定。",
        "weakness": "假突破频繁（低波动后突然放大）；日线版无法捕捉日内反转。",
    },
    "awesome": {
        "desc": "神奇振荡器：EMA 双均线 + AO 双均线（中价 5/34）双确认做多。",
        "logic": "两个动量信号同时转强才进场——减少单一指标假信号。",
        "params": "快线 5 / 慢线 34 是 Bill Williams 原版参数。",
        "weakness": "双确认 = 更保守也更容易错过启动点；趋势钝化期信号滞后。",
    },
    "heikin_ashi": {
        "desc": "Heikin-Ashi 趋势蜡烛：把 OHLC 平滑成'平均蜡烛'，按四条件识别趋势启动。",
        "logic": "HA 蜡烛滤掉噪音，实体方向 = 趋势方向；四条件确认后进场（忠实移植源仓库）。",
        "params": "无参数——纯规则策略，适合观察，不适合微调。",
        "weakness": "横盘时假信号多；平滑导致进出场都滞后。",
    },
    "london_breakout": {
        "desc": "伦敦突破：开盘 ± 前 N 日平均振幅，突破追入。经典开盘区间突破的日线版。",
        "logic": "开盘价是全天多空均衡点——突破开盘区间 = 一方发力。",
        "params": "区间回看越大，振幅越平滑。",
        "weakness": "低波动日振幅小、假突破多；高开低走的日子追高被套。",
    },
    "sar": {
        "desc": "抛物线 SAR：止损点跟随价格移动（加速因子 0.02 起步），趋势跟踪。",
        "logic": "SAR 点像'卫星轨道'贴着价格：多头时在下方托底，跌破即离场。",
        "params": "加速因子 0.02/0.02/0.2 是 Wilder 经典——越创新高，止损跟得越紧。",
        "weakness": "横盘时 SAR 反复上下翻转（来回止损）；单边反转初期离场慢。",
    },
    "shooting_star": {
        "desc": "射击之星：上影线 ≥ 2× 实体 = 上方抛压重，离场信号（本实验场为多头出场版）。",
        "logic": "射击之星出现在上涨后 = 卖方开始发力，价格可能反转。",
        "params": "上影/实体比越高，信号越严格（触发越少）。",
        "weakness": "强趋势中射击之星频繁出现但价格继续涨；单独使用胜率有限。",
    },
    "pair_trading": {
        "desc": "配对交易：两只资产价差偏离均值过多时，做多弱的、做空强的（纸面含对冲）。",
        "logic": "长期同涨同跌的资产（如沪深300 vs 纳指），价差偏离后会回归——赌回归不赌方向。",
        "params": "回归窗口 60 日算 β 和 z 分数；进场 z 阈值越高信号越少但越确定。",
        "weakness": "协整关系会破裂（基本面变化）——价差偏离后不回归，就是接飞刀；含做空仅纸面。",
    },
    "equal_weight": {
        "desc": "等权组合：每月再平衡回 1/N 比例。第 3 章实验 1——平均分钱。",
        "logic": "定期卖出涨多的、补入跌多的，保持每只资产'金额影响力'相等。",
        "params": "无参数——每月再平衡是唯一节奏（实验场固定每月）。",
        "weakness": "某只资产暴涨时被强制减仓（错过最猛一段）；再平衡有交易成本。",
    },
    "risk_parity": {
        "desc": "风险平价：权重 ∝ 1/波动率，让每份钱的风险贡献相等。第 3 章实验 2。",
        "logic": "波动小的资产分到更多钱（如沪深300 权重高于黄金）——组合波动更稳。",
        "params": "无参数——波动率加权是唯一规则（每月重算）。",
        "weakness": "低波动资产'突然'波动放大时（黑天鹅）仓位过重；牛市中跑输等权。",
    },
    "momentum": {
        "desc": "动量轮动：每月持有过去 N 日动量最强的资产。第 3 章实验 3 + 第 9 章因子实证。",
        "logic": "'强者恒强'：把资金全部押到涨得最好的资产上，每月换仓。",
        "params": "回看 20 日偏短线、60 日偏中线——书里实测动量在低波动资产上更有效。",
        "weakness": "趋势反转时满仓最弱的'前冠军'（回撤巨大）；高波动资产上 IC 为负（第 9 章）。",
    },
}

STRATEGIES = [
    ("dca", "定投（每月固定金额）", ["510300.SS"], "单资产",
     {"monthly": ("每月金额", "int", 100, 100000, 1000)}),
    ("ma_timing", "均线择时（价格 vs MA）", ["510300.SS"], "单资产",
     {"window": ("MA 窗口", "int", 5, 120, 20)}),
    ("macd", "MACD 金叉（快线上穿慢线）", ["510300.SS"], "单资产",
     {"fast": ("快线周期", "int", 5, 60, 12), "slow": ("慢线周期", "int", 10, 120, 26)}),
    ("rsi", "RSI 超买超卖（低吸高抛）", ["510300.SS"], "单资产",
     {"window": ("RSI 周期", "int", 5, 60, 14),
      "oversold": ("超卖线（买入）", "int", 5, 40, 30),
      "overbought": ("超买线（卖出）", "int", 60, 95, 70)}),
    ("bollinger", "布林带均值回归（触轨低吸高抛）", ["510300.SS"], "单资产",
     {"window": ("布林窗口", "int", 5, 120, 20),
      "n_std": ("标准差倍数", "float", 1.0, 4.0, 2.0)}),
    ("dual_thrust", "双推力突破（开盘 ±K×区间）", ["510300.SS"], "单资产",
     {"lookback": ("突破回看", "int", 5, 60, 10),
      "k": ("K 参数", "float", 0.1, 0.9, 0.5)}),
    ("equal_weight", "等权组合（每月再平衡）", ["510300.SS", "513100.SS", "518880.SS"], "组合", {}),
    ("risk_parity", "风险平价（1/波动加权）", ["510300.SS", "513100.SS", "518880.SS"], "组合", {}),
    ("momentum", "动量轮动（每月持最强）", ["510300.SS", "513100.SS", "518880.SS", "501018.SS"], "组合",
     {"window": ("动量回看", "int", 5, 120, 20)}),
    ("awesome", "神奇振荡器（EMA+AO 双确认）", ["510300.SS"], "单资产",
     {"fast": ("快线", "int", 5, 60, 5), "slow": ("慢线", "int", 10, 120, 34)}),
    ("heikin_ashi", "Heikin-Ashi 趋势蜡烛", ["510300.SS"], "单资产", {}),
    ("london_breakout", "伦敦突破（开盘区间突破）", ["510300.SS"], "单资产",
     {"lookback": ("区间回看", "int", 1, 20, 5)}),
    ("sar", "抛物线 SAR（趋势跟踪）", ["510300.SS"], "单资产", {}),
    ("shooting_star", "射击之星（反转出场）", ["510300.SS"], "单资产",
     {"ratio": ("上影/实体比", "float", 1.0, 4.0, 2.0)}),
    ("pair_trading", "配对交易（滚动β z分数）", ["510300.SS", "513100.SS"], "配对",
     {"window": ("回归窗口", "int", 20, 120, 60),
      "entry_z": ("进场 z 阈值", "float", 1.0, 3.0, 2.0)}),
]
