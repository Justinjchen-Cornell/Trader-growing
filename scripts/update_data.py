# -*- coding: utf-8 -*-
"""一键更新行情数据：Wind / akshare 双源（parquet -> ~/.oxq/data/market/）

用法:
  python scripts/update_data.py                  # 自动选源：有 Wind skill 用 Wind，否则 akshare
  python scripts/update_data.py --source akshare # 强制 akshare（免费，无需注册）
  python scripts/update_data.py --source wind    # 强制 Wind
  python scripts/update_data.py 2026-08-09       # 指定截止日期

覆盖资产：
  4 只 ETF/LOF（沪深300 / 纳指100 / 黄金 / 原油）+ 5 只个股（茅台/五粮液/招行/平安/平银）
  ——个股数据是第 2 章关卡（个股 vs ETF）的素材，必须一起更新

akshare 说明：
  - ETF 走东财 fund_etf_hist_em，个股走新浪 stock_zh_a_daily（稳定性更好）
  - 某资产失败时保留本地旧数据并给出提示（网络不稳时重跑即可）
"""
import sys, os, json, subprocess, glob, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
from pathlib import Path

# (本地文件名, Wind代码, 名称, 类型)
ASSETS = [
    ("510300.SS", "510300.SH", "沪深300ETF", "etf"),
    ("513100.SS", "513100.SH", "纳指100ETF", "etf"),
    ("518880.SS", "518880.SH", "黄金ETF", "etf"),
    ("501018.SS", "501018.SH", "原油LOF", "lof"),
    ("600519.SS", "600519.SH", "贵州茅台", "stock"),
    ("000858.SZ", "000858.SZ", "五粮液", "stock"),
    ("600036.SS", "600036.SH", "招商银行", "stock"),
    ("601318.SS", "601318.SH", "中国平安", "stock"),
    ("000001.SZ", "000001.SZ", "平安银行", "stock"),
]
START = "2021-01-01"

DATA_DIR = Path.home() / ".oxq" / "data" / "market"


def find_wind_skill():
    env = os.environ.get("WIND_SKILL_DIR")
    if env:
        return env
    candidates = [
        os.path.join(os.path.expanduser("~"), ".agents", "skills", "wind-mcp-skill"),
        os.path.join(os.path.expanduser("~"), ".claude", "skills", "wind-mcp-skill"),
        os.path.join(os.path.expanduser("~"), "Documents", "陈嘉-资料备份", "04.SecurityAI",
                     "00.GitHub", "xquant-beginner-main", ".agents", "skills", "wind-mcp-skill"),
    ]
    for c in candidates:
        if os.path.exists(os.path.join(c, "scripts", "cli.mjs")):
            return c
    return None


def _normalize(df):
    ren = {"日期": "date", "开盘": "open", "收盘": "close", "最高": "high",
           "最低": "low", "成交量": "volume"}
    df = df.rename(columns=ren)
    keep = [c for c in ["date", "open", "close", "high", "low", "volume"] if c in df.columns]
    df = df[keep]
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    for c in ["open", "close", "high", "low"]:
        df[c] = df[c].astype(float)
    df["volume"] = df["volume"].fillna(0).astype(float)
    return df


def fetch_akshare(sym, atype, start, end):
    """akshare 拉取，返回 DataFrame(date/open/close/high/low/volume) 或抛异常

    数据源优先级：
      个股 -> 新浪 stock_zh_a_daily（稳定）
      ETF/LOF -> 东财 fund_etf_hist_em -> 失败回退新浪 fund_etf_hist_sina
    """
    import akshare as ak
    code = sym.split(".")[0]
    s, e = start.replace("-", ""), end.replace("-", "")
    if atype == "stock":
        prefix = "sh" if sym.endswith(".SS") else "sz"
        df = ak.stock_zh_a_daily(symbol=prefix + code, start_date=s, end_date=e, adjust="qfq")
        if df is None or len(df) == 0:
            raise RuntimeError("空数据")
        return _normalize(df)
    # ETF / LOF：先东财，失败回退新浪
    last_err = None
    try:
        if atype == "etf":
            df = ak.fund_etf_hist_em(symbol=code, period="daily", start_date=s, end_date=e, adjust="qfq")
        else:
            df = ak.fund_lof_hist_em(symbol=code, period="daily", start_date=s, end_date=e, adjust="qfq")
        if df is None or len(df) == 0:
            raise RuntimeError("空数据")
        return _normalize(df)
    except Exception as e:
        last_err = e
    prefix = "sh" if sym.endswith(".SS") else "sz"
    df = ak.fund_etf_hist_sina(symbol=prefix + code)
    if df is None or len(df) == 0:
        raise RuntimeError("新浪空数据（东财失败: {}）".format(str(last_err)[:80]))
    return _normalize(df)


