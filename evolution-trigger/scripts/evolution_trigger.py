#!/usr/bin/env python3
"""
evolution-trigger: 四层进化节奏控制器 CLI
pcec / ppec / piec / psec 触发检查、状态查询、事件记录
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
STATE_FILE = MEMORY_DIR / "evolution-state.json"
LOG_FILE = MEMORY_DIR / "evolution-log.jsonl"
TASK_STATUS_FILE = MEMORY_DIR / "task-status.json"

LEVELS = ["pcec", "ppec", "piec", "psec"]
LEVEL_LABELS = {
    "pcec": "PCEC（微进化）",
    "ppec": "PPEC（小进化）",
    "piec": "PIEC（中进化）",
    "psec": "PSEC（大进化）",
}

FAILED_STATES = {"failed", "error", "blocked", "cancelled", "canceled", "❌", "fail"}
DONE_STATES = {"done", "completed", "success", "finished", "✅"}
ACTIVE_STATES = {"pending", "todo", "doing", "in_progress", "in-progress", "running", "backlog"}


def _now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _this_week_start_date():
    return (datetime.now() - timedelta(days=datetime.now().weekday())).date()


def _load_state():
    if not STATE_FILE.exists():
        return {l: {"last_trigger": None, "count": 0} for l in LEVELS}
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if "pcpec" in state and "pcec" not in state:
            state["pcec"] = state.pop("pcpec")
        for l in LEVELS:
            if l not in state:
                state[l] = {"last_trigger": None, "count": 0}
        return state
    except Exception:
        return {l: {"last_trigger": None, "count": 0} for l in LEVELS}


def _save_state(state):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_dt(ts):
    if ts is None:
        return None
    try:
        raw = ts.strip()
        if not raw.endswith(("+08:00", "+00:00", "Z")):
            raw = raw + "+08:00"
        raw = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _normalize_level(level):
    return "pcec" if level == "pcpec" else level


def _normalize_status(status):
    if status is None:
        return ""
    return str(status).strip().lower()


def _extract_task_json(text: str):
    text = text.strip()
    if text.startswith("{"):
        return json.loads(text)
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if m:
        return json.loads(m.group(1))
    raise ValueError("task-status.json 中未找到可解析 JSON")


def _load_task_status():
    if not TASK_STATUS_FILE.exists():
        return []
    try:
        raw = TASK_STATUS_FILE.read_text(encoding="utf-8")
        data = _extract_task_json(raw)
    except Exception:
        return []

    if isinstance(data, dict):
        tasks = data.get("tasks") or data.get("items") or data.get("data") or []
    elif isinstance(data, list):
        tasks = data
    else:
        tasks = []
    return [t for t in tasks if isinstance(t, dict)]


def _task_date(task):
    for key in ["updatedAt", "updated_at", "completedAt", "completed_at", "createdAt", "created_at", "date"]:
        val = task.get(key)
        if not val:
            continue
        dt = _parse_dt(str(val))
        if dt:
            return dt.date()
        try:
            return datetime.fromisoformat(str(val)).date()
        except Exception:
            pass
    return None


def _task_type(task):
    for key in ["task_type", "type", "category", "source"]:
        val = task.get(key)
        if val:
            return str(val)
    return "unknown"


def _task_status_value(task):
    for key in ["status", "state", "result"]:
        if key in task:
            return _normalize_status(task.get(key))
    return ""


# ── task-status 驱动逻辑（主数据源）────────────────────────────

def _has_recent_failed_task(_state):
    tasks = _load_task_status()
    if not tasks:
        return False
    latest_failed = None
    for task in tasks:
        status = _task_status_value(task)
        if status in FAILED_STATES:
            dt = _task_date(task)
            if latest_failed is None or ((dt or datetime.min.date()) > (latest_failed or datetime.min.date())):
                latest_failed = dt
    if latest_failed is None:
        return False
    return (datetime.now().date() - latest_failed).days <= 7


def _has_task_change_today(_state):
    tasks = _load_task_status()
    today = datetime.now().date()
    for task in tasks:
        dt = _task_date(task)
        if dt == today:
            return True
    return False


def _week_task_count(_state, min_count=5):
    tasks = _load_task_status()
    week_start = _this_week_start_date()
    count = 0
    for task in tasks:
        dt = _task_date(task)
        if dt and dt >= week_start:
            count += 1
    return count >= min_count


def _week_failure_rate(_state, threshold=0.3):
    tasks = _load_task_status()
    week_start = _this_week_start_date()
    total = 0
    failed = 0
    for task in tasks:
        dt = _task_date(task)
        if dt and dt >= week_start:
            total += 1
            if _task_status_value(task) in FAILED_STATES:
                failed += 1
    if total == 0:
        return False
    return (failed / total) >= threshold


def _week_repeated_failure_type(_state, min_repeat=2):
    tasks = _load_task_status()
    week_start = _this_week_start_date()
    counts = {}
    for task in tasks:
        dt = _task_date(task)
        if dt and dt >= week_start and _task_status_value(task) in FAILED_STATES:
            t = _task_type(task)
            counts[t] = counts.get(t, 0) + 1
    return any(v >= min_repeat for v in counts.values())


# ── fallback：日记关键词（次要数据源）──────────────────────────

def _has_failures_today_fallback(_state):
    diary = WORKSPACE / "memory" / f"{_today()}.md"
    if not diary.exists():
        return False
    try:
        content = diary.read_text(encoding="utf-8")
        return "❌" in content or "失败" in content
    except IOError:
        return False


def _has_new_experience_today_fallback(_state):
    diary = WORKSPACE / "memory" / f"{_today()}.md"
    if not diary.exists():
        return False
    try:
        content = diary.read_text(encoding="utf-8")
        return "经验" in content or "教训" in content or "✅" in content
    except IOError:
        return False


def _has_decisions_today_fallback(_state):
    diary = WORKSPACE / "memory" / f"{_today()}.md"
    if not diary.exists():
        return False
    try:
        content = diary.read_text(encoding="utf-8")
        return "决策" in content or "决定" in content
    except IOError:
        return False


def _pcec_cooldown(state, hours=6):
    last = state.get("pcec", {}).get("last_trigger")
    if last is None:
        return True
    dt = _parse_dt(last)
    if dt is None:
        return True
    return (datetime.now().astimezone(timezone.utc) - dt).total_seconds() > hours * 3600


TRIGGER_MAP = {
    "pcec": [
        ("task-status.json 显示最近存在失败任务", _has_recent_failed_task),
        ("fallback：今日日记有失败教训记录", _has_failures_today_fallback),
        ("距上次 PCEC 触发已超 6 小时", lambda s: _pcec_cooldown(s, hours=6)),
    ],
    "ppec": [
        ("task-status.json 显示今日有任务变更", _has_task_change_today),
        ("fallback：今日有新经验记录", _has_new_experience_today_fallback),
        ("fallback：今日有失败教训", _has_failures_today_fallback),
        ("fallback：今日有决策记录", _has_decisions_today_fallback),
    ],
    "piec": [
        ("本周任务总数 ≥ 5（来自 task-status.json）", lambda s: _week_task_count(s, min_count=5)),
        ("本周失败率 ≥ 30%（来自 task-status.json）", lambda s: _week_failure_rate(s, threshold=0.3)),
        ("本周存在重复失败任务类型（来自 task-status.json）", lambda s: _week_repeated_failure_type(s, min_repeat=2)),
    ],
    "psec": [
        # TODO (P2): 接入更长周期真实指标（30天任务成功率、技能频率、用户反馈）
        ("PSEC 暂未接入月度真实指标，需人工触发/后续扩展", lambda s: False),
    ],
}

ACTIONS_MAP = {
    "pcec": [
        "记录失败模式到 evolution-log.jsonl",
        "更新 memory/topics/failures.md（新增失败类型）",
        "微调工具调用参数（记录到工具偏好）",
    ],
    "ppec": [
        "提取今日经验规则 → 写入 memory/rules/",
        "更新 MEMORY.md（决策同步）",
        "记录 PPEC 事件到 evolution-log.jsonl",
    ],
    "piec": [
        "汇总本周所有事件 → 生成 docs/weekly-evolution.md",
        "识别本周主要矛盾（失败率最高类型）",
        "输出技能迭代建议",
        "记录 PIEC 事件到 evolution-log.jsonl",
    ],
    "psec": [
        "汇总本月所有 PIEC 报告",
        "走 decision-cognition 流程评估方向",
        "生成 docs/monthly-evolution.md",
        "记录 PSEC 事件到 evolution-log.jsonl",
    ],
}


def check(mode: str) -> dict:
    mode = _normalize_level(mode)
    if mode not in TRIGGER_MAP:
        return {"should_trigger": False, "reasons": [], "actions": [], "error": f"未知层级: {mode}，可选: {LEVELS}"}
    state = _load_state()
    reasons = []
    triggered = False
    for desc, check_fn in TRIGGER_MAP[mode]:
        try:
            result = check_fn(state)
        except Exception:
            result = False
        if result:
            triggered = True
            reasons.append(f"✅ {desc}")
    if not reasons:
        reasons.append(f"ℹ️ 无特殊触发条件（层级: {mode}），按需手动触发")
    return {
        "should_trigger": triggered,
        "reasons": reasons,
        "actions": ACTIONS_MAP.get(mode, []),
        "level": mode,
        "label": LEVEL_LABELS.get(mode, mode),
    }


def status() -> str:
    state = _load_state()
    now_str = _now()
    task_count = len(_load_task_status())
    lines = ["=" * 48, f"🧬 进化状态概览  —  {now_str}", "=" * 48]
    for level in LEVELS:
        info = state.get(level, {"last_trigger": None, "count": 0})
        last = info.get("last_trigger") or "从未触发"
        count = info.get("count", 0)
        label = LEVEL_LABELS.get(level, level)
        if last != "从未触发":
            dt = _parse_dt(last)
            if dt:
                delta = datetime.now().astimezone(timezone.utc) - dt
                if delta.days > 0:
                    since = f"{delta.days} 天前"
                elif delta.seconds >= 3600:
                    since = f"{delta.seconds // 3600} 小时前"
                else:
                    since = f"{delta.seconds // 60} 分钟前"
            else:
                since = last
        else:
            since = "—"
        lines += [f"\n  [{level.upper()}] {label}", f"    累计触发: {count} 次", f"    上次触发: {last}", f"    距今:     {since}"]
    lines += ["\n" + "=" * 48, f"\n📋 task-status 数据源: {'✅ 可用' if task_count else '⚠️ 不可用/为空'}（任务数: {task_count}）", "\n📁 数据文件状态:"]
    for fname, fpath in [("状态文件", STATE_FILE), ("日志文件", LOG_FILE), ("任务状态文件", TASK_STATUS_FILE)]:
        exists = "✅ 存在" if fpath.exists() else "❌ 不存在"
        size = f" ({fpath.stat().st_size} bytes)" if fpath.exists() else ""
        lines.append(f"   {exists} — {fname}{size}")
    return "\n".join(lines)


def log_event(level: str, action: str) -> dict:
    level = _normalize_level(level)
    if level not in LEVELS:
        return {"success": False, "error": f"未知层级: {level}，可选: {LEVELS}"}
    if not action or not action.strip():
        return {"success": False, "error": "action 不能为空"}
    now_str = _now()
    event = {
        "ts": now_str,
        "type": "evolution",
        "level": level,
        "source": "evolution-trigger",
        "task_id": None,
        "data": {"action": action.strip()},
        "tags": [],
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    state = _load_state()
    state.setdefault(level, {"last_trigger": None, "count": 0})
    state[level]["last_trigger"] = now_str
    state[level]["count"] = state[level].get("count", 0) + 1
    _save_state(state)
    return {"success": True, "event": event, "message": f"已记录 {LEVEL_LABELS.get(level)} 事件: {action.strip()}"}


def main():
    parser = argparse.ArgumentParser(prog="evolution-trigger", description="🧬 四层进化节奏控制器 — pcec / ppec / piec / psec")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="检查指定进化层级是否应触发").add_argument("--mode", "-m", required=True, choices=LEVELS)
    sub.add_parser("status", help="输出当前四层进化状态概览")
    log_p = sub.add_parser("log", help="记录一次进化事件")
    log_p.add_argument("--level", "-l", required=True, choices=LEVELS)
    log_p.add_argument("--action", "-a", required=True)

    args = parser.parse_args()
    if args.command == "check":
        result = check(args.mode)
        print(f"\n🧬 检查层级: {result['label']}")
        print(f"   是否触发: {'✅ 应该触发' if result['should_trigger'] else '❌ 暂不触发'}")
        for r in result.get("reasons", []):
            print(f"     {r}")
        print("   建议动作:")
        for a in result.get("actions", []):
            print(f"     → {a}")
    elif args.command == "status":
        print(status())
    elif args.command == "log":
        result = log_event(args.level, args.action)
        if result["success"]:
            print(f"✅ {result['message']}")
            print(f"   时间戳: {result['event']['ts']}")
        else:
            print(f"❌ 记录失败: {result.get('error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
