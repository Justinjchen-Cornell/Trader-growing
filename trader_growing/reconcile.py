# -*- coding: utf-8 -*-
"""纪律对账核心：策略计划 vs 日记实际执行"""
from .models import ReconcileResult


def reconcile(plan, record):
    tb = record.trades_today or {}
    issues = []
    if plan and tb.get("traded_today") and plan.signal in ("FORCE_EMPTY", "STAY_EMPTY", "HOLD"):
        issues.append("计划外交易：策略建议「{}」，但今天发生了交易".format(plan.action))
    if tb.get("impulse_trade"):
        issues.append("冲动交易：有计划外开仓/加仓（违反数学维度纪律）")
    if tb.get("moved_stop_loss"):
        issues.append("手动移动止损线（违反金融维度纪律）")
    if tb.get("traded_today") and tb.get("followed_plan") is False:
        issues.append("交易未严格按计划执行")
    return ReconcileResult(date=record.date,
                           plan_signal=plan.signal if plan else None,
                           plan_action=plan.action if plan else None,
                           issues=issues, clean=len(issues) == 0)
