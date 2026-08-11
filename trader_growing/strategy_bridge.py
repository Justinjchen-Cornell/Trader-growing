# -*- coding: utf-8 -*-
"""中庸策略对接：读取/生成今日交易计划

策略仓库位置可通过环境变量 TRADER_STRATEGY_DIR 配置，
默认指向 ../zhongyong_strategy（与中庸策略仓库并列时）。
"""
import os, json, sys


def strategy_dir():
    env = os.environ.get("TRADER_STRATEGY_DIR")
    if env:
        return env
    # 常见位置探测
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base, "..", "zhongyong_strategy"),
        os.path.join(os.path.expanduser("~"), "Documents", "陈嘉-资料备份", "04.SecurityAI",
                     "00.GitHub", "xquant-beginner-main", "策略", "zhongyong_strategy"),
        os.path.join(os.path.expanduser("~"), "Documents", "陈嘉-资料备份", "04.SecurityAI",
                     "00.GitHub", "Trader-growing", "zhongyong_strategy"),
    ]
    for c in candidates:
        if os.path.exists(os.path.join(c, "plan.py")):
            return c
    return candidates[0]


def default_plan_path():
    return os.path.join(strategy_dir(), "plan_today.json")


def load_plan(plan_path=None):
    """读取 plan_today.json -> dict 或 None"""
    path = plan_path or default_plan_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def generate_plan(symbol="510300.SS"):
    """调用中庸策略的 plan.py 重新生成计划（需要 PYTHONPATH 含中庸策略目录）"""
    sd = strategy_dir()
    plan_script = os.path.join(sd, "plan.py")
    if not os.path.exists(plan_script):
        return None, "未找到中庸策略 plan.py（路径: {}）".format(sd)
    sys.path.insert(0, sd)
    try:
        import plan as plan_mod
        plan_mod.main(symbol)
        return load_plan(), None
    except Exception as e:
        return None, "生成计划失败: {}".format(e)
