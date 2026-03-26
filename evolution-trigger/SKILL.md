---
name: evolution-trigger
description: 进化节奏控制器。根据任务结果、会话状态、时间触发四层进化（PCEC/PPEC/PIEC/PSEC），判断是否需要触发进化动作。
when:
  - Boss 说「复盘」「总结进化」「检查进化」「进化状态」
  - 会话结束信号（/new、/reset）
  - 任务失败后首次对话
  - 每周日20:00定时触发（cron）
---

# evolution-trigger（进化触发器）

## 定位

进化节奏控制器。通过感知任务结果、会话状态与时间节律，动态决定是否触发进化动作，并将进化记录沉淀为可检索的经验资产。

## 何时激活

| 触发场景 | 关键词/信号 | 对应层级 |
|---------|------------|---------|
| 任务完成/失败时 | 工具返回 failure / 异常 | PCEC |
| 会话结束 | /new、/reset、"先这样" | PPEC |
| Boss 主动询问 | 复盘、总结进化、检查进化、进化状态 | 任意层级 |
| 任务失败后首次对话 | 检测到失败 flag | PCEC |
| 每周日 20:00 | cron 定时 | PIEC |
| 每月末 | cron 定时 | PSEC |

## 四层进化节奏定义

### PCEC — 微进化（每一次任务级）
- **触发频率**：实时，每任务结束时
- **典型场景**：工具调用失败、API 返回非预期结果、用户纠正行为
- **改动范围**：单次工具调用方式、提示词片段、参数微调
- **验证方式**：下一轮同类任务是否不再出错

### PPEC — 小进化（每日会话级）
- **触发频率**：每次会话结束时（/new、/reset）
- **典型场景**：今日完成了新类型任务、踩了坑、有决策结论
- **改动范围**：经验规则新增/更新、行为模式库调整
- **验证方式**：次日遇到同类场景是否自动复用新规则

### PIEC — 中进化（每周日级）
- **触发频率**：每周日 20:00，结合 PCEC 汇总
- **典型场景**：本周任务数量、成功/失败率、能力短板浮现
- **改动范围**：Skill 迭代、记忆结构升级、流程 SOP 优化
- **验证方式**：下周该类任务成功率是否提升

### PSEC — 大进化（每月级）
- **触发频率**：每月末
- **典型场景**：技能使用频率异常、用户反馈积累、方向偏差显著
- **改动范围**：架构重构、方向调整、新能力引入决策
- **验证方式**：下月用户满意度或任务吞吐量是否改善

## 触发判断逻辑（自然语言决策树）

### PCEC 触发判断

```
当任务失败时：
  → 是否为首次失败该类型？
      是 → 记录失败模式，微调工具调用参数，触发 PCEC
      否 → 是否与上次失败相同根因？
          是 → 升级问题等级，触发 PCEC 并通知 PPEC 记录
          否 → 记录新失败类型，触发 PCEC
  → PCEC 动作：更新失败模式库 → 写入 memory/evolution-log.jsonl
```

### PPEC 触发判断

```
当会话结束信号到达时：
  → 检查今日 memory/YYYY-MM-DD.md 是否有新增内容？
      有新增经验 → 提取经验规则，入库到 memory/rules/
      有失败教训 → 写入失败教训库
      有决策记录 → 同步到 MEMORY.md
      无新增 → 本次不触发 PPEC
  → PPEC 动作：生成规则更新摘要 → 追加到 evolution-log.jsonl
```

### PIEC 触发判断

```
每周日 20:00 自动触发（cron）：
  → 汇总本周所有 evolution-log.jsonl 事件
  → 计算：任务总数 / 成功数 / 失败数 / 成功率
  → 识别失败率最高的任务类型 → 定义为本周主要矛盾
  → 该矛盾是否在连续 2 周以上重复出现？
      是 → 触发 Skill 迭代建议（PIEC）
      否 → 仅记录，不触发 PIEC
  → PIEC 动作：输出技能迭代建议报告 → 写入 docs/weekly-evolution.md
```

### PSEC 触发判断

```
每月末自动触发：
  → 汇总当月所有 PIEC 报告
  → 检查：哪些能力短板连续 3 周以上未解决？
  → 检查：用户是否有明确反馈指向某类问题？
  → 检查：当前技能栈使用频率是否有明显偏移？
  → 任一条件满足 → 触发 PSEC 大进化评估
  → PSEC 动作：架构/方向评估报告 → 走 decision-cognition 流程
```

## 进化动作输出格式

| 触发层级 | 输出动作 | 记录位置 |
|---------|---------|---------|
| PCEC | 失败模式记录 / 工具参数调整 | `memory/evolution-log.jsonl` |
| PPEC | 经验规则新增 / 更新 | `memory/rules/` + `evolution-log.jsonl` |
| PIEC | 技能迭代建议报告 | `docs/weekly-evolution.md` + `evolution-log.jsonl` |
| PSEC | 架构评估与方向建议 | `docs/monthly-evolution.md` + `evolution-log.jsonl` |

## 与现有组件的联动

### 联动 `monica-three-tier-memory`
- PPEC/PIEC 触发时 → 调用三级记忆写入接口
- 写入内容：经验规则 → 中期记忆；重要结论 → 长期记忆
- 联动文件：`~/.openclaw/workspace/skills/monica-three-tier-memory/SKILL.md`

### 联动 `decision-cognition`
- PSEC 触发时 → 重大方向决策走决策认知流程
- 输入：PSEC 评估报告摘要
- 流程：矛盾识别（矛盾论）→ 方案验证（实践论）→ 决策输出
- 联动文件：`~/.openclaw/workspace/skills/decision-cognition/SKILL.md`

## 毛泽东思想对照

### 矛盾论 — 识别主要进化矛盾

> 在每一事物的诸多矛盾中，必有一个主要矛盾，它处于支配地位，对事物发展起决定作用。

进化判断同理：每次 PIEC/PSEC 触发时，从诸多失败和短板中识别主要矛盾（失败率最高的任务类型），集中资源优先解决主要矛盾，而非平均用力。

### 实践论 — 进化效果用行动验证

> 认识从实践开始，实践是检验认识真理性的唯一标准。

每个进化动作（PCEC 微调到 PSEC 架构调整）都必须设置验证条件：
- PCEC 验证：下一轮同类任务是否成功
- PPEC 验证：次日是否自动复用新规则
- PIEC 验证：下周该类任务成功率是否提升
- PSEC 验证：下月用户满意度是否改善

未经实践验证的进化结论，不入库、不固化。

## 数据文件

- **状态文件**：`~/.openclaw/workspace/memory/evolution-state.json`
- **日志文件**：`~/.openclaw/workspace/memory/evolution-log.jsonl`
- **规则库**：`~/.openclaw/workspace/memory/rules/`
- **周期报告**：`~/.openclaw/workspace/docs/weekly-evolution.md`、`docs/monthly-evolution.md`

## CLI 工具

```bash
# 检查指定层级是否应触发
evolution-trigger check --mode pcpec|ppec|piec|psec

# 查看当前进化状态概览
evolution-trigger status

# 记录一次进化事件
evolution-trigger log --level pcpec|ppec|piec|psec --action "动作描述"
```
