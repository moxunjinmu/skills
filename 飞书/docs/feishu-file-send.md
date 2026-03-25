# 飞书发送文件完整流程

## 结论先行

飞书机器人发送文件，**只有两种可行方式**：

| 方式 | 路径 | 适用场景 |
|------|------|---------|
| `message` 工具 + `workspace/tmp/` 目录 | 文件放在 `~/.openclaw/workspace/tmp/` 下 | **首选**，最简单 |
| 飞书 IM 文件上传 API（curl） | 通过 API 上传并直接发送 | 需要自动化脚本时 |

**绝对不行**：直接把本地路径（`/Users/moxun/...`）传给 `message` 工具的 `filePath`。

---

## 方式一：message 工具（首选）

### 前置条件

- 文件必须放在 `~/.openclaw/workspace/tmp/` 目录下
- 文件名不含特殊字符

### 完整步骤

1. 把文件复制到 `~/.openclaw/workspace/tmp/`
2. 用 `message` 工具发送：

```python
message(action="send", channel="feishu", target="user:ou_xxx", filePath="/Users/moxun/.openclaw/workspace/tmp/xxx.zip")
```

### 为什么会通

OpenClaw 的 `message` 工具内部把 `workspace/tmp/` 路径做了特殊映射，飞书服务器能够访问。

`/tmp/` 和其他本地路径飞书服务器访问不到，会报错。

### 常见错误

```
# ❌ 错误：飞书收到的是本地路径，服务器访问不到
filePath="/Users/moxun/Downloads/xxx.zip"
filePath="/tmp/xxx.zip"

# ✅ 正确：workspace/tmp 目录
filePath="/Users/moxun/.openclaw/workspace/tmp/xxx.zip"
```

---

## 方式二：飞书 IM 文件上传 API（自动化脚本用）

### 前置条件

1. 应用已开通 `im:message:send_as_bot` 权限
2. 知道目标用户的 `open_id`（格式：`ou_xxx`）
3. `curl` 已安装（macOS 自带）

### 完整 curl 命令

```bash
# Step 1: 获取 tenant_access_token
TOKEN=$(curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d '{
    "app_id": "cli_xxxx",
    "app_secret": "xxxx"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")

# Step 2: 上传并发送文件
curl -s -X POST 'https://open.feishu.cn/open-apis/im/v1/files?receive_id_type=open_id' \
  -H "Authorization: Bearer $TOKEN" \
  -F "receive_id=ou_目标用户open_id" \
  -F "file_name=文件名.zip" \
  -F "file_type=zip" \
  -F "file=@/Users/moxun/.openclaw/workspace/tmp/文件名.zip;type=application/zip"
```

### 已知限制

| 问题 | 原因 | 状态 |
|------|------|------|
| HTTP 400 | `receive_id` 必须是 form-data 字段，不能放 URL | 已验证 |
| urllib multipart 上传失败 | urllib 构造的 multipart 与飞书不兼容 | 必须用 curl |
| Drive API 上传失败 | 需要 `drive:drive` 写权限，且 `parent_type` 枚举值有限制 | 改用 IM 接口 |

### receive_id_type 参数说明

必须是 URL 查询参数 `?receive_id_type=open_id`，不是 body 字段。飞书支持：
- `open_id`（推荐）
- `user_id`
- `union_id`
- `chat_id`

---

## 方式三：上传到飞书云盘，再分享链接

### 前置条件

- 应用有 `drive:drive` 写权限

### 完整步骤

```bash
# Step 1: 创建云盘文件夹
curl -s -X POST 'https://open.feishu.cn/open-apis/drive/v1/files/create_folder' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"feishu-skills","folder_token":""}'

# Step 2: 上传文件（parent_type 必须是 "folder"）
curl -s -X POST 'https://open.feishu.cn/open-apis/drive/v1/files/upload_all' \
  -H "Authorization: Bearer $TOKEN" \
  -F "file_name=feishu-skills.zip" \
  -F "parent_type=folder" \
  -F "parent_node=文件夹token" \
  -F "file=@/Users/moxun/.openclaw/workspace/tmp/feishu-skills.zip;type=application/zip"
```

### 已知限制

| 问题 | 原因 | 状态 |
|------|------|------|
| 报 1061002 params error | `parent_type` 枚举值有限制，必须是 `folder`/`docx`/`sheet` 等标准值 | 已验证 |
| 无 drive 写权限 | 应用未开通 `drive:drive` 写权限 | 改用 IM 接口 |

---

## 总结：决策树

```
发送文件给用户/群
    │
    ├─ 文件已在 workspace/tmp/ ──→ message 工具，直接发 ✅
    │
    └─ 文件在其他位置
            │
            ├─ 临时文件，不需要脚本 ──→ 复制到 workspace/tmp/ → message 工具 ✅
            │
            └─ 需要脚本自动化 ──→ IM 文件上传 API（curl）✅
                                    （urllib 不行，必须 curl）
```

---

## 经验教训

1. **`message` 工具的 `filePath` 只认 `workspace/tmp/`**：所有要发给飞书的文件，事先复制到这个目录
2. **urllib multipart 有兼容问题**：飞书 API 上传文件必须用 curl
3. **`receive_id_type` 是 URL 参数不是 body 字段**：很多 SDK/脚本容易搞错这个
4. **Drive API 权限要求高**：若无 `drive:drive` 写权限，上传云盘会报 1061002，改走 IM 接口
5. **文件必须先上传再发送**：飞书机器人不能直接发本地路径附件，必须通过 API 中转
