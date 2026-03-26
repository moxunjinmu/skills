#!/usr/bin/env python3
"""
decision-cognition tools
期望值计算 / 认知偏差扫描 / 贝叶斯更新
"""

import sys
import json
import argparse
from typing import Any


def expect_value(options: list[dict]) -> str:
    """
    计算各选项期望值
    输入格式: [{"name": "选项名", "outcomes": [{"prob": 0.7, "value": 100}, {"prob": 0.3, "value": -20}]}]
    """
    results = []
    for opt in options:
        ev = sum(o["prob"] * o["value"] for o in opt["outcomes"])
        results.append({"name": opt["name"], "expect_value": round(ev, 2)})
    results.sort(key=lambda x: x["expect_value"], reverse=True)
    out = ["期望值对比：", ""]
    for i, r in enumerate(results):
        badge = "🥇" if i == 0 else ("🥈" if i == 1 else "🥉")
        out.append(f"{badge} {r['name']}: {r['expect_value']}")
    return "\n".join(out)


def bias_scan(decision_text: str) -> str:
    """认知偏差扫描：给定决策文本，输出潜在偏差列表"""
    bias_map = {
        "确认偏误": ["我相信", "明显是", "毫无疑问", "肯定没错", "已经决定了"],
        "损失厌恶": ["不想失去", "不敢放弃", "万一失败", "亏了怎么办", "舍不得"],
        "锚定效应": ["第一次", "最初", "一开始", "原来以为", "参照"],
        "过度自信": ["肯定", "百分百", "绝对", "一定", "万无一失"],
        "现状偏见": ["还是算了", "保持现状", "再说吧", "先不动", "不变"],
        "情绪决策": ["太气了", "太激动", "睡不着", "不想等了", "冲动"],
    }
    found = []
    text_lower = decision_text.lower()
    for bias, keywords in bias_map.items():
        if any(kw in text_lower for kw in keywords):
            found.append(bias)
    if not found:
        return "✅ 未检测到明显认知偏差信号，但不代表完全没有偏差。"
    lines = ["⚠️ 检测到以下认知偏差风险：", ""]
    for b in found:
        lines.append(f"  • {b}")
    lines += ["", "建议：决策前用数据验证，用外部视角复核。"]
    return "\n".join(lines)


def bayes_update(prior: float, likelihood: float, marginal: float) -> str:
    """
    贝叶斯更新
    prior: P(H) 先验概率
    likelihood: P(E|H) 似然度
    marginal: P(E) 边缘概率
    """
    if marginal == 0:
        return "错误：边缘概率不能为0"
    posterior = (likelihood * prior) / marginal
    posterior = round(posterior, 4)
    lines = [
        "📊 贝叶斯更新结果：",
        f"  先验概率 P(H)      = {prior}",
        f"  似然度   P(E|H)    = {likelihood}",
        f"  边缘概率 P(E)      = {marginal}",
        f"  → 后验概率 P(H|E) = {posterior}",
        "",
    ]
    if posterior > prior:
        lines.append("↑ 证据支持假设，置信度上调")
    elif posterior < prior:
        lines.append("↓ 证据削弱假设，置信度下调")
    else:
        lines.append("→ 证据无影响，置信度不变")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="decision-cognition tools")
    sub = parser.add_subparsers(dest="cmd")

    p_ev = sub.add_parser("expect-value", help="期望值计算")
    p_ev.add_argument("--options", required=True, help='JSON格式选项列表')

    p_bias = sub.add_parser("bias-scan", help="认知偏差扫描")
    p_bias.add_argument("--text", required=True, help="决策描述文本")

    p_bayes = sub.add_parser("bayes", help="贝叶斯更新")
    p_bayes.add_argument("--prior", type=float, required=True)
    p_bayes.add_argument("--likelihood", type=float, required=True)
    p_bayes.add_argument("--marginal", type=float, required=True)

    args = parser.parse_args()

    if args.cmd == "expect-value":
        opts = json.loads(args.options)
        print(expect_value(opts))
    elif args.cmd == "bias-scan":
        print(bias_scan(args.text))
    elif args.cmd == "bayes":
        print(bayes_update(args.prior, args.likelihood, args.marginal))
    else:
        parser.print_help()
