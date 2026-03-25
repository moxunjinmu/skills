---
name: feishu-community
description: 飞书群运营与社群自动化技能。用于群管理、欢迎新成员、@消息巡检、消息撤回、群公告读写等社群运营场景。
---

# 飞书社群运营技能

负责飞书群运营与社群自动化，是飞书技能体系中的运营层。

## 何时使用

当你需要：
- 创建群聊、添加/移除成员
- 一键创建会话群并发送欢迎语
- 欢迎群中新成员（批量 @）
- 巡检群里遗漏的 @消息
- 撤回（删除）机器人发送的消息
- 读写群公告

## 凭证

脚本从 `~/.openclaw/openclaw.json` 自动读取飞书凭证，无需手动设置环境变量。

## 脚本

主脚本：`scripts/feishu-community.py`

```bash
cd ~/.openclaw/workspace/skills/feishu-community/scripts
```

### 群管理

```bash
# 创建群聊
python3 feishu-community.py create-chat <name> [--users USER_IDS] [--desc TEXT]

# 向群聊添加成员
python3 feishu-community.py add-members <chat_id> <user_ids>

# 检查机器人是否在群里
python3 feishu-community.py check-bot <chat_id>

# 解散群聊
python3 feishu-community.py delete-chat <chat_id>
```

### 创建会话群（一键建群 + 欢迎语）

```bash
# 建群 + 发欢迎语（8套模板随机，自动夜间静默）
python3 feishu-community.py create-session-chat <name> <user_ids> [--greeting TEXT] [--desc TEXT]
```

整合自 m1heng/clawdbot-feishu（`create_session_chat`）。

### 欢迎新成员

```bash
# 检查并欢迎群中新成员（批量@）
python3 feishu-community.py welcome <chat_id> [--batch-size N] [--dry-run]
```

- 自动夜间静默（23:00–07:00 不发欢迎消息）
- 批量 @ 分批发送（每批最多 20 人）
- 8 套欢迎语模板随机轮换

整合自 wulaosiji/feishu-group-welcome。

### @消息巡检

```bash
# 检查最近 N 分钟内的遗漏 @消息
python3 feishu-community.py check-mentions <chat_id> [--minutes N]
```

整合自 wulaosiji/feishu-chat-monitor。

### 消息撤回

```bash
# 撤回（删除）单条消息
python3 feishu-community.py recall <message_id>

# 删除话题中机器人发送的所有消息
python3 feishu-community.py recall-thread <thread_id> [--dry-run]
```

⚠️ 只能删除机器人自己发送的消息。整合自 wulaosiji/feishu-message-recall。

### 群公告

```bash
# 获取群公告
python3 feishu-community.py get-announcement <chat_id>

# 写入群公告
python3 feishu-community.py write-announcement <chat_id> <content>
```

## 夜间模式

欢迎功能在 **23:00–07:00** 自动静默，不发送消息。

## 欢迎语模板

8 套模板随机选择，涵盖：简洁实用型、资源型、专业型、幽默型、边界感型。可在脚本中修改 `WELCOME_TEMPLATES` 列表。

## 外部技能吸收来源

| 参考来源 | 吸收内容 |
|---------|---------|
| m1heng/clawdbot-feishu `chat-tools` | `create_session_chat`、`check_bot_in_chat`、群公告读写 |
| wulaosiji/feishu-group-welcome | 批量 @、夜间模式、欢迎语模板 |
| wulaosiji/feishu-chat-monitor | @消息巡检逻辑 |
| wulaosiji/feishu-message-recall | 消息撤回、话题消息批量删除 |

## 注意事项

- `@消息巡检` 需要机器人已在目标群中
- `delete-chat` 解散后不可恢复，请确认后再操作
- `recall-thread` 只能删除机器人自己发送的消息
- 欢迎语中的 `user_ids` 需要是精确的飞书 user_id（open_id）
