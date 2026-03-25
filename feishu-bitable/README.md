# 飞书多维表格技能

这是面向飞书 Bitable 的独立技能，负责：
- 记录 CRUD
- 字段 CRUD
- 批量删除空白记录
- 字段 property 调试
- 关联 / 双向关联实验

## 主脚本

`scripts/feishu-bitable.py`

## 依赖

使用前需要准备：
- `FEISHU_TENANT_ACCESS_TOKEN` 或 `FEISHU_USER_ACCESS_TOKEN`

## 常用命令

```bash
cd ~/.openclaw/workspace/skills/feishu-bitable/scripts

# 列记录
python3 feishu-bitable.py list-records <app_token> <table_id>

# 删单条记录
python3 feishu-bitable.py delete-record <app_token> <table_id> <record_id>

# 批量删记录
python3 feishu-bitable.py batch-delete-records <app_token> <table_id> '["rec1","rec2"]'

# 列字段
python3 feishu-bitable.py list-fields <app_token> <table_id>

# 删除字段
python3 feishu-bitable.py delete-field <app_token> <table_id> <field_id>

# 透传 property 创建字段
python3 feishu-bitable.py create-field <app_token> <table_id> "关联提示词" 21 '{"table_id":"tblTarget","back_field_name":"关联网站"}'

# 创建双向关联字段 helper
python3 feishu-bitable.py create-duplex-link <app_token> <table_id> "关联提示词" <target_table_id> "关联网站"
```

## 说明

### 删除记录
- 支持单删
- 支持批量删除（一次最多 500 条）

### 删除字段
- 主键字段不能删除
- 删除前先 `list-fields` 确认 `field_id`

### 关联字段
- `create-field` 适合精细调试 property
- `create-duplex-link` 是便捷命令
- 如果出现 `DuplexLinkFieldPropertyError`，说明还需要针对当前表结构继续调试

## 推荐工作流

1. 用 `feishu_bitable_get_meta` 确认 app/table 身份
2. 用内置工具先做常规读取/写入
3. 需要删除、批量清理、字段底层调试时，切换到本脚本
