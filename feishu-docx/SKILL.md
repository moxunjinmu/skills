---
name: feishu-docx
description: 飞书文档创建、读取、更新技能。支持将 Markdown 内容转换为飞书块格式并创建/更新文档。
license: Proprietary
---

# 飞书文档技能

负责飞书文档（Docx）的生命周期管理：创建、读取、更新、追加、块级操作。

## 何时使用

当你需要：
- 从 Markdown 文件创建飞书文档
- 读取飞书文档内容
- 更新或追加文档内容
- 将 Markdown 转换为飞书块格式（本地，不调 API）
- 追加 Markdown 内容到已有文档

## 工具层级建议

### 优先用 OpenClaw 内置工具 `feishu_doc` 的场景
- 读取文档（read）
- 写入文档（write）
- 追加内容（append）
- 创建文档（create）
- 列出块结构（list_blocks）
- 更新/删除块（update_block / delete_block）

内置工具覆盖大部分场景，是首选。

### 用本 skill 脚本的场景
当你需要这些能力时，用 `scripts/index.js`：
- **从 Markdown 文件批量创建文档**（`create` 命令）
- **追加 Markdown 内容到已有文档**（`append` 命令）
- **本地预览 Markdown → 飞书块格式转换**（`convert` 命令，不走 API）
- 底层 API 验证

## 凭证

脚本从 `~/.openclaw/openclaw.json` 自动读取飞书凭证，无需手动设置环境变量。

## 脚本

主脚本：`scripts/index.js`

```bash
cd ~/.openclaw/workspace/skills/feishu-docx/scripts
```

### 命令

```bash
# 从 Markdown 文件创建新文档
node index.js create <markdown-file> [title]

# 追加 Markdown 内容到现有文档
node index.js append <document-token> <markdown-file>

# 读取文档内容
node index.js read <document-token> [obj-token] [obj-type]

# 将 Markdown 转换为飞书块格式（本地，不调 API）
node index.js convert <markdown-file> [output-file]
```

### 本地转换器

`scripts/markdown-to-blocks.js` — 可独立使用，将 Markdown 转飞书块格式：

```bash
node markdown-to-blocks.js <input.md> [output.json]
```

## 内置 feishu_doc 实战技巧

### 已知限制

内置 markdown 解析器有以下限制，违反会返回 400 错误：

1. **不支持 Markdown 表格** — 用列表替代
2. **不支持嵌套列表** — 缩进的子列表项会导致 400，必须拍平为同级列表
3. **不支持 `---` 分隔线** — 直接省略或用空行替代
4. **单次写入内容不宜过长** — 建议分段写入

### 正确写法

```markdown
## 标题

- 第一点说明
- 第二点说明
- 第三点的子内容也写成同级列表项
- 第四点说明
```

### 错误写法（会 400）

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

| Block 类型 | 说明 | Markdown |
|-----------|------|---------|
| Heading1 | 一级标题 | `# 标题` |
| Heading2 | 二级标题 | `## 标题` |
| Heading3 | 三级标题 | `### 标题` |
| Bullet | 无序列表 | `- 列表项` |
| Ordered | 有序列表 | `1. 列表项` |
| Text | 普通文本段落 | 普通文字 |
| Code | 代码块 | ` ```code``` ` |
| Quote | 引用 | `> 引用内容` |
| Divider | 分隔线 | `---` |

## 注意事项

1. 写完必须 `read` 验证 + 发链接给用户
2. 大文档分段写入，避免单次内容过长
3. 嵌套列表一律拍平为同级
4. 需要表格展示的数据，考虑用多维表格（Bitable）替代
5. wiki 创建的文档，obj_token = doc_token

## 多维表格（Bitable）

Bitable 能力已独立拆分到：`skills/feishu-bitable/`

涉及记录 CRUD、字段管理、批量清理、关联字段调试时，请改用 `feishu-bitable` skill。

## 参考

- 知识库正式资产落位规范：`../docs/workflows/knowledge-base-rules.md`
- Bitable 独立 skill：`../feishu-bitable/SKILL.md`
- Wiki 节点编排：`../feishu-wiki/SKILL.md`
