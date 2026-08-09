# -*- coding: utf-8 -*-
"""一键更新四资产数据：Wind CLI -> parquet（~/.oxq/data/market/）

用法: python scripts/update_data.py [end_date]
示例: python scripts/update_data.py            # 更新到 2026-12-31
      python scripts/update_data.py 2026-08-09  # 指定截止日期

依赖:
  - Wind 金融能力 Skill（含 wind-mcp-skill 的 scripts/cli.mjs）
  - 环境变量 WIND_SKILL_DIR 可指定 skill 目录（默认自动探测）
"""
import sys, os, json, subprocess, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
from pathlib import Path

ASSETS = [
    ("510300.SS", "510300.SH", "沪深300ETF"),
    ("513100.SS", "513100.SH", "纳指100ETF"),
    ("518880.SS", "518880.SH", "黄金ETF"),
    ("501018.SS", "501018.SH", "原油LOF"),
]
START = "2021-01-01"


def find_wind_skill():
    """探测 wind-mcp-skill 目录"""
    env = os.environ.get("WIND_SKILL_DIR")
    if env:
        return env
    # 常见位置探测
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


def fetch_kline(skill_dir, wind_code, start, end, tmp_json):
    """调用 Wind CLI 下载日 K 线"""
    cli = os.path.join(skill_dir, "scripts", "cli.mjs")
    params = json.dumps({"windcode": wind_code, "begin_date": start, "end_date": end,
                         "period": "1d", "aftype": "0"})
    cmd = ["node", cli, "call", "fund_data", "get_fund_kline", params]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
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


def to_parquet(wind_json, out_path):
    t = json.loads(wind_json["content"][0]["text"])
    rows = t["data"]["rows"]
    recs = []
    for r in rows:
        vol = r[6] if r[6] is not None else 0
        recs.append({"date": r[0][:10], "open": float(r[1]), "close": float(r[2]),
                     "high": float(r[3]), "low": float(r[4]), "volume": int(float(vol))})
    df = pd.DataFrame(recs)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_parquet(out_path)
    return len(df)


def main():
    end = sys.argv[1] if len(sys.argv) > 1 else "2026-12-31"
    skill_dir = find_wind_skill()
    if not skill_dir:
        print("=" * 55)
        print("  未找到 Wind skill（数据更新需要）")
        print("=" * 55)
        print("  自助安装（2 分钟）：")
        print("  1) 注册 Wind AIFin Market 获取 API Key:")
        print("     https://aifinmarket.wind.com.cn/#/user/overview")
        print("  2) 安装两个 skill（在项目目录运行）:")
        print("     npx skills add Wind-Information-Co-Ltd/wind-skills --skill wind-find-finance-skill -y")
        print("     npx skills add Wind-Information-Co-Ltd/wind-skills --skill wind-mcp-skill -y")
        print("  3) 配置 Key（写入 ~/.wind-aifinmarket/config）:")
        print("     WIND_API_KEY=<你的Key>")
        print()
        print("  或用环境变量 WIND_SKILL_DIR 指定已安装的 skill 路径")
        print("  替代方案：用 akshare/yfinance 手动更新 ~/.oxq/data/market/*.parquet")
        print("  详细说明见 docs/WIND_SETUP.md")
        print("=" * 55)
        return 1
    print("Wind skill: {}".format(skill_dir))
    data_dir = Path.home() / ".oxq" / "data" / "market"
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "_tmp_wind.json")

    print("开始更新四资产（{} ~ {}）...".format(START, end))
    for yf_sym, wind_code, name in ASSETS:
        d, err = fetch_kline(skill_dir, wind_code, START, end, tmp)
        if err:
            print("  {}: 失败 - {}".format(name, err))
            continue
        out = data_dir / (yf_sym + ".parquet")
        n = to_parquet(d, str(out))
        print("  {}: OK - {} 行 -> {}".format(name, n, out))
    if os.path.exists(tmp):
        os.remove(tmp)
    print("完成！运行 python scripts/tg.py dashboard 查看最新看板")


if __name__ == "__main__":
    sys.exit(main())
