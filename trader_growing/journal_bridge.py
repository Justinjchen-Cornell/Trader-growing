# -*- coding: utf-8 -*-
"""修行日记对接：读取日记 JSON -> DailyRecord

日记目录：~/.claude/skills/trader-cultivation-journal/diary/（可配置）
"""
import os, json, glob

from .models import DailyRecord


def diary_dir():
    env = os.environ.get("TRADER_DIARY_DIR")
    if env:
        return env
    return os.path.join(os.path.expanduser("~"), ".claude", "skills",
                        "trader-cultivation-journal", "diary")


def _to_record(d):
    tb = d.get("trades_today") or {}
    return DailyRecord(
        date=d.get("date", ""),
        mode=d.get("mode", "evening"),
        math=d.get("math", {}).get("score", 0) if isinstance(d.get("math"), dict) else d.get("math", 0),
        finance=d.get("finance", {}).get("score", 0) if isinstance(d.get("finance"), dict) else d.get("finance", 0),
        psychology=d.get("psychology", {}).get("score", 0) if isinstance(d.get("psychology"), dict) else d.get("psychology", 0),
        philosophy=d.get("philosophy", {}).get("score", 0) if isinstance(d.get("philosophy"), dict) else d.get("philosophy", 0),
        overall=d.get("overall", 0),
        notes=d.get("notes", ""),
        trades_today=tb,
        discipline_suggestion=d.get("discipline_suggestion", ""),
    )


def load_latest():
    """加载最新一天日记 -> DailyRecord 或 None"""
    files = sorted(glob.glob(os.path.join(diary_dir(), "*.json")))
    if not files:
        return None
    with open(files[-1], encoding="utf-8") as f:
        return _to_record(json.load(f))


def load_all():
    """加载全部日记 -> [DailyRecord]"""
    recs = []
    for fp in sorted(glob.glob(os.path.join(diary_dir(), "*.json"))):
        try:
            with open(fp, encoding="utf-8") as f:
                recs.append(_to_record(json.load(f)))
        except (json.JSONDecodeError, OSError):
            continue
    return recs
