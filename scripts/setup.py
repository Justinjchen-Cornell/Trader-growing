# -*- coding: utf-8 -*-
"""Trader-growing 一键环境准备

用法: python scripts/setup.py

步骤:
  1. 安装 Python 依赖（requirements.txt）
  2. 检查 / 安装 Wind skill（可选数据源，缺失时给出安装命令）
  3. 检查 WIND_API_KEY（缺失时提示配置）
  4. 可选：下载首批四资产数据
"""
import sys, os, subprocess, platform
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def step(title):
    print()
    print("=" * 55)
    print("  {}".format(title))
    print("=" * 55)


def ask(msg, default=True):
    s = input("{} (y/n, 默认{}): ".format(msg, "y" if default else "n")).strip().lower()
    if not s:
        return default
    return s in ("y", "yes", "是")


def install_deps():
    step("1/4 安装 Python 依赖")
    req = os.path.join(ROOT, "requirements.txt")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-r", req],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✅ 依赖安装完成（streamlit / pandas / numpy / matplotlib / pyarrow / akshare ...）")
    else:
        print("  ⚠️ 依赖安装可能有问题: {}".format(r.stderr[-200:]))
    # 关键依赖自检（parquet 读写必需）
    try:
        import pyarrow  # noqa: F401
        print("  ✅ pyarrow 可用（parquet 读写正常）")
    except ImportError:
        print("  ❌ pyarrow 未装好——看板/学习关卡将无法读取数据！请重试 pip install -r requirements.txt")
        return False
    return r.returncode == 0


def find_wind_skill():
    candidates = [
        os.path.join(os.path.expanduser("~"), ".agents", "skills", "wind-mcp-skill"),
        os.path.join(os.path.expanduser("~"), ".claude", "skills", "wind-mcp-skill"),
    ]
    # 当前项目内
    for root, dirs, files in os.walk(os.path.join(ROOT, "..")):
        if "wind-mcp-skill" in dirs and os.path.exists(os.path.join(root, "wind-mcp-skill", "scripts", "cli.mjs")):
            return os.path.join(root, "wind-mcp-skill")
        if root.count(os.sep) - ROOT.count(os.sep) > 3:
            break
    for c in candidates:
        if os.path.exists(os.path.join(c, "scripts", "cli.mjs")):
            return c
    return None


def check_wind():
    step("2/4 Wind 数据源（可选但推荐）")
    skill = find_wind_skill()
    if skill:
        print("  ✅ Wind skill 已安装: {}".format(skill))
        return True
    print("  ⚠️ 未找到 Wind skill（用于四资产数据更新）")
    if ask("  现在安装？（需要已注册 aifinmarket.wind.com.cn）"):
        cmds = [
            "npx skills add Wind-Information-Co-Ltd/wind-skills --skill wind-find-finance-skill -y",
            "npx skills add Wind-Information-Co-Ltd/wind-skills --skill wind-mcp-skill -y",
        ]
        for c in cmds:
            print("  > " + c)
            r = subprocess.run(c, shell=True)
            if r.returncode != 0:
                print("    失败，可换 Gitee 源或手动安装（见 docs/WIND_SETUP.md）")
    else:
        print("  跳过。之后可手动安装（docs/WIND_SETUP.md），或使用 akshare/yfinance 数据")
    return False


def check_key():
    step("3/4 WIND_API_KEY")
    cfg = os.path.join(os.path.expanduser("~"), ".wind-aifinmarket", "config")
    if os.path.exists(cfg):
        with open(cfg, encoding="utf-8") as f:
            if "WIND_API_KEY=" in f.read():
                print("  ✅ 已配置（{}）".format(cfg))
                return True
    print("  ⚠️ 未找到 WIND_API_KEY（{}）".format(cfg))
    print("  获取 Key: https://aifinmarket.wind.com.cn/#/user/overview")
    if ask("  现在输入 Key 并写入配置？"):
        key = input("  WIND_API_KEY: ").strip()
        if key:
            os.makedirs(os.path.dirname(cfg), exist_ok=True)
            with open(cfg, "w", encoding="utf-8") as f:
                f.write("WIND_API_KEY=" + key)
            print("  ✅ 已写入 {}".format(cfg))
            return True
    return False


def fetch_data():
    step("4/4 首批数据")
    if ask("  下载四资产数据（金/油/沪深300/纳指）？"):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "update_data.py")])
        if r.returncode == 0:
            print("  ✅ 数据就绪")
        else:
            print("  ⚠️ 数据下载失败（检查 Wind 配置，或用 akshare 手动准备）")


def main():
    print("🌱 Trader-growing · 环境准备")
    install_deps()
    check_wind()
    check_key()
    fetch_data()
    print()
    print("=" * 55)
    print("  ✅ 环境准备完成！下一步：")
    print("  streamlit run app.py          # Web 界面")
    print("  python scripts/tg.py status   # 角色/花园")
    print("  python scripts/tg.py check    # 每日打卡")
    print("  修行日历见 docs/DAILY_RITUAL.md")
    print("=" * 55)


if __name__ == "__main__":
    main()