def fetch_akshare_retry(sym, atype, start, end, tries=3):
    last = None
    for t in range(tries):
        try:
            return fetch_akshare(sym, atype, start, end), None
        except Exception as e:
            last = e
            time.sleep(2 * (t + 1))
    return None, str(last)[:120]


def to_parquet(df, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_parquet(out_path)
    return len(df)


def fetch_wind(skill_dir, wind_code, start, end, tmp_json):
    cli = os.path.join(skill_dir, "scripts", "cli.mjs")
    params = json.dumps({"windcode": wind_code, "begin_date": start, "end_date": end,
                         "period": "1d", "aftype": "0"})
    r = subprocess.run(["node", cli, "call", "fund_data", "get_fund_kline", params],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None, "Wind 调用失败: {}".format(r.stderr[-200:])
    with open(tmp_json, "w", encoding="utf-8") as f:
        f.write(r.stdout)
    try:
        d = json.load(open(tmp_json, encoding="utf-8"))
        if "content" not in d:
            return None, "Wind 返回错误: {}".format(json.dumps(d.get("error", {}), ensure_ascii=False)[:150])
        return d, None
    except (json.JSONDecodeError, OSError) as e:
        return None, "解析失败: {}".format(e)


def wind_to_df(wind_json):
    t = json.loads(wind_json["content"][0]["text"])
    rows = t["data"]["rows"]
    recs = []
    for r in rows:
        vol = r[6] if r[6] is not None else 0
        recs.append({"date": r[0][:10], "open": float(r[1]), "close": float(r[2]),
                     "high": float(r[3]), "low": float(r[4]), "volume": int(float(vol))})
    df = pd.DataFrame(recs)
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()


def main():
    argv = [a for a in sys.argv[1:]]
    end = "2026-12-31"
    source = "auto"
    rest = []
    for a in argv:
        if a.startswith("--source="):
            source = a.split("=", 1)[1]
        elif a == "--source":
            pass  # 取下一个
        elif a in ("wind", "akshare", "auto"):
            rest.append(a)
        elif a.startswith("--source"):
            pass
        elif a.startswith("20") and "-" in a:
            end = a
        else:
            rest.append(a)
    if rest and rest[-1] in ("wind", "akshare", "auto"):
        source = rest[-1]

    skill_dir = find_wind_skill() if source != "akshare" else None
    if source == "auto":
        source = "wind" if skill_dir else "akshare"

    print("=" * 55)
    if source == "wind" and skill_dir:
        print("  数据源: Wind（skill: {}）".format(skill_dir))
    elif source == "akshare":
        print("  数据源: akshare（免费，无需注册）")
    else:
        print("  数据源: Wind 未找到 → 请先安装 Wind skill，或用 --source akshare")
        print("  Wind 安装指引见 docs/WIND_SETUP.md")
        return 1
    print("  资产 {} 只 | 区间 {} ~ {}".format(len(ASSETS), START, end))
    print("=" * 55)

    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "_tmp_wind.json")
    ok, fail = 0, []
    for yf_sym, wind_code, name, atype in ASSETS:
        out = DATA_DIR / (yf_sym + ".parquet")
        if source == "wind" and skill_dir:
            d, err = fetch_wind(skill_dir, wind_code, START, end, tmp)
            if err:
                fail.append((name, err))
                continue
            df = wind_to_df(d)
            n = to_parquet(df, str(out))
            print("  {}: ✅ Wind {} 行 -> {}".format(name, n, out))
            ok += 1
        else:
            df, err = fetch_akshare_retry(yf_sym, atype, START, end)
            if err or df is None:
                keep = "（保留本地旧数据）" if out.exists() else "（无本地数据！）"
                fail.append((name, err))
                print("  {}: ❌ {} {}".format(name, err, keep))
                continue
            n = to_parquet(df, str(out))
            print("  {}: ✅ akshare {} 行 -> {}".format(name, n, out))
            ok += 1

    if os.path.exists(tmp):
        os.remove(tmp)
    print("=" * 55)
    print("  完成: {}/{} 成功".format(ok, len(ASSETS)))
    if fail:
        print("  失败资产（可稍后重跑本命令）:")
        for n, e in fail:
            print("    - {}: {}".format(n, e))
    print("  查看: python scripts/tg.py dashboard")

    return 0 if not fail else 2


if __name__ == "__main__":
    sys.exit(main())
