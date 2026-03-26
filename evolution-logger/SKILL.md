---
name: evolution-logger
description: 进化事件记录 + 效果追踪。统一管理所有进化事件日志，提供查询、分析、可视化能力，是进化体系的数据基础设施。
when:
  - evolution-trigger 触发进化动作时记录
  - self-evaluator 完成评估后记录
  - Boss 说「查看进化记录」「进化历史」「进化报告」
tags:
  - 进化
  - 日志
  - 自我评估
  - 数据基础设施
---

# Evolution Logger - 进化记录器

## 概述

进化记录器是进化体系的数据基础设施，统一管理所有进化事件日志，提供写入、查询、统计和导出能力。

## 日志格式

日志文件路径：`~/.openclaw/workspace/memory/evolution-log.jsonl`

每行一个 JSON 事件，格式如下：

```json
{
  "ts": "2026-03-26T16:30:00+08:00",
  "type": "evaluation|evolution|decision|lesson",
  "level": "pcpec|ppec|piec|psec",
  "data": {},
  "tags": []
}
```

### 事件类型（type）

| type | 说明 |
|------|------|
| `evaluation` | 自我评估结果（来自 self-evaluator） |
| `evolution` | 进化触发记录（来自 evolution-trigger） |
| `decision` | 重大决策记录（关联 decision-cognition） |
| `lesson` | 失败教训/踩坑记录 |

### 级别（level）

| level | 说明 |
|-------|------|
| `pcec` | PCEC 级别（最高） |
| `ppec` | PPEC 级别 |
| `piec` | PIEC 级别 |
| `psec` | PSEC 级别 |

> ⚠️ PCEC 已统一为 `pcec`（旧 `pcpec` 已废弃）。

### data 字段示例

**evaluation 事件：**
```json
{"accuracy": 8, "efficiency": 6, "task_type": "code-review", "notes": ""}
```

**evolution 事件：**
```json
{"expected_improvements": ["accuracy+1", "speed+10%"], "trigger_reason": "evaluation_threshold", "parent_event_id": ""}
```

**decision 事件：**
```json
{"decision": "切换到 MiniMax-M2.7-highspeed", "reason": "效率提升", "alternatives_considered": ["claude-3.5"]}
```

**lesson 事件：**
```json{"lesson": "飞书消息长度超限导致截断", "context": "长消息未拆分直接发送", "avoidance": "超过200字的消息需分块发送"}
```

## 核心能力

### 1. 写入（add）
接收各模块推送的进化事件，自动补充时间戳。

### 2. 查询（query）
按时间、类型、级别过滤历史记录。

### 3. 统计（stats）
生成进化频率/效果趋势报告，各类型事件分布。

### 4. 导出（export）
生成 Markdown 格式进化报告，支持指定时间范围。

### 5. 趋势追踪（trend）
从 evaluation 事件中提取指定指标的历史趋势，用于衡量进化效果。

## CLI 用法

```bash
# 添加进化事件
evolution-logger add --type evaluation --level pcpec --data '{"accuracy": 8, "efficiency": 6}'
evolution-logger add --type evolution --level pcpec --data '{"expected_improvements": ["accuracy+1"]}'

# 查询最近7天的评估事件
evolution-logger query --type evaluation --days 7

# 查询所有类型，最近30天
evolution-logger query --days 30

# 生成30天统计报告
evolution-logger stats --days 30

# 导出 Markdown 进化报告
evolution-logger export --output evolution-report.md --days 30

# 追踪 accuracy 指标趋势
evolution-logger trend --metric accuracy
```

## 进化效果追踪机制

每次 PCEC 进化后：
1. 记录 `expected_improvements`（预期改进点）
2. 下次同类任务执行时，从 evaluation 事件中提取实际指标
3. 对比预期 vs 实际，评估进化效果
4. 将对比结果写入新的 evaluation 事件，形成闭环

## 依赖

- Python 标准库（argparse, json, datetime, collections, pathlib）
- 无第三方依赖
