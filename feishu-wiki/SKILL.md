---
name: feishu-wiki
description: 飞书知识库（Wiki）节点与挂载编排。用于知识库空间/节点查询、创建、移动、重命名、删除，以及批量文档挂载。适用于正式资产落位路径治理、知识库结构梳理等场景。
---

# 飞书知识库技能

负责飞书知识库（Wiki）的节点编排与资产落位，是飞书技能体系中的知识组织层。

## 何时使用

当你需要：
- 查询知识库空间和节点结构
- 在知识库中创建新节点
- 移动或重命名知识库节点
- 删除不需要的节点
- 批量将已有文档挂入知识库
- 获取节点的完整路径（breadcrumb）
- 打印知识库目录树

## 工具层级建议

### 优先用 OpenClaw 内置工具 `feishu_wiki` 的场景
- 列出知识库空间
- 列出空间下的节点
- 获取节点详情
- 创建节点
- 移动节点
- 重命名节点

内置工具已经覆盖了大部分基础操作，且有 OpenClaw 直接支持。

### 用本 skill 脚本的场景
当你需要这些内置工具不支持的能力时，用 `scripts/feishu-wiki.py`：
- **删除节点**（内置工具不支持）
- **批量将已有文档挂入知识库节点**（`attach-docs`）
- **获取节点祖先路径**（breadcrumb，逐级向上爬）
- **递归打印目录树**（`space-tree`）
- **跨空间搜索节点**（`search`）

## 凭证

脚本从 `~/.openclaw/openclaw.json` 自动读取飞书凭证，无需手动设置环境变量。

## 脚本

主脚本：`scripts/feishu-wiki.py`

```bash
cd ~/.openclaw/workspace/skills/feishu-wiki/scripts
```

### 基础查询

```bash
# 列出所有知识库空间
python3 feishu-wiki.py list-spaces

# 列出空间下的节点（默认根节点）
python3 feishu-wiki.py list-nodes <space_id>

# 列出指定父节点下的子节点
python3 feishu-wiki.py list-nodes <space_id> --parent <node_token>

# 获取节点详情
python3 feishu-wiki.py get-node <node_token>

# 在所有知识库中按标题搜索节点
python3 feishu-wiki.py search <keyword>
```

### 节点操作

```bash
# 创建节点
python3 feishu-wiki.py create-node <space_id> <title> [--parent NODE_TOKEN] [--obj-type TYPE] [--obj-token TOKEN]

# 重命名节点
python3 feishu-wiki.py rename-node <space_id> <node_token> <new_title>

# 移动节点
python3 feishu-wiki.py move-node <space_id> <node_token> [--target-space SPACE_ID] [--target-parent NODE_TOKEN]

# 删除节点
python3 feishu-wiki.py delete-node <space_id> <node_token>
```

### 路径与结构

```bash
# 获取节点的完整祖先路径（breadcrumb）
python3 feishu-wiki.py node-path <node_token>

# 递归打印知识库目录树
python3 feishu-wiki.py space-tree <space_id> [--depth N]
```

### 批量挂载

```bash
# 将已有文档批量挂入知识库节点下（创建 wiki 节点引用）
python3 feishu-wiki.py attach-docs <space_id> <parent_node_token> <doc_token>...
```

`obj-type` 选项：`docx`(默认) / `sheet` / `bitable` / `mindnote` / `file` / `doc` / `slides`

## 节点类型说明

| obj_type | 说明 |
|----------|------|
| `docx` | 飞书文档 |
| `sheet` | 电子表格 |
| `bitable` | 多维表格 |
| `mindnote` | 思维笔记 |
| `file` | 文件 |
| `doc` | 旧版文档 |
| `slides` | 幻灯片 |

### node_type 参数说明（关键）

创建节点时，`node_type` 控制节点与对象的关系：

| node_type | 含义 | 使用场景 |
|-----------|------|---------|
| `origin` | 在知识库内**新建**一个对象（文档/Bitable/表格） | 在 wiki 内创建新的 Bitable 应用时使用 |
| `shortcut` | 创建**快捷方式**，引用已有对象（需指定 `origin_node_token`） | 跨空间引用时使用 |
| 默认（不传） | 创建空节点，关联已有对象 | 仅设置 `obj_token` 时 |

**标准用法：**
```bash
# 在知识库内新建 Bitable 并直接挂载为 wiki 节点
python3 feishu-wiki.py create-node <space_id> <title> \
  --parent <parent_node_token> \
  --obj-type bitable \
  --obj-token <bitable_app_token>
# API 实际请求体: { node_type: "origin", obj_type: "bitable", obj_token: "...", ... }
```

## 知识库内创建 Bitable 标准流程

**目标**：在知识库节点下新建一个 Bitable 应用并直接挂载

**Step 1**：在目标父节点下创建 Bitable 类型的 wiki 节点
```bash
python3 feishu-wiki.py create-node <space_id> "Skills 技能库" \
  --parent <parent_node_token> \
  --obj-type bitable
# 返回新的 app_token，即为知识库内的 Bitable 应用
```

**Step 2**：用返回的 `app_token` 配置字段（参考 `feishu-bitable` skill）

**Step 3**：写入记录

**注意**：脚本的 `create-node` 目前不传 `node_type`，底层 API 会自动设为 `origin`。如遇 `shortcut` 场景需跨空间引用，需直接调用 API 并显式传 `node_type=shortcut` + `origin_node_token`。

## Wiki-Doc 联动工作流

1. `feishu_wiki get-node <node_token>` → 拿到 `obj_token`
2. `feishu_doc read <obj_token>` → 读取文档内容
3. `feishu_doc write <obj_token> <content>` → 更新文档内容

## 注意事项

- **删除节点前先确认无子节点**：有子节点的父节点无法直接删除，需先清理子节点
- **批量挂载 `attach-docs`**：用于将已创建的独立文档批量引入知识库目录结构，而非创建新文档
- **`space-tree` 深度限制**：默认不限深度，`--depth N` 可限制显示层数，避免在大型知识库中输出过长

## 参考

- 知识库正式资产落位规范：`../docs/workflows/knowledge-base-rules.md`
- Bitable 新建注意事项：`../feishu-bitable/SKILL.md`
