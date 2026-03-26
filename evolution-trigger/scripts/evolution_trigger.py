#!/usr/bin/env python3
"""
evolution-trigger: 四层进化节奏控制器 CLI
pcec / ppec / piec / psec 触发检查、状态查询、事件记录
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
STATE_FILE = MEMORY_DIR / "evolution-state.json"
LOG_FILE = MEMORY_DIR / "evolution-log.jsonl"

LEVELS = ["pcec", "ppec", "piec", "psec"]
LEVEL_LABELS = {
    "pcec": "PCEC（微进化）",
    "ppec": "PPEC（小进化）",
    "piec": "PIEC（中进化）",
    "psec": "PSEC（大进化）",
}
TZ_SH = timedelta(hours=8)


def _now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _this_week_start():
    monday = datetime.now() - timedelta(days=datetime.now().weekday())
    return monday.strftime("%Y-%m-%d")


def _this_month_start():
    return datetime.now().strftime("%Y-%m") + "-01"


def _load_state():
    if not STATE_FILE.exists():
        return {l: {"last_trigger": None, "count": 0} for l in LEVELS}
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        # 迁移：旧 pcpec → pcec
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
        return dt.astimezone(timezone.utc)  # 统一返回 UTC，用于计算
    except Exception:
        return None


# ── 辅助检查函数 ────────────────────────────────────────────

def _has_failures_today(state):
    diary = WORKSPACE / "memory" / f"{_today()}.md"
    if not diary.exists():
        return False
    try:
        content = diary.read_text(encoding="utf-8")
        return "❌" in content or "失败" in content
    except IOError:
        return False


def _has_new_experience_today(state):
    diary = WORKSPACE / "memory" / f"{_today()}.md"
    if not diary.exists():
        return False
    try:
        content = diary.read_text(encoding="utf-8")
        return "经验" in content or "教训" in content or "✅" in content
    except IOError:
        return False


def _has_decisions_today(state):
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


def _count_events_in_log(since_ts, level=None):
    if not LOG_FILE.exists():
        return 0
    count = 0
    try:
        for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = ev.get("ts") or ev.get("timestamp") or ""
            # 兼容旧日志时间格式
            if ts:
                try:
                    dt = _parse_dt(ts)
                    if dt is None:
                        continue
                    ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if "Z" in ts or "+" in ts else None
                    if ts_dt:
                        if ts_dt < _parse_dt(since_ts):
                            continue
                except Exception:
                    continue
            if level is None or ev.get("level") in (level, _normalize_level(level)):
                count += 1
    except IOError:
        pass
    return count


def _normalize_level(level):
    if level == "pcpec":
        return "pcec"
    return level


# ── 触发条件映射 ────────────────────────────────────────────

TRIGGER_MAP = {
    "pcec": [
        ("今日有失败教训记录", _has_failures_today),
        ("距上次 PCEC 触发已超 6 小时", lambda s: _pcec_cooldown(s, hours=6)),
        ("强制指定检查", lambda s: True),
    ],
    "ppec": [
        ("今日有新经验记录", _has_new_experience_today),
        ("今日有失败教训", _has_failures_today),
        ("今日有决策记录", _has_decisions_today),
    ],
    "piec": [
        # TODO (P1): 接入真实任务系统，不再靠日记关键词
        ("本周任务总数 > 5", lambda s: True),  # 占位，需 P1 真实指标
        ("强制检查 PIEC", lambda s: True),
    ],
    "psec": [
        # TODO (P1): 接入真实任务系统
        ("强制检查 PSEC", lambda s: True),
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


# ── 核心逻辑 ────────────────────────────────────────────────

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
    lines += ["\n" + "=" * 48, "\n📁 数据文件状态:"]
    for fname, fpath in [("状态文件", STATE_FILE), ("日志文件", LOG_FILE)]:
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

    # 写入统一 schema 事件
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

    # 更新状态
    state = _load_state()
    state.setdefault(level, {"last_trigger": None, "count": 0})
    state[level]["last_trigger"] = now_str
    state[level]["count"] = state[level].get("count", 0) + 1
    _save_state(state)

    return {
        "success": True,
        "event": event,
        "message": f"已记录 {LEVEL_LABELS.get(level)} 事件: {action.strip()}",
    }


# ── CLI 入口 ────────────────────────────────────────────────

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
