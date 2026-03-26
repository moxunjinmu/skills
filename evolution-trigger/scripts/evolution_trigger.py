#!/usr/bin/env python3
"""
evolution-trigger: 四层进化节奏控制器 CLI
PCEC / PPEC / PIEC / PSEC 触发检查、状态查询、事件记录
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 路径配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
STATE_FILE = MEMORY_DIR / "evolution-state.json"
LOG_FILE = MEMORY_DIR / "evolution-log.jsonl"

# 层级定义（按优先级从低到高）
LEVELS = ["pcpec", "ppec", "piec", "psec"]
LEVEL_LABELS = {
    "pcpec": "PCEC（微进化）",
    "ppec": "PPEC（小进化）",
    "piec": "PIEC（中进化）",
    "psec": "PSEC（大进化）",
}

# PCEC 触发条件（元组：条件描述, 检查函数）
PCEC_TRIGGERS = [
    ("今日有失败教训记录", lambda s: _has_failures_today(s)),
    ("昨日 PCEC 距今超过 6 小时", lambda s: _pcpec_cooldown(s, hours=6)),
    ("强制指定检查", lambda s: True),  # 无状态时默认触发
]

PPEC_TRIGGERS = [
    ("今日有新经验记录", lambda s: _has_new_experience_today(s)),
    ("今日有失败教训", lambda s: _has_failures_today(s)),
    ("今日有决策记录", lambda s: _has_decisions_today(s)),
]

PIEC_TRIGGERS = [
    ("本周任务总数 > 5", lambda s: _week_task_count(s, min_count=5)),
    ("本周成功率 < 80%", lambda s: _week_success_rate(s, threshold=0.8)),
    ("本周连续失败类型 ≥ 2 种", lambda s: _week_failure_types(s, min_types=2)),
]

PSEC_TRIGGERS = [
    ("本月 PIEC 触发次数 ≥ 2", lambda s: _month_piec_count(s, min_count=2)),
    ("本月成功率持续下降", lambda s: _month_success_decline(s)),
    ("技能使用频率偏移显著", lambda s: _skill_freq_drift(s)),
]


# ─── 辅助检查函数 ────────────────────────────────────────────

def _now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _default_state():
    return {
        "pcpec": {"last_trigger": None, "count": 0},
        "ppec": {"last_trigger": None, "count": 0},
        "piec": {"last_trigger": None, "count": 0},
        "psec": {"last_trigger": None, "count": 0},
    }


def _load_state():
    if not STATE_FILE.exists():
        return _default_state()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return _default_state()


def _save_state(state):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _parse_dt(ts):
    if ts is None:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _days_ago(ts_str, days):
    """判断 ts_str 是否在 days 天之内"""
    dt = _parse_dt(ts_str)
    if dt is None:
        return False
    return (datetime.now() - dt).days < days


def _this_week_start():
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    return monday.strftime("%Y-%m-%d")


def _this_month_start():
    return datetime.now().strftime("%Y-%m") + "-01"


# 模拟检查函数（实际接入记忆系统后可增强）
def _has_failures_today(state):
    today = _today()
    diary = WORKSPACE / "memory" / f"{today}.md"
    if not diary.exists():
        return False
    try:
        content = diary.read_text(encoding="utf-8")
        return "❌" in content or "失败" in content
    except IOError:
        return False


def _has_new_experience_today(state):
    today = _today()
    diary = WORKSPACE / "memory" / f"{today}.md"
    if not diary.exists():
        return False
    try:
        content = diary.read_text(encoding="utf-8")
        return "经验" in content or "教训" in content or "✅" in content
    except IOError:
        return False


def _has_decisions_today(state):
    today = _today()
    diary = WORKSPACE / "memory" / f"{today}.md"
    if not diary.exists():
        return False
    try:
        content = diary.read_text(encoding="utf-8")
        return "决策" in content or "决定" in content
    except IOError:
        return False


def _pcpec_cooldown(state, hours=6):
    last = state.get("pcpec", {}).get("last_trigger")
    if last is None:
        return True
    dt = _parse_dt(last)
    if dt is None:
        return True
    return (datetime.now() - dt).total_seconds() > hours * 3600


def _week_task_count(state, min_count=5):
    if not LOG_FILE.exists():
        return False
    week_start = _this_week_start()
    try:
        count = 0
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    ev = json.loads(line.strip())
                    ts = ev.get("timestamp", "")
                    if ts >= week_start and ev.get("level") in LEVELS:
                        count += 1
                except json.JSONDecodeError:
                    continue
        return count >= min_count
    except IOError:
        return False


def _week_success_rate(state, threshold=0.8):
    if not LOG_FILE.exists():
        return False
    week_start = _this_week_start()
    total = 0
    failures = 0
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    ev = json.loads(line.strip())
                    ts = ev.get("timestamp", "")
                    if ts >= week_start:
                        total += 1
                        if "failure" in ev.get("action", "").lower() or ev.get("result") == "failure":
                            failures += 1
                except json.JSONDecodeError:
                    continue
        if total == 0:
            return False
        return (total - failures) / total < threshold
    except IOError:
        return False


def _week_failure_types(state, min_types=2):
    if not LOG_FILE.exists():
        return False
    week_start = _this_week_start()
    types = set()
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    ev = json.loads(line.strip())
                    ts = ev.get("timestamp", "")
                    if ts >= week_start and "failure" in ev.get("action", "").lower():
                        types.add(ev.get("type", "unknown"))
                except json.JSONDecodeError:
                    continue
        return len(types) >= min_types
    except IOError:
        return False


def _month_piec_count(state, min_count=2):
    if not LOG_FILE.exists():
        return False
    month_start = _this_month_start()
    count = 0
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    ev = json.loads(line.strip())
                    ts = ev.get("timestamp", "")
                    if ts >= month_start and ev.get("level") == "piec":
                        count += 1
                except json.JSONDecodeError:
                    continue
        return count >= min_count
    except IOError:
        return False


def _month_success_decline(state):
    """本月成功率是否持续下降（简化：最近2周对比）"""
    # 简化判断：检查是否存在连续下降的周记录
    return False  # 需要更复杂的历史分析，暂时返回 False


def _skill_freq_drift(state):
    """技能使用频率偏移（简化：检查是否所有层级 count 都是 0）"""
    counts = [state.get(l, {}).get("count", 0) for l in LEVELS]
    return all(c == 0 for c in counts)  # 全零表示从未触发，视为偏移


# ─── 核心逻辑 ────────────────────────────────────────────────

def check(mode: str) -> dict:
    """
    检查指定层级的触发条件
    返回：{"should_trigger": bool, "reasons": [str], "actions": [str]}
    """
    state = _load_state()

    trigger_map = {
        "pcpec": PCEC_TRIGGERS,
        "ppec": PPEC_TRIGGERS,
        "piec": PIEC_TRIGGERS,
        "psec": PSEC_TRIGGERS,
    }

    actions_map = {
        "pcpec": [
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

    if mode not in trigger_map:
        return {"should_trigger": False, "reasons": [], "actions": [], "error": f"未知层级: {mode}"}

    reasons = []
    triggered = False

    for desc, check_fn in trigger_map[mode]:
        try:
            result = check_fn(state)
        except Exception:
            result = False
        if result:
            triggered = True
            reasons.append(f"✅ {desc}")

    # 默认理由（无特殊条件时）
    if not reasons:
        reasons.append(f"ℹ️ 无特殊触发条件（层级: {mode}），按需手动触发")

    return {
        "should_trigger": triggered,
        "reasons": reasons,
        "actions": actions_map.get(mode, []),
        "level": mode,
        "label": LEVEL_LABELS.get(mode, mode),
    }


def status() -> dict:
    """输出当前四层进化状态概览"""
    state = _load_state()
    now_str = _now()

    lines = []
    lines.append("=" * 48)
    lines.append(f"🧬 进化状态概览  —  {now_str}")
    lines.append("=" * 48)

    all_zero = all(state.get(l, {}).get("count", 0) == 0 for l in LEVELS)

    for level in LEVELS:
        info = state.get(level, {"last_trigger": None, "count": 0})
        last = info.get("last_trigger") or "从未触发"
        count = info.get("count", 0)
        label = LEVEL_LABELS.get(level, level)

        if last == "从未触发":
            since = "—"
        else:
            dt = _parse_dt(last)
            if dt:
                delta = datetime.now() - dt
                if delta.days > 0:
                    since = f"{delta.days} 天前"
                elif delta.seconds >= 3600:
                    since = f"{delta.seconds // 3600} 小时前"
                else:
                    since = f"{delta.seconds // 60} 分钟前"
            else:
                since = last

        lines.append(f"\n  [{level.upper()}] {label}")
        lines.append(f"    累计触发: {count} 次")
        lines.append(f"    上次触发: {last}")
        lines.append(f"    距今:     {since}")

    lines.append("\n" + "=" * 48)

    # 文件状态
    lines.append("\n📁 数据文件状态:")
    for fname, fpath in [("状态文件", STATE_FILE), ("日志文件", LOG_FILE)]:
        exists = "✅ 存在" if fpath.exists() else "❌ 不存在"
        size = ""
        if fpath.exists():
            try:
                size = f" ({fpath.stat().st_size} bytes)"
            except OSError:
                size = ""
        lines.append(f"   {exists} — {fname}{size}")

    if all_zero:
        lines.append("\n⚠️  所有层级累计次数为 0，请确认 cron 配置是否生效")

    output = "\n".join(lines)
    return {
        "state": state,
        "timestamp": now_str,
        "output": output,
    }


def log_event(level: str, action: str) -> dict:
    """记录一次进化事件到日志文件"""
    if level not in LEVELS:
        return {"success": False, "error": f"未知层级: {level}，可选: {LEVELS}"}

    if not action or not action.strip():
        return {"success": False, "error": "action 不能为空"}

    now_str = _now()
    event = {
        "timestamp": now_str,
        "level": level,
        "action": action.strip(),
        "label": LEVEL_LABELS.get(level, level),
    }

    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # 更新状态
    state = _load_state()
    if level not in state:
        state[level] = {"last_trigger": None, "count": 0}
    state[level]["last_trigger"] = now_str
    state[level]["count"] = state[level].get("count", 0) + 1
    _save_state(state)

    return {
        "success": True,
        "event": event,
        "message": f"已记录 {LEVEL_LABELS.get(level)} 事件: {action.strip()}",
    }


# ─── CLI 入口 ────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="evolution-trigger",
        description="🧬 四层进化节奏控制器 — PCEC / PPEC / PIEC / PSEC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s status                              查看进化状态概览
  %(prog)s check --mode pcpec                   检查 PCEC 是否应触发
  %(prog)s check --mode piec                    检查 PIEC 是否应触发
  %(prog)s log --level pcpec --action "优化了飞书文档写入工具调用参数"
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # check
    p_check = sub.add_parser("check", help="检查指定进化层级是否应触发")
    p_check.add_argument(
        "--mode",
        "-m",
        required=True,
        choices=["pcpec", "ppec", "piec", "psec"],
        help="进化层级（必选）",
    )

    # status
    sub.add_parser("status", help="输出当前四层进化状态概览")

    # log
    p_log = sub.add_parser("log", help="记录一次进化事件")
    p_log.add_argument(
        "--level",
        "-l",
        required=True,
        choices=["pcpec", "ppec", "piec", "psec"],
        help="进化层级（必选）",
    )
    p_log.add_argument(
        "--action",
        "-a",
        required=True,
        help="动作描述（必填，建议一句话）",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "check":
        result = check(args.mode)
        print(f"\n🧬 检查层级: {result.get('label', args.mode)}")
        print(f"   是否触发: {'✅ 应该触发' if result['should_trigger'] else '❌ 暂不触发'}")
        if result.get("reasons"):
            print("   触发原因:")
            for r in result["reasons"]:
                print(f"     {r}")
        if result.get("actions"):
            print("   建议动作:")
            for a in result["actions"]:
                print(f"     → {a}")
        if result.get("error"):
            print(f"   错误: {result['error']}")
        sys.exit(0 if result["should_trigger"] else 0)  # 不管是否触发都正常退出

    elif args.command == "status":
        result = status()
        print(result["output"])
        sys.exit(0)

    elif args.command == "log":
        result = log_event(args.level, args.action)
        if result["success"]:
            print(f"✅ {result['message']}")
            print(f"   时间戳: {result['event']['timestamp']}")
            sys.exit(0)
        else:
            print(f"❌ 记录失败: {result.get('error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
