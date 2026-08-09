# -*- coding: utf-8 -*-
"""数据模型：日记记录 / 策略计划 / 对账报告"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class DailyRecord:
    date: str
    mode: str = "evening"
    math: float = 0.0
    finance: float = 0.0
    psychology: float = 0.0
    philosophy: float = 0.0
    overall: float = 0.0
    notes: str = ""
    trades_today: Optional[dict] = None
    discipline_suggestion: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class Plan:
    date: str
    asset: str
    symbol: str
    signal: str
    cap: float
    action: str
    close: float
    stop_loss_line: float
    advice: str = ""


@dataclass
class ReconcileResult:
    date: str
    plan_signal: Optional[str] = None
    plan_action: Optional[str] = None
    issues: list = field(default_factory=list)
    clean: bool = True

    def to_report(self):
        lines = ["=" * 50, "  纪律对账报告（Trader-growing）", "=" * 50]
        if self.plan_signal:
            lines.append("  策略计划: {} | {}".format(self.plan_signal, self.plan_action))
        if self.issues:
            lines.append("  偏差:")
            for it in self.issues:
                lines.append("    - " + it)
        else:
            lines.append("  通过: 无偏差，纪律良好")
        return "\n".join(lines)
