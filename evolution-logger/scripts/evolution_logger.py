#!/usr/bin/env python3
"""
Evolution Logger - 进化事件记录 CLI
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from evolution_event import append_event, load_events, parse_iso_flexible, now_iso_shanghai


def filter_events(events, event_type=None, level=None, days=None):
    cutoff = None
    if days is not None:
        from datetime import timedelta
        cutoff = parse_iso_flexible(now_iso_shanghai()) - timedelta(days=days)
    result = []
    for e in events:
        if event_type and e.get("type") != event_type:
            continue
        if level and e.get("level") != level:
            continue
        if cutoff:
            ts = parse_iso_flexible(e.get("ts"))
            if ts is None or ts < cutoff:
                continue
        result.append(e)
    return result


def get_eval_metric(event, metric):
    data = event.get("data") or {}
    if metric in data:
        return data.get(metric)
    return None


def cmd_add(args):
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

    event = append_event(
        event_type=args.type,
        level=args.level,
        source=args.source,
        data=data,
        tags=tags,
        task_id=args.task_id,
    )
    print(f"[ok] 事件已记录: {event['type']} / {event['level']} @ {event['ts']}")


def cmd_query(args):
    filtered = filter_events(load_events(), event_type=args.type, level=args.level, days=args.days)
    if not filtered:
        print("(无记录)")
        return
    for e in filtered:
        print(json.dumps(e, ensure_ascii=False))


def cmd_stats(args):
    filtered = filter_events(load_events(), days=args.days)
    type_counts = defaultdict(int)
    level_counts = defaultdict(int)
    date_counts = defaultdict(int)
    trend_by_level = defaultdict(lambda: defaultdict(int))

    for e in filtered:
        t = e.get("type", "unknown")
        l = e.get("level", "unknown")
        type_counts[t] += 1
        level_counts[l] += 1
        ts = parse_iso_flexible(e.get("ts"))
        dt = ts.date().isoformat() if ts else "unknown"
        date_counts[dt] += 1
        trend_by_level[dt][l] += 1

    print(f"\n{'='*50}")
    print(f"  进化统计报告（最近 {args.days} 天）")
    print(f"{'='*50}")
    print(f"\n总事件数：{len(filtered)}")

    print(f"\n【按类型】")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:<12} {c:>4}  {'█' * c}")

    print(f"\n【按级别】")
    for l, c in sorted(level_counts.items(), key=lambda x: -x[1]):
        print(f"  {l:<8} {c:>4}  {'█' * c}")

    print(f"\n【每日趋势】")
    for dt in sorted(date_counts.keys()):
        total = date_counts[dt]
        levels = trend_by_level[dt]
        lvl_str = " | ".join(f"{k}:{v}" for k, v in sorted(levels.items()))
        print(f"  {dt}  total={total}  {lvl_str}")

    evolution_count = type_counts.get("evolution", 0)
    if evolution_count:
        weeks = max(args.days / 7, 1)
        print(f"\n【进化频率】")
        print(f"  平均每周进化次数: {evolution_count / weeks:.2f}")

    accuracies = []
    for e in filtered:
        if e.get("type") == "evaluation":
            acc = get_eval_metric(e, "accuracy")
            if acc is not None:
                try:
                    accuracies.append((e.get("ts", ""), float(acc)))
                except (TypeError, ValueError):
                    pass
    if accuracies:
        accuracies.sort(key=lambda x: x[0])
        avg = sum(a for _, a in accuracies) / len(accuracies)
        print(f"\n【评估质量】")
        print(f"  平均准确率: {avg:.2f}（基于 {len(accuracies)} 条记录）")
        print(f"  最早: {accuracies[0][0][:10]} accuracy={accuracies[0][1]}")
        print(f"  最新: {accuracies[-1][0][:10]} accuracy={accuracies[-1][1]}")


def cmd_export(args):
    filtered = filter_events(load_events(), days=args.days)
    lines = ["# 进化报告", f"\n> 生成时间：{now_iso_shanghai()}", f"> 统计周期：最近 {args.days} 天", f"> 总事件数：{len(filtered)}", ""]
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
            data_str = json.dumps(e.get("data", {}), ensure_ascii=False)
            tag_str = " ".join(f"`{t}`" for t in e.get("tags", [])) if e.get("tags") else ""
            lines.append(f"- **{ts}** | [{lvl}] {data_str} {tag_str}")
        lines.append("")

    lines.append("## 统计摘要\n")
    type_counts = {k: len(v) for k, v in grouped.items()}
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {t}: **{c}** 条")
    lines.append("")

    Path(args.output).write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] 报告已导出: {args.output}")


def cmd_trend(args):
    filtered = filter_events(load_events(), event_type="evaluation", days=args.days)
    metric = args.metric
    records = []
    for e in filtered:
        val = get_eval_metric(e, metric)
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
        print(f"  {ts}  {val:.1f}  {'▓' * int(val)}")
    if len(records) >= 2:
        first, last = records[0][1], records[-1][1]
        change = last - first
        direction = "↑" if change > 0 else "↓" if change < 0 else "→"
        print(f"\n趋势: {first:.1f} → {last:.1f}  ({direction} {abs(change):.1f})")


def main():
    parser = argparse.ArgumentParser(prog="evolution-logger", description="进化事件记录 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="添加一条进化事件")
    p_add.add_argument("--type", required=True, choices=["evaluation", "evolution", "decision", "lesson"])
    p_add.add_argument("--level", required=True, choices=["pcec", "ppec", "piec", "psec"])
    p_add.add_argument("--data", required=True)
    p_add.add_argument("--tags")
    p_add.add_argument("--source", default="evolution-logger")
    p_add.add_argument("--task-id")

    p_q = sub.add_parser("query", help="查询进化事件")
    p_q.add_argument("--type", choices=["evaluation", "evolution", "decision", "lesson"])
    p_q.add_argument("--level", choices=["pcec", "ppec", "piec", "psec"])
    p_q.add_argument("--days", type=int, default=7)

    p_s = sub.add_parser("stats", help="生成进化统计报告")
    p_s.add_argument("--days", type=int, default=30)

    p_e = sub.add_parser("export", help="导出 Markdown 进化报告")
    p_e.add_argument("--output", required=True)
    p_e.add_argument("--days", type=int, default=30)

    p_t = sub.add_parser("trend", help="追踪指标历史趋势")
    p_t.add_argument("--metric", required=True)
    p_t.add_argument("--days", type=int, default=90)

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
