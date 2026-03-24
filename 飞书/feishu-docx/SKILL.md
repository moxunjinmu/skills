---
name: feishu-docx
description: 飞书文档创建、读取、更新技能。支持将 Markdown 内容转换为飞书块格式并创建/更新文档。
license: Proprietary
---

# 飞书文档技能

帮助用户创建、读取、更新飞书文档。支持 Markdown 内容转换为飞书块格式。

## 工具选择

有两种方式操作飞书文档：

1. **内置 `feishu_doc` 工具**（推荐日常使用）：直接在对话中调用，支持 read/write/append/create/list_blocks/get_block/update_block/delete_block
2. **飞书 REST API 脚本**：适合内置工具无法覆盖的场景（如 bitable 记录操作）

## 内置 feishu_doc 写入技巧（实战总结）

### ⚠️ 已知限制

内置 `feishu_doc` 的 markdown 解析器有以下限制，违反会返回 400 错误：

1. **不支持 Markdown 表格** — 用列表替代
2. **不支持嵌套列表** — 缩进的子列表项会导致 400，必须拍平为同级列表
3. **不支持 `---` 分隔线** — 直接省略或用空行替代
4. **单次写入内容不宜过长** — 超过一定长度可能失败，建议分段

### ✅ 正确写法

```markdown
## 标题

- 第一点说明
- 第二点说明
- 第三点的子内容也写成同级列表项
- 第四点说明
```

### ❌ 错误写法（会 400）

```markdown
## 标题

| 列1 | 列2 |        ← 表格不支持
|------|------|
| 值1 | 值2 |

---                     ← 分隔线不支持

- 第一点
  - 子项1              ← 嵌套列表不支持
  - 子项2
```

### 长文档写入策略

1. 用 `write` 写入文档开头（标题 + 简介）
2. 用 `append` 分段追加后续内容
3. 每段控制在 10-15 个列表项以内
4. 写完用 `read` 验证内容完整性

### 知识库文档创建流程

1. `feishu_wiki` create → 拿到 node_token + obj_token
2. obj_token 就是 doc_token，用于 `feishu_doc` 操作
3. 文档链接格式：`https://moxunjinmu.feishu.cn/wiki/{node_token}`

## 飞书 API 块格式

飞书文档使用块（Block）类型组织内容：

- Heading1：一级标题（# 标题）
- Heading2：二级标题（## 标题）
- Heading3：三级标题（### 标题）
- Bullet：无序列表（- 列表项）
- Ordered：有序列表（1. 列表项）
- Text：普通文本段落
- Code：代码块
- Quote：引用（> 引用内容）

## 使用方法

### 创建新文档

```json
{ "action": "create", "title": "文档标题", "folder_token": "fldcnXXX" }
```

### 写入内容（替换全部）

```json
{ "action": "write", "doc_token": "ABC123def", "content": "# 标题\n\n内容..." }
```

### 追加内容

```json
{ "action": "append", "doc_token": "ABC123def", "content": "追加的内容" }
```

### 读取文档

```json
{ "action": "read", "doc_token": "ABC123def" }
```

返回 title、content（纯文本）、block_count、block_types。如果有结构化内容（表格、图片），用 list_blocks 获取完整数据。

## 注意事项

1. 写完必须 `read` 验证 + 发链接给用户
2. 大文档分段写入，避免单次内容过长
3. 嵌套列表一律拍平为同级
4. 需要表格展示的数据，考虑用多维表格（bitable）替代
5. wiki 创建的文档，obj_token = doc_token

## 多维表格（Bitable）踩坑记录

操作脚本：`scripts/feishu-bitable.py`

### 支持的记录操作

- `list-records`：列出记录
- `create-record`：创建记录
- `update-record`：更新记录
- `delete-record`：删除单条记录
- `batch-delete-records`：批量删除记录（一次最多 500 条）
- `create-duplex-link`：创建双向关联字段（type 21）

### 字段管理

- 主键字段（is_primary=true）不能删除，只能改名
- PUT 改名字段时必须带 `type` 参数，否则返回 "field validation failed"
  - 正确：`{"field_name": "新名字", "type": 1}`
  - 错误：`{"field_name": "新名字"}` → 400
- 新建 bitable 默认带 4 个字段（Text/Single option/Date/Attachment）和 10 条空记录
- 建议流程：先创建自定义字段 → 改名主键字段 → 删除多余默认字段 → 清空默认空记录

### 字段类型编号

| type | 名称 | 可创建 | 值格式 |
|------|------|--------|--------|
| 1 | 文本 | ✓ | `"文本"` |
| 2 | 数字 | ✓ | `123.45` |
| 3 | 单选 | ✓ | `"选项名"` |
| 4 | 多选 | ✓ | `["选项1", "选项2"]` |
| 5 | 日期 | ✓ | `1708387200000`（毫秒时间戳） |
| 7 | 复选框 | ✓ | `true` / `false` |
| 11 | 人员 | ✓ | `[{"id": "ou_xxx"}]` |
| 15 | URL链接 | ✓ | `{"link": "https://...", "text": "显示文本"}` |
| 17 | 附件 | ✓ | `[{"file_token": "..."}]` |
| 18 | 单向关联 | ✓ | `["recXXX", "recYYY"]`（record_id 数组） |
| 21 | 双向关联(DuplexLink) | ✓ | `["recXXX", "recYYY"]`（record_id 数组） |

### 创建关联字段

双向关联字段（type 21）创建时只需传目标表 ID，API 自动在目标表创建反向字段：

```json
POST /bitable/v1/apps/{app_token}/tables/{table_id}/fields
{
  "field_name": "关联项目",
  "type": 21,
  "property": {
    "table_id": "目标表的table_id"
  }
}
```

返回中包含 `back_field_id`（反向字段 ID）和 `back_field_name`（反向字段名）。

### 记录操作

- 批量删除一次最多 500 条
- 创建记录时字段名必须精确匹配（区分大小写）
