#!/usr/bin/env python3
"""Shared helpers for evolution event schema/logging."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
LOG_FILE = MEMORY_DIR / "evolution-log.jsonl"
TZ_SH = timezone(timedelta(hours=8))
LEVELS = ["pcec", "ppec", "piec", "psec"]
EVENT_TYPES = ["evaluation", "evolution", "decision", "lesson"]


def now_iso_shanghai() -> str:
    return datetime.now(TZ_SH).isoformat()


def normalize_level(level: str | None) -> str | None:
    if level == "pcpec":
        return "pcec"
    return level


def ensure_log_file() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.touch()


def parse_iso_flexible(ts: str | None):
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ_SH)
        return dt.astimezone(TZ_SH)
    except Exception:
        return None


def normalize_event(raw: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    ts = raw.get("ts") or raw.get("timestamp")
    dt = parse_iso_flexible(ts)
    ts_norm = dt.isoformat() if dt else now_iso_shanghai()

    level = normalize_level(raw.get("level"))
    event_type = raw.get("type")
    source = raw.get("source")
    task_id = raw.get("task_id")
    tags = raw.get("tags") or []
    if not isinstance(tags, list):
        tags = [str(tags)]

    if "data" in raw and isinstance(raw.get("data"), dict):
        data = raw.get("data", {})
    elif "dimensions" in raw:
        data = dict(raw.get("dimensions") or {})
        for key in ("overall", "feedback", "weaknesses", "evolution_suggestion"):
            if key in raw:
                data[key] = raw[key]
    else:
        data = {}
        for key in ("action", "label", "result", "notes"):
            if key in raw:
                data[key] = raw[key]

    if not event_type:
        if "dimensions" in raw or raw.get("type") == "evaluation":
            event_type = "evaluation"
        elif "action" in raw:
            event_type = "evolution"
        else:
            event_type = "lesson"

    if not source:
        if event_type == "evaluation":
            source = "self-evaluator"
        elif event_type == "evolution":
            source = "evolution-trigger"
        else:
            source = "manual"

    return {
        "ts": ts_norm,
        "type": event_type,
        "level": level,
        "source": source,
        "task_id": task_id,
        "data": data,
        "tags": tags,
    }


def append_event(event_type: str, level: str, source: str, data: dict[str, Any], tags: list[str] | None = None, task_id: str | None = None) -> dict[str, Any]:
    ensure_log_file()
    event = {
        "ts": now_iso_shanghai(),
        "type": event_type,
        "level": normalize_level(level),
        "source": source,
        "task_id": task_id,
        "data": data or {},
        "tags": tags or [],
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def load_events() -> list[dict[str, Any]]:
    if not LOG_FILE.exists():
        return []
    out = []
    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            event = normalize_event(raw)
            if event:
                out.append(event)
    return list(reversed(out))
