# Feishu Message References

## 当前已并入/可复用能力

### 1. 卡片解析
- 来源：`../feishu-card-parser/scripts/card_parser.py`
- 用途：解析 interactive card / post / card JSON

### 2. 流式输出配置
- 参考：`../../docs/workflows/feishu-streaming-setup.md`
- 关键结论：普通长文本若要稳定触发 streaming card，建议 `renderMode: "card"`

## 后续吸收清单

### 待吸收（消息层）
- `feishu-message-recall`
- `feishu-video-sender`
- `feishu-voice-sender`
- `feishu-chat-extractor`（基础消息读取部分）
- `feishu-pdf-downloader`（若最终归消息附件链路）

## 后续要补的脚本

### message-read
目标：
- 按 `message_id` 读取飞书消息
- 返回 `msg_type` / `content` / sender / create_time

### message-parse
目标：
- 读取消息后自动识别：text / post / interactive
- interactive / post 自动转 parser

### chunk-send
目标：
- 飞书长消息拆分发送
- 执行型任务阶段播报
