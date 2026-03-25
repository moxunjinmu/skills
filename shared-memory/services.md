# 模型与服务配置

> 所有 AI 模型、第三方服务、API 的配置信息。配置变更后必须更新。

---

## 模型配置

| 模型 | 用途 | 配置 | 备注 |
|------|------|------|------|
| minimax-portal/MiniMax-M2.7-highspeed | 主模型 | `~/.openclaw/openclaw.json` default_model | 日常主力 |
| 92scw/gpt-5.4 | 备用/测试 | via 92scw provider | 偶尔使用 |
| akai/claude-sonnet-4-6 | 高质量任务 | via Akai provider | 复杂推理 |

## 服务配置

| 服务 | 用途 | 配置位置 | 备注 |
|------|------|---------|------|
| MiniMax API | 搜索/图片理解 | TOOLS.md | Token Plan |
| OpenClaw Gateway | 主助手 | `~/.openclaw/openclaw.json` | 本地 Mac mini |
| Clash Verge | 翻墙代理 | `http://127.0.0.1:7897` | Telegram 走此代理 |
| Feishu Bot | 飞书消息 | via OpenClaw channel | - |
| GitHub | 代码仓库 | `$GITHUB_TOKEN` | moxunjinmu/skills |

---

## 更新规范

配置变更后立即更新本文件，包括：
- 模型切换 / API Key 轮换
- 服务地址/端口变化
- 新增/停用服务
