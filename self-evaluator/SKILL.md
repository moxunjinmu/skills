---
name: self-evaluator
description: 任务质量评分 + 能力雷达。量化评估每次任务执行质量，生成能力短板报告，为进化提供数据依据
when:
  - Boss 说「评估一下」「我的能力怎么样」「哪里做得好/不好」
  - evolution-trigger 触发 PCEC/PPEC 时调用
  - 每次任务完成后自动评估（被其他技能调用）
tags:
  - 自我评估
  - 能力雷达
  - 进化
---

# Self-Evaluator · 自我评估器

## 概述

对每次任务执行进行 5 维度量化评估，输出能力雷达报告和短板分析，结果写入 `memory/evolution-log.jsonl`，供进化触发器（evolution-trigger）读取判断。

## 评估维度

| 维度 | 含义 | 满分 |
|------|------|------|
| 准确性 | 任务结果正确吗？答案/产出是否与需求匹配 | 10 |
| 效率 | 用了多少轮对话/时间？是否简洁直接 | 10 |
| 安全性 | 有没有触碰红线/泄露风险？操作是否合规 | 10 |
| 完整性 | 需求覆盖全了吗？有遗漏吗？ | 10 |
| 主动性 | 有没有主动发现并解决问题？有没有超出预期 | 10 |

## 评分规则

### 自动评分逻辑

由调用方根据以下信号综合打分（0-10）：

- **准确性**：工具返回状态=success + 任务完成标志 + 结果验证
- **效率**：对话轮次 ≤ 3 轮得 8-10，4-6 轮得 5-7，> 6 轮得 0-4；时间同理
- **安全性**：无危险操作/泄露/违规 → 9-10；小瑕疵 → 6-8；明显风险 → 0-5
- **完整性**：需求全部覆盖 → 8-10；部分覆盖 → 4-7；有明显遗漏 → 0-3
- **主动性**：主动发现问题/给出建议 → 8-10；按要求执行 → 5-7；被动等待 → 0-4

### Boss 反馈信号

- **positive**（夸奖/确认完成）：各维度 +1-2 分，上限 10
- **negative**（批评/指出问题）：各维度 -1-2 分，下限 0
- **neutral**：不调整

### 评分函数

```python
def compute_score(base: float, feedback: str) -> float:
    delta = {"positive": 1.5, "negative": -1.5, "neutral": 0}.get(feedback, 0)
    return max(0.0, min(10.0, base + delta))
```

## 输出格式

### 能力雷达（文本版）

```
## 能力雷达
准确性: ████████░░ 8.0
效率:   ██████░░░░ 6.0
安全性: █████████░ 9.0
完整性: █████░░░░░ 5.0
主动性: ███████░░░ 7.0

## 短板TOP3
1. 完整性（5.0）：需求覆盖不完整，存在明显遗漏项
2. 效率（6.0）：对话轮次偏多，可更直接简洁
3. 准确性（7.0）：结果有小错误，需加强验证

## 进化建议
下次任务应重点关注：完整性和效率，建议接任务后先列清单对标需求再执行
```

### 雷达图（文本表格）

5 维度等角度排列，雷达图数据用坐标对表示：

```
         准确性(10)
            ▲
           / \
          /   \
         /     \
  安全性(9)◄────►效率(6)
         \     /
          \   /
           \ /
            ▼
         完整性(5)
```

## 能力趋势报告（radar --history N）

从 `memory/evolution-log.jsonl` 读取最近 N 条 `evaluation` 类型事件，输出：

- 各维度平均值/最高值/最低值
- 趋势判断（上升/下降/稳定）
- 持续弱点
- 改进优先级排序

## 与 Evolution-Trigger 联动

评估结果自动输出标准事件 JSON 供保存/管道，格式：

```json
{
  "type": "evaluation",
  "level": "pcec",
  "source": "self-evaluator",
  "task_id": "MO-20260326-S001",
  "data": {
    "accuracy": 8.0,
    "efficiency": 6.0,
    "safety": 9.0,
    "completeness": 5.0,
    "proactiveness": 7.0,
    "overall": 7.0,
    "feedback": "neutral",
    "weaknesses": ["完整性（5.0）", "效率（6.0）"],
    "evolution_suggestion": "完整性和效率，建议接任务后先列清单对标需求再执行"
  },
  "tags": []
}
```

evolution-trigger 读取该文件，当 overall < 6.0 或任一维度 < 5.0 持续 3 次时触发 PCEC/PPEC。

## 命令行接口

```bash
# 单次评分（默认只输出报告，不写日志）
self-evaluator score --accuracy 8 --efficiency 6 --safety 9 --completeness 5 --proactiveness 7 [--feedback positive]

# 单次评分并写入日志
self-evaluator score --accuracy 8 --efficiency 6 --safety 9 --completeness 5 --proactiveness 7 --save

# 能力趋势（读取最近N条历史）
self-evaluator radar --history 10

# 当前短板报告
self-evaluator短板
```

> 📌 默认行为变更：score 不再自动写日志，日志写入需显式加 `--save`。这样避免了 self-evaluator 与 evolution-logger 重复写入的问题。

## 与其他技能的关系

| 技能 | 关系 |
|------|------|
| evolution-trigger | 读取 evaluation 日志，判断是否触发 PCEC/PPEC |
| evolution-log | 日志持久化存储 |
| memory-manager | 共享 `memory/evolution-log.jsonl` 作为长期记忆数据源 |
