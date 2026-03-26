#!/usr/bin/env python3
"""self-evaluator.py — 自我评估器 CLI"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LOGGER_DIR = SCRIPT_DIR.parent.parent / "evolution-logger" / "scripts"
if str(LOGGER_DIR) not in sys.path:
    sys.path.insert(0, str(LOGGER_DIR))

from evolution_event import append_event, load_events

DIMENSIONS = ["accuracy", "efficiency", "safety", "completeness", "proactiveness"]
DIM_CN = {
    "accuracy": "准确性",
    "efficiency": "效率",
    "safety": "安全性",
    "completeness": "完整性",
    "proactiveness": "主动性",
}
FEEDBACK_DELTA = {"positive": 1.5, "negative": -1.5, "neutral": 0.0}


def bar(score: float) -> str:
    filled = int(round(score))
    return "█" * filled + "░" * (10 - filled)


def compute_score(base: float, feedback: str) -> float:
    delta = FEEDBACK_DELTA.get(feedback, 0.0)
    return max(0.0, min(10.0, base + delta))


def generate_report(accuracy, efficiency, safety, completeness, proactiveness, feedback="neutral"):
    a = compute_score(accuracy, feedback)
    e = compute_score(efficiency, feedback)
    s = compute_score(safety, feedback)
    c = compute_score(completeness, feedback)
    p = compute_score(proactiveness, feedback)

    dims = {"accuracy": a, "efficiency": e, "safety": s, "completeness": c, "proactiveness": p}
    overall = sum(dims.values()) / len(dims)
    sorted_dims = sorted(dims.items(), key=lambda x: x[1])

    weakness_desc = {
        "accuracy": "结果存在错误或偏差，需加强验证环节",
        "efficiency": "对话轮次偏多或耗时过长，可更直接简洁",
        "safety": "存在安全风险或合规隐患，需注意操作边界",
        "completeness": "需求覆盖不完整，存在明显遗漏项",
        "proactiveness": "被动等待指令，缺乏主动发现和解决问题的意识",
    }
    evolution_suggestions = {
        "accuracy": "加强任务结果的自我验证，执行后对照需求核对一遍",
        "efficiency": "接任务后先想清楚再动手，减少无效来回",
        "safety": "操作前先过一遍安全红线清单，尤其是外部操作和敏感数据",
        "completeness": "接任务后先列清单对标需求，完成后逐项打勾",
        "proactiveness": "主动预判 Boss 潜在需求，超出预期给出建议",
    }

    top3 = [f"{i+1}. {DIM_CN[k]}（{v:.1f}）：{weakness_desc[k]}" for i, (k, v) in enumerate(sorted_dims[:3])]
    top2_keys = [k for k, _ in sorted_dims[:2]]
    suggestions = "；".join(evolution_suggestions[k] for k in top2_keys)

    report = "\n".join([
        "## 能力雷达",
        f"准确性: {bar(a)} {a:.1f}",
        f"效率:   {bar(e)} {e:.1f}",
        f"安全性: {bar(s)} {s:.1f}",
        f"完整性: {bar(c)} {c:.1f}",
        f"主动性: {bar(p)} {p:.1f}",
        "",
        "## 短板TOP3",
        *top3,
        "",
        "## 进化建议",
        f"下次任务应重点关注：{'、'.join([DIM_CN[k] for k in top2_keys])}，{suggestions}",
    ])

    event_data = {
        **dims,
        "overall": round(overall, 2),
        "feedback": feedback,
        "weaknesses": [f"{DIM_CN[k]}（{v:.1f}）" for k, v in sorted_dims[:3]],
        "evolution_suggestion": suggestions,
    }
    return report, event_data


def eval_dimensions_from_event(event):
    data = event.get("data") or {}
    if all(k in data for k in DIMENSIONS):
        return {k: float(data[k]) for k in DIMENSIONS}
    if "dimensions" in event:
        dims = event.get("dimensions") or {}
        if all(k in dims for k in DIMENSIONS):
            return {k: float(dims[k]) for k in DIMENSIONS}
    return None


def load_history(n: int):
    events = []
    for event in load_events():
        if event.get("type") != "evaluation":
            continue
        dims = eval_dimensions_from_event(event)
        if not dims:
            continue
        data = event.get("data") or {}
        overall = data.get("overall")
        if overall is None:
            overall = sum(dims.values()) / len(dims)
        events.append({"dimensions": dims, "overall": float(overall)})
    return list(reversed(events))[-n:] if n > 0 else list(reversed(events))


def trend(values):
    if len(values) < 2:
        return "（数据不足）"
    diff = values[-1] - values[0]
    if diff > 0.5:
        return "📈 上升"
    elif diff < -0.5:
        return "📉 下降"
    return "➡️ 稳定"


def generate_radar_report(history_n: int) -> str:
    events = load_history(history_n)
    if not events:
        return "## 能力趋势报告\n\n暂无历史评估记录。\n先运行 `self-evaluator score` 积累数据后再查看趋势。"
    lines = ["## 能力趋势报告", f"（基于最近 {len(events)} 条评估记录）", ""]
    for dim in DIMENSIONS:
        vals = [e["dimensions"][dim] for e in events]
        avg = sum(vals) / len(vals)
        lines.append(f"### {DIM_CN[dim]}")
        lines.append(f"- 平均: {avg:.2f}  最高: {max(vals):.1f}  最低: {min(vals):.1f}  {trend(vals)}")
        lines.append(f"- 折线: {' '.join(f'{v:.0f}' for v in vals)}")
        lines.append("")
    overalls = [e["overall"] for e in events]
    avg_overall = sum(overalls) / len(overalls)
    lines.append(f"### 综合得分: {avg_overall:.2f}  {trend(overalls)}")
    lines.append("")
    dim_avgs = {dim: sum(e["dimensions"][dim] for e in events) / len(events) for dim in DIMENSIONS}
    sorted_weak = sorted(dim_avgs.items(), key=lambda x: x[1])
    lines.append("## 持续弱点（按均分排序）")
    for i, (k, v) in enumerate(sorted_weak[:3]):
        lines.append(f"{i+1}. {DIM_CN[k]}（均分{v:.2f}）")
    lines.append("")
    lines.append("## 改进优先级")
    top2 = [x[0] for x in sorted_weak[:2]]
    for i, (k, v) in enumerate(sorted_weak):
        tag = "🔴 优先改进" if k in top2 else "🟡 次要关注"
        lines.append(f"{i+1}. **{DIM_CN[k]}**（均分{v:.2f}）— {tag}")
    return "\n".join(lines)


def generate_weakness_report() -> str:
    events = load_history(10)
    if not events:
        return "## 能力短板报告\n\n暂无历史数据。\n请先运行 `self-evaluator score` 记录评估结果。"
    recent = events[-3:] if len(events) >= 3 else events
    dim_avgs = {dim: sum(e["dimensions"][dim] for e in recent) / len(recent) for dim in DIMENSIONS}
    sorted_dims = sorted(dim_avgs.items(), key=lambda x: x[1])
    lines = ["## 能力短板报告", f"（基于最近 {len(recent)} 条评估，均分）", ""]
    for dim in DIMENSIONS:
        v = dim_avgs[dim]
        lines.append(f"{DIM_CN[dim]}: {bar(v)} {v:.1f}")
    lines.append("")
    lines.append("## 短板TOP3")
    for i, (k, v) in enumerate(sorted_dims[:3]):
        color = "🔴" if v < 5 else "🟡"
        lines.append(f"{i+1}. {color} {DIM_CN[k]}（{v:.1f}）")
    lines.append("")
    lines.append("## 改进优先级")
    for i, (k, v) in enumerate(sorted_dims):
        tag = "🔴 紧急" if v < 5 else "🟡 关注" if v < 7 else "🟢 良好"
        lines.append(f"{i+1}. {tag} {DIM_CN[k]}（{v:.1f}）")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(prog="self-evaluator", description="自我评估器 — 任务质量评分 + 能力雷达")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_score = sub.add_parser("score", help="输入5个维度分数，输出雷达报告 + 标准事件")
    p_score.add_argument("--accuracy", type=float, required=True)
    p_score.add_argument("--efficiency", type=float, required=True)
    p_score.add_argument("--safety", type=float, required=True)
    p_score.add_argument("--completeness", type=float, required=True)
    p_score.add_argument("--proactiveness", type=float, required=True)
    p_score.add_argument("--feedback", choices=["positive", "negative", "neutral"], default="neutral")
    p_score.add_argument("--save", action="store_true", help="显式保存到 evolution-log.jsonl")
    p_score.add_argument("--task-id", type=str, default=None)

    p_radar = sub.add_parser("radar", help="读取最近N条评估记录，生成综合能力趋势报告")
    p_radar.add_argument("--history", type=int, default=10)

    sub.add_parser("短板", help="输出当前能力短板报告 + 改进优先级")

    args = parser.parse_args()
    if args.cmd == "score":
        report, event_data = generate_report(args.accuracy, args.efficiency, args.safety, args.completeness, args.proactiveness, args.feedback)
        print(report)
        event_payload = {
            "type": "evaluation",
            "level": "pcec",
            "source": "self-evaluator",
            "task_id": args.task_id,
            "data": event_data,
            "tags": [],
        }
        print("\n## 标准事件\n" + json.dumps(event_payload, ensure_ascii=False, indent=2))
        if args.save:
            event = append_event("evaluation", "pcec", "self-evaluator", event_data, tags=[], task_id=args.task_id)
            print(f"\n✅ 已写入 evolution-log.jsonl: {event['ts']}")
        else:
            print("\n（默认未写入日志；如需落盘请加 --save）")
    elif args.cmd == "radar":
        print(generate_radar_report(args.history))
    elif args.cmd == "短板":
        print(generate_weakness_report())


if __name__ == "__main__":
    main()
