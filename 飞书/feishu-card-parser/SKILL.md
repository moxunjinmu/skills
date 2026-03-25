---
name: feishu-card-parser
description: 解析飞书卡片（interactive card / post / card json）消息内容，提取文本、Markdown、图片、链接、@提及信息。适用于排查飞书卡片显示、调试 streaming card、把飞书卡片转成可读文本。
---

# 飞书卡片解析技能

用于把飞书卡片消息内容解析为更容易阅读和调试的结构化结果。

## 何时使用

当你需要：
- 解析飞书 `interactive` 卡片消息内容
- 把飞书 `post` / card JSON 转为纯文本或 Markdown
- 排查 streaming card 最终落地内容
- 提取图片 key、链接、@用户、代码块

## 主要能力

主脚本：`scripts/card_parser.py`

支持：
- 解析 JSON 字符串
- 解析 JSON 文件
- 输出 `text` / `markdown` / `json`

## 常见用法

```bash
cd ~/.openclaw/workspace/skills/feishu-card-parser/scripts

# 解析 JSON 文件
python3 card_parser.py --input ./card.json --format markdown

# 直接解析字符串
python3 card_parser.py --text '{"title":"标题","content":[[{"tag":"text","text":"内容"}]]}' --format text
```

## 输出字段

- `title`
- `text_content`
- `markdown_content`
- `images`
- `links`
- `mentions`
- `raw`

## 注意

- 这个 skill 负责“解析内容”，不负责从飞书服务端拉取消息。
- 如果要读取某条历史飞书消息，仍需要先通过 Feishu API 拿到 `content`，再交给本脚本解析。
- 之后可以把“读取消息 + 解析卡片”继续并入单独的 `feishu-message` skill。
