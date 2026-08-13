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
]
