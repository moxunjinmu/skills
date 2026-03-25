---
name: feishu-message
description: 飞书消息能力技能。用于读取/排查飞书消息、解析 interactive card / post 内容、群聊历史拉取与内容分析、chunked 分块发送、流式输出调试。适用于消息读取、卡片解析、聊天提炼、流式输出诊断、长消息拆分策略等场景。
---

# 飞书消息技能

负责飞书消息层的完整能力，是飞书技能体系中的基础设施层。

## 何时使用

当你需要：
- 读取某条飞书消息
- 解析 interactive card / post 内容
- 按 chat_id 拉取群聊历史
- 分析群聊内容（关键词过滤、分类统计）
- 诊断 Feishu streaming card 行为
- 实现飞书长消息分块发送
- 规划执行阶段消息播报

## 工具层级

### 优先用内置工具
- `feishu_chat` 工具：查 chat 成员、chat 信息
- `feishu_doc` / `feishu_wiki` / `feishu_bitable`：对应各自专业领域

### 用本 skill 脚本的场景
- 按 `message_id` 读取单条消息
- 解析 card/post 内容
- 拉取群聊历史
- 内容分析/关键词过滤
- streaming card 诊断
- chunked output 发送

## 脚本

主脚本：`scripts/feishu_message.py`

```bash
cd ~/.openclaw/workspace/skills/feishu-message/scripts

# 读取单条消息（简化摘要）
python3 feishu_message.py get <message_id>

# 读取单条消息（原始 JSON）
python3 feishu_message.py get <message_id> --raw

# 读取并解析卡片内容
python3 feishu_message.py parse <message_id>

# 拉取群聊最近消息
python3 feishu_message.py chat-history <chat_id> --limit 20

# 按时间范围拉取群聊
python3 feishu_message.py chat-history <chat_id> --start-time 1700000000 --end-time 1700100000
```

### 发送消息

```bash
# 直接发送（超过 1000 字自动分块）
python3 feishu_message.py send <chat_id> "内容"

# 从 stdin 读取内容发送（适合长文本）
echo "很长一段内容..." | python3 feishu_message.py send <chat_id> "-"

# 自定义分块大小
python3 feishu_message.py send <chat_id> "内容" --chunk-size 800
```

### 执行阶段播报（progress）

用于多步任务中主动推送进度消息，避免飞书端感觉"卡住"。

```bash
# 基本用法：第 2 步，共 5 步
python3 feishu_message.py progress <chat_id> 2 5

# 自定义标签
python3 feishu_message.py progress <chat_id> 3 4 --label "填写表单中"
# 输出：[■■■□] 填写表单中
```

进度条语义：
- `■` = 已完成步骤
- `□` = 剩余步骤

从外部吸收的脚本：
- `scripts/extract_chat.py`：完整群聊历史拉取（支持分页/时间范围）
- `scripts/analyze_content.py`：内容分析（关键词过滤/分类统计/markdown 报告生成）

### 流式处理命令（新增）

用于处理飞书 streaming card 增量文本去重：

```bash
# 合并两段流式文本（处理重复）
python3 feishu_message.py merge-streaming "上一段" "下一段"

# 从流式日志 JSON 文件还原去重后的完整文本
python3 feishu_message.py deduplicate streaming_log.json
```

`mergeStreamingText` 逻辑（来源：m1heng/clawdbot-feishu `streaming-card.ts`）：
- next 完全包含 prev → 返回 next
- prev 完全包含 next → 返回 prev
- 两段有部分重叠（工具调用中常见）→ 去掉重叠后拼接
- 两段完全不重叠 → 直接拼接
- 最大重叠检测：500 字符

## 流式输出参考

飞书 channel 当前配置（2026-03-24 确认）：
```json
{
  "streaming": true,
  "blockStreaming": false,
  "renderMode": "text",
  "textChunkLimit": 1200
}
```

关键变化：
- `blockStreaming: false` — 响应分块直接推送，不再阻塞等待完整结果
- `renderMode: "text"` — 直接文本推送，不走卡片渲染

分块发送脚本（`send` 命令）会在内容超过 `textChunkLimit` 时自动切分，适合配合使用。

## 卡片解析参考

卡片解析器独立存在：
- `../feishu-card-parser/scripts/card_parser.py`

## 常见错误码

- `232006`：无效 chat_id
- `232011`：不在群中
- `232025`：机器人能力未开启
