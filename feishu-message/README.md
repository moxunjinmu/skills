# 飞书消息技能

负责飞书消息层，是飞书技能体系中的基础设施层。

## 已接入能力

### 1. 消息读取 / 解析
脚本：`scripts/feishu_message.py`

```bash
# 读取单条消息
python3 feishu_message.py get <message_id>

# 读取并解析卡片内容
python3 feishu_message.py parse <message_id>

# 拉取群聊历史
python3 feishu_message.py chat-history <chat_id> --limit 20
```

### 2. 卡片解析器
脚本：`../feishu-card-parser/scripts/card_parser.py`

### 3. 群聊历史拉取
脚本：`scripts/extract_chat.py`

```bash
python3 scripts/extract_chat.py --chat-id <OC_XXX> --output history.json
```

### 4. 内容分析
脚本：`scripts/analyze_content.py`

```bash
python3 scripts/analyze_content.py \
  --input history.json \
  --keywords openclaw,飞书,cron \
  --output analysis.json
```

支持按关键词过滤、分类统计、生成 markdown 报告。

## 凭证说明

脚本自动从 `~/.openclaw/openclaw.json` 读取飞书 appId / appSecret，无需手动配置环境变量。

## 流式输出

配置参考：
- `../../docs/workflows/feishu-streaming-setup.md`

## 下一步

- chunked output 发送器
- streaming card 调试辅助
- 消息撤回
- 媒体发送（视频/语音）
