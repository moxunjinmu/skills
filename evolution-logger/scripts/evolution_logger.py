#!/usr/bin/env python3
"""
Evolution Logger - 进化事件记录 CLI

用法:
    evolution-logger add     --type <type> --level <level> --data <json> [--tags <json>]
    evolution-logger query  --type <type> --level <level> --days <n>
    evolution-logger stats   --days <n>
    evolution-logger export --output <path> --days <n>
    evolution-logger trend  --metric <name> [--days <n>]
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

LOG_FILE = Path.home() / ".openclaw" / "workspace" / "memory" / "evolution-log.jsonl"


# ── Helpers ──────────────────────────────────────────────────────────────────

def now_iso():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def ensure_log_file():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.touch()


def load_events():
    """Return list of parsed JSON lines, newest first."""
    if not LOG_FILE.exists():
        return []
    events = []
    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return list(reversed(events))  # newest first


def parse_iso(ts_str):
    """Parse ISO timestamp string to datetime."""
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))


def days_ago(n):
    """Return datetime n days ago from now (UTC+8)."""
    return datetime.now(timezone(timedelta(hours=8))) - timedelta(days=n)


def filter_events(events, event_type=None, level=None, days=None):
    """Filter events by optional criteria."""
    cutoff = days_ago(days) if days else None
    result = []
    for e in events:
        if event_type and e.get("type") != event_type:
            continue
        if level and e.get("level") != level:
            continue
        if cutoff:
            try:
                ts = parse_iso(e.get("ts", ""))
                if ts < cutoff:
                    continue
            except Exception:
                continue
        result.append(e)
    return result


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_add(args):
    ensure_log_file()
    try:
        data = json.loads(args.data) if args.data else {}
    except json.JSONDecodeError as err:
        print(f"[error] --data 必须为合法 JSON: {err}", file=sys.stderr)
        sys.exit(1)

    tags = []
    if args.tags:
        try:
            tags = json.loads(args.tags)
        except json.JSONDecodeError as err:
            print(f"[error] --tags 必须为合法 JSON: {err}", file=sys.stderr)
            sys.exit(1)

    event = {
        "ts": now_iso(),
        "type": args.type,
        "level": args.level,
        "data": data,
        "tags": tags,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"[ok] 事件已记录: {event['type']} / {event['level']} @ {event['ts']}")


def cmd_query(args):
    events = load_events()
    filtered = filter_events(events, event_type=args.type, level=args.level, days=args.days)
    if not filtered:
        print("(无记录)")
        return
    for e in filtered:
        print(json.dumps(e, ensure_ascii=False))


def cmd_stats(args):
    events = load_events()
    filtered = filter_events(events, days=args.days)

    # Count by type
    type_counts = defaultdict(int)
    level_counts = defaultdict(int)
    date_counts = defaultdict(int)
    trend_by_level = defaultdict(lambda: defaultdict(int))  # date -> level -> count

    for e in filtered:
        t = e.get("type", "unknown")
        l = e.get("level", "unknown")
        type_counts[t] += 1
        level_counts[l] += 1
        try:
            dt = parse_iso(e.get("ts", "")).date().isoformat()
        except Exception:
            dt = "unknown"
        date_counts[dt] += 1
        trend_by_level[dt][l] += 1

    print(f"\n{'='*50}")
    print(f"  进化统计报告（最近 {args.days} 天）")
    print(f"{'='*50}")
    print(f"\n总事件数：{len(filtered)}")

    print(f"\n【按类型】")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        bar = "█" * c
        print(f"  {t:<12} {c:>4}  {bar}")

    print(f"\n【按级别】")
    for l, c in sorted(level_counts.items(), key=lambda x: -x[1]):
        bar = "█" * c
        print(f"  {l:<8} {c:>4}  {bar}")

    print(f"\n【每日趋势】")
    for dt in sorted(date_counts.keys()):
        total = date_counts[dt]
        levels = trend_by_level[dt]
        lvl_str = " | ".join(f"{k}:{v}" for k, v in sorted(levels.items()))
        print(f"  {dt}  total={total}  {lvl_str}")

    # Evolution frequency: evolution events per week
    if "evolution" in type_counts:
        weeks = args.days / 7
        print(f"\n【进化频率】")
        print(f"  平均每周进化次数: {type_counts['evolution'] / weeks:.2f}")

    # Evaluation quality trend (avg accuracy if present)
    accuracies = []
    for e in filtered:
        if e.get("type") == "evaluation":
            acc = e.get("data", {}).get("accuracy")
            if acc is not None:
                try:
                    accuracies.append((e.get("ts", ""), float(acc)))
                except (TypeError, ValueError):
                    pass
    if accuracies:
        avg = sum(a for _, a in accuracies) / len(accuracies)
        print(f"\n【评估质量】")
        print(f"  平均准确率: {avg:.2f}（基于 {len(accuracies)} 条记录）")
        print(f"  最早: {accuracies[0][0][:10]} accuracy={accuracies[0][1]}")
        print(f"  最新: {accuracies[-1][0][:10]} accuracy={accuracies[-1][1]}")


def cmd_export(args):
    events = load_events()
    filtered = filter_events(events, days=args.days)

    lines = []
    lines.append("# 进化报告")
    lines.append(f"\n> 生成时间：{now_iso()}")
    lines.append(f"> 统计周期：最近 {args.days} 天")
    lines.append(f"> 总事件数：{len(filtered)}")
    lines.append("")

    # Group by type
    grouped = defaultdict(list)
    for e in filtered:
        grouped[e.get("type", "unknown")].append(e)

    for ev_type in ["evaluation", "evolution", "decision", "lesson"]:
        events_list = grouped.get(ev_type, [])
        if not events_list:
            continue
        lines.append(f"## {ev_type.upper()} 事件（共 {len(events_list)} 条）")
        lines.append("")
        for e in events_list:
            ts = e.get("ts", "")[:19].replace("T", " ")
            lvl = e.get("level", "-")
            data = e.get("data", {})
            tags = e.get("tags", [])
            data_str = json.dumps(data, ensure_ascii=False)
            tag_str = " ".join(f"`{t}`" for t in tags) if tags else ""
            lines.append(f"- **{ts}** | [{lvl}] {data_str} {tag_str}")
        lines.append("")

    # Stats summary
    lines.append("## 统计摘要")
    lines.append("")
    type_counts = {k: len(v) for k, v in grouped.items()}
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {t}: **{c}** 条")
    lines.append("")

    output = "\n".join(lines)
    Path(args.output).write_text(output, encoding="utf-8")
    print(f"[ok] 报告已导出: {args.output}")


def cmd_trend(args):
    events = load_events()
    filtered = filter_events(events, event_type="evaluation", days=args.days)

    metric = args.metric
    records = []
    for e in filtered:
        val = e.get("data", {}).get(metric)
        if val is not None:
            try:
                records.append((e.get("ts", "")[:10], float(val)))
            except (TypeError, ValueError):
                pass

    if not records:
        print(f"(未找到指标 '{metric}' 的历史数据)")
        return

    records.sort(key=lambda x: x[0])
    print(f"\n指标趋势: {metric}（共 {len(records)} 条）")
    print(f"{'─'*50}")
    for ts, val in records:
        bar = "▓" * int(val)
        print(f"  {ts}  {val:.1f}  {bar}")

    # Simple trend
    if len(records) >= 2:
        first = records[0][1]
        last = records[-1][1]
        change = last - first
        direction = "↑" if change > 0 else "↓" if change < 0 else "→"
        print(f"\n趋势: {first:.1f} → {last:.1f}  ({direction} {abs(change):.1f})")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="evolution-logger",
        description="进化事件记录 CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="添加一条进化事件")
    p_add.add_argument("--type", required=True,
                        choices=["evaluation", "evolution", "decision", "lesson"],
                        help="事件类型")
    p_add.add_argument("--level", required=True,
                        choices=["pcpec", "ppec", "piec", "psec"],
                        help="事件级别")
    p_add.add_argument("--data", required=True,
                        help="事件数据（JSON 字符串）")
    p_add.add_argument("--tags", help="标签列表（JSON 字符串）")

    # query
    p_q = sub.add_parser("query", help="查询进化事件")
    p_q.add_argument("--type", choices=["evaluation", "evolution", "decision", "lesson"],
                      help="按类型过滤")
    p_q.add_argument("--level", choices=["pcpec", "ppec", "piec", "psec"],
                      help="按级别过滤")
    p_q.add_argument("--days", type=int, default=7, help="查询最近N天（默认7）")

    # stats
    p_s = sub.add_parser("stats", help="生成进化统计报告")
    p_s.add_argument("--days", type=int, default=30, help="统计最近N天（默认30）")

    # export
    p_e = sub.add_parser("export", help="导出 Markdown 进化报告")
    p_e.add_argument("--output", required=True, help="输出文件路径")
    p_e.add_argument("--days", type=int, default=30, help="导出最近N天（默认30）")

    # trend
    p_t = sub.add_parser("trend", help="追踪指标历史趋势")
    p_t.add_argument("--metric", required=True, help="要追踪的指标名称（如 accuracy）")
    p_t.add_argument("--days", type=int, default=90, help="查询最近N天（默认90）")

    args = parser.parse_args()

    if args.command == "add":
        cmd_add(args)
    elif args.command == "query":
        cmd_query(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "trend":
        cmd_trend(args)


if __name__ == "__main__":
    main()
