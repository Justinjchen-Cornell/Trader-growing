# -*- coding: utf-8 -*-
"""四资产看板：金 / 油 / 沪深300 / 纳指 每日行情 + 轻信号

数据源：~/.oxq/data/market/*.parquet（open-xquant 本地数据，可用 Wind/akshare 更新）
轻信号：MA20 趋势方向 + 20 日动量 + 20 日波动率（重信号由中庸策略 plan 提供）
"""
import os, glob
from datetime import date

import pandas as pd
import numpy as np

ASSETS = [
    ("510300.SS", "沪深300", "A股"),
    ("513100.SS", "纳指100", "QDII"),
    ("518880.SS", "黄金", "避险"),
    ("501018.SS", "原油", "商品"),
]


def _data_dir():
    return os.path.join(os.path.expanduser("~"), ".oxq", "data", "market")


def load_latest(symbol):
    """读取某资产最新一段数据（返回 close Series）"""
    p = os.path.join(_data_dir(), symbol + ".parquet")
    if not os.path.exists(p):
        return None
    df = pd.read_parquet(p)
    close = df["close"].dropna()
    return close


def common_close(syms):
    """多资产对齐：取所有资产共有日期的 close，返回 {sym: Series}"""
    series = {}
    for sym in syms:
        close = load_latest(sym)
        if close is None:
            return None
        series[sym] = close
    idx = series[syms[0]].index
    for sym in syms[1:]:
        idx = idx.intersection(series[sym].index)
    return {sym: series[sym].loc[idx] for sym in syms}


def window_ret(close, days=252):
    """区间收益率（最近 days 个交易日，不含今天按比例折算）"""
    if close is None or len(close) < 2:
        return None
    ref = close.iloc[-(days + 1)] if len(close) > days else close.iloc[0]
    return float(close.iloc[-1] / ref - 1)


def annualized_vol(close, days=252):
    """年化波动率（最近 days 个交易日日收益 std × √252）"""
    if close is None or len(close) < 30:
        return None
    return float(close.pct_change().tail(days).std() * np.sqrt(252))


def pair_corr(close_a, close_b, days=252):
    """两资产日收益相关性（最近 days 个交易日）"""
    if close_a is None or close_b is None or len(close_a) < 30 or len(close_b) < 30:
        return None
    ra = close_a.pct_change().tail(days)
    rb = close_b.pct_change().tail(days)
    j = ra.index.intersection(rb.index)
    if len(j) < 30:
        return None
    return float(ra.loc[j].corr(rb.loc[j]))


def signal_for(close):
    """轻信号：MA20 趋势 + 动量方向"""
    if close is None or len(close) < 60:
        return None, "数据不足"
    ma20 = close.rolling(20).mean()
    last = close.iloc[-1]
    ma = ma20.iloc[-1]
    mom20 = last / close.iloc[-21] - 1 if len(close) > 21 else 0
    vol20 = close.pct_change().tail(20).std() * np.sqrt(252)
    if last > ma:
        sig, tone = "多头 (MA20上方)", "up"
    else:
        sig, tone = "空头 (MA20下方)", "down"
    return {"signal": sig, "tone": tone, "mom20": mom20, "vol20": vol20,
            "close": last, "ma20": ma, "date": str(close.index[-1].date())}, None


def build_dashboard():
    rows = []
    for sym, name, tag in ASSETS:
        close = load_latest(sym)
        info, err = signal_for(close)
        if err:
            rows.append({"资产": name, "标签": tag, "状态": err})
            continue
        rows.append({
            "资产": name, "标签": tag,
            "收盘": round(info["close"], 3),
            "MA20": round(info["ma20"], 3),
            "趋势": info["signal"],
            "20日动量": "{:+.1%}".format(info["mom20"]),
            "年化波动": "{:.0%}".format(info["vol20"]),
            "数据至": info["date"],
        })
    return pd.DataFrame(rows)


def print_dashboard():
    df = build_dashboard()
    print()
    print("  🌍 Trader-growing · 四资产看板（{}）".format(date.today()))
    print("  " + "=" * 90)
    if len(df) == 0:
        print("  ⚠️ 未找到本地数据（~/.oxq/data/market/*.parquet）")
        print("  提示：可用 Wind 下载后存为 parquet，或用 akshare 更新")
        return
    print(df.to_string(index=False))
    print("  " + "=" * 90)
    print("  说明：趋势 = 轻信号(MA20)；重信号见'今日策略计划'(plan)")


if __name__ == "__main__":
    print_dashboard()
