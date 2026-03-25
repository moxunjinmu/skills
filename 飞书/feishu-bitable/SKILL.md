---
name: feishu-bitable
description: 飞书多维表格（Bitable）操作技能。用于记录 CRUD、字段管理、批量清理、知识库内表整理，以及调试关联字段/双向关联等场景。
---

# 飞书多维表格技能

负责飞书多维表格（Bitable）操作与自动化，是飞书技能体系中的核心数据层。

## 何时使用

当你需要：
- 列出 / 创建 / 更新 / 删除记录
- 批量删除空白记录
- 列出 / 创建 / 删除字段
- 调试关联字段、双向关联字段（DuplexLink）
- 清理新建 bitable 的默认空行与占位列
- 用脚本直连飞书 Bitable REST API

## 工具层级建议

### 优先用 OpenClaw 内置工具的场景
- `feishu_bitable_get_meta` — 解析 Bitable URL
- `feishu_bitable_list_fields` — 列出字段
- `feishu_bitable_list_records` — 列出记录
- `feishu_bitable_get_record` — 查单条记录
- `feishu_bitable_create_record` — 创建记录
- `feishu_bitable_update_record` — 更新记录
- `feishu_bitable_create_app` — 创建 Bitable 应用
- `feishu_bitable_create_field` — 创建字段

### 用本 skill 脚本的场景
- 删除记录 / 批量删除记录
- 删除字段
- 透传字段 property
- 调试 DuplexLink / SingleLink
- **清理空白记录**（内置工具未覆盖）
- **格式化字段类型列表**（内置工具未覆盖）
- 底层 API 验证

## 凭证

脚本从 `~/.openclaw/openclaw.json` 自动读取飞书凭证，无需手动设置环境变量。

## 脚本

主脚本：`scripts/feishu-bitable.py`

```bash
cd ~/.openclaw/workspace/skills/feishu-bitable/scripts
```

### 记录操作

```bash
# 列出所有记录（自动翻页）
python3 feishu-bitable.py list-records <app_token> <table_id> [--page-size N]

# 创建记录（fields 为 JSON 或 .json 文件路径）
python3 feishu-bitable.py create-record <app_token> <table_id> <fields.json>

# 更新记录
python3 feishu-bitable.py update-record <app_token> <table_id> <record_id> <fields.json>

# 删除单条记录
python3 feishu-bitable.py delete-record <app_token> <table_id> <record_id>

# 批量删除（最多500条/次，record_ids 为 JSON 数组或 .json 文件）
python3 feishu-bitable.py batch-delete-records <app_token> <table_id> <record_ids.json>
```

### 字段操作

```bash
# 列出所有字段
python3 feishu-bitable.py list-fields <app_token> <table_id>

# 格式化查看字段类型（字段ID / 类型ID / 类型名 / 字段名）
python3 feishu-bitable.py field-types <app_token> <table_id>

# 创建字段（type: 1=文本, 3=单选, 4=多选, 5=日期, 21=双向关联…）
python3 feishu-bitable.py create-field <app_token> <table_id> <field_name> <type> [--property property.json]

# 删除字段
python3 feishu-bitable.py delete-field <app_token> <table_id> <field_id>

# 创建双向关联字段
python3 feishu-bitable.py create-duplex-link <app_token> <table_id> <field_name> <target_table_id> [--back-name NAME]
```

### 清理操作

```bash
# 清理空白记录（dry-run 模式：只报告，不删除）
python3 feishu-bitable.py cleanup-empty <app_token> <table_id> --dry-run

# 正式清理
python3 feishu-bitable.py cleanup-empty <app_token> <table_id>
```

## 常见规则

### 1. 主键字段不能删除
主键字段（`is_primary=true`）只能改名，不能删除。

### 2. 新建表默认自带垃圾内容
通常会有：
- 10 条空记录
- 默认字段：`Text` / `Single option` / `Date` / `Attachment`

建完表不要直接交付，先清理。

### 3. 关联字段值格式
- 单向关联 / 双向关联的记录值一般是 `record_id` 数组
- 字段创建时 `property` 结构要求严格，必要时需单独调试 API

### 4. 字段类型速查

| type | 类型 |
|------|------|
| 1 | 文本 |
| 2 | 数字 |
| 3 | 单选 |
| 4 | 多选 |
| 5 | 日期 |
| 7 | 复选框 |
| 11 | 用户 |
| 13 | 电话 |
| 15 | URL |
| 17 | 附件 |
| 18 | 关联 |
| 19 | 查我 |
| 20 | 公式 |
| 21 | 双向关联 |
| 22 | 地理位置 |
| 23 | 群组 |
| 1001 | 创建时间 |
| 1002 | 修改时间 |
| 1003 | 创建人 |
| 1004 | 修改人 |
| 1005 | 自动编号 |

## 当前已知难点

### DuplexLink
已知问题：
- 直接传 `type=21` + `property.table_id` 在部分场景仍会报 `DuplexLinkFieldPropertyError`
- 当前脚本已支持该命令，但仍需要继续针对不同表结构调试

因此：
- 删除 / 批量删 / 字段删 已可稳定使用
- DuplexLink 作为后续持续攻关项

## 参考

- 如果任务涉及知识库落位与表创建流程，结合阅读：
  - `../docs/workflows/feishu-bitable-workflow.md`
  - `../docs/workflows/knowledge-base-rules.md`
