---
name: feishu-perm
description: 飞书权限与协作者管理技能。用于查询、添加、移除文档/云盘/多维表格/知识库等资产的协作者权限。
---

# 飞书权限技能

负责飞书权限与协作者管理，是飞书技能体系中的横切能力层。

## 何时使用

当你需要：
- 查询某个文档/表格的当前协作者列表
- 给用户或群聊授予查看/编辑/完全控制权限
- 移除某个协作者的权限
- 批量添加多个协作者

## 工具层级建议

### 优先用 OpenClaw 内置工具 `feishu_perm` 的场景
- 基础权限查询、添加、移除（JSON 参数格式）

### 用本 skill 脚本的场景
- `batch-add` 批量添加协作者（内置工具不支持）
- 需要明确参数校验和友好的错误提示
- 底层 API 验证

## 凭证

脚本从 `~/.openclaw/openclaw.json` 自动读取飞书凭证，无需手动设置环境变量。

## 脚本

主脚本：`scripts/feishu-perm.py`

```bash
cd ~/.openclaw/workspace/skills/feishu-perm/scripts
```

### 查询权限

```bash
# 查询文档的所有协作者
python3 feishu-perm.py list <token> <type>
# 示例：
python3 feishu-perm.py list XnWHdvjYdoMuXdxIOIbcBUwNn5c docx
```

### 添加协作者

```bash
# 添加用户权限
python3 feishu-perm.py add <token> <type> <member_id> <member_type> <perm>
# 示例：
python3 feishu-perm.py add XnWHdvjYdoMuXdxIOIbcBUwNn5c docx ou_xxx openid edit

# 添加群聊查看权限
python3 feishu-perm.py add <token> docx <chat_id> openchat view
```

### 移除协作者

```bash
python3 feishu-perm.py remove <token> <type> <member_id> <member_type>
```

### 批量添加

```bash
# 从 JSON 文件批量添加
python3 feishu-perm.py batch-add <token> <type> members.json

# members.json 格式：
[
  {"member_id": "ou_xxx", "member_type": "openid", "perm": "edit"},
  {"member_id": "oc_xxx", "member_type": "openchat", "perm": "view"}
]
```

## 参数说明

### token_type（资源类型）

| 值 | 说明 |
|----|------|
| `docx` | 飞书文档 |
| `doc` | 旧版文档 |
| `sheet` | 电子表格 |
| `bitable` | 多维表格 |
| `file` | 云盘文件 |
| `folder` | 云盘文件夹 |
| `wiki` | 知识库 |
| `mindnote` | 思维笔记 |

### member_type（成员类型）

| 值 | 说明 |
|----|------|
| `openid` | 用户 Open ID |
| `userid` | 用户 User ID |
| `unionid` | 联合 ID |
| `email` | 邮箱 |
| `openchat` | 群聊 |
| `opendepartmentid` | 部门 |

### perm（权限级别）

| 级别 | 说明 |
|------|------|
| `view` | 仅查看，不可编辑 |
| `edit` | 可编辑，不可管理权限 |
| `full_access` | 完全控制，可删除 |

## 典型工作流

### 创建文档并授权给群聊（查看权限）

```bash
# Step 1: 创建文档（用 feishu_doc）
# Step 2: 获取文档 token（从 URL 或返回值）
# Step 3: 给群聊添加查看权限
python3 feishu-perm.py add <token> docx <chat_id> openchat view
# Step 4: 给特定用户添加编辑权限
python3 feishu-perm.py add <token> docx <user_openid> openid edit
```

### 解决"无法转发"问题

部分文档默认不允许转发，给用户 `edit` 权限后即可转发：
```bash
python3 feishu-perm.py add <token> docx <user_openid> openid edit
```

## 安全最佳实践

1. **最小权限原则**：默认给 `view`，需要编辑才给 `edit`，`full_access` 仅限管理员
2. **群聊给只读**：群聊一般给 `view`，避免全员可编辑
3. **敏感文档保护**：核心配置文件不给 `full_access` 给群聊
4. **定期审查**：用 `list` 命令定期检查协作者列表

## 注意事项

- 移除权限时 `member_type` 必须与添加时一致
- `folder` 权限会向下继承，子文件/子文件夹自动获得
- 知识库（wiki）权限需用 `wiki` 类型，文档 token 本身无法直接授权

## 参考

- 飞书开放平台权限文档：https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/permission/overview
- 相关：文档创建 `../feishu-docx/`、表格操作 `../feishu-bitable/`
