---
name: feishu-media
description: 飞书媒体文件发送与下载工具。支持图片、视频（播放器形式）、语音（语音条形式）、文件附件发送，以及图片/消息资源下载。
---

# 飞书媒体技能

负责飞书媒体文件发送与下载，是飞书技能体系中的媒体层。

## 何时使用

当你需要：
- 发送图片（以图片消息形式，非文件附件）
- 发送视频（以播放器形式，可直接播放，非文件附件）
- 发送语音（以语音条形式，类似微信语音，非音频文件）
- 发送文件附件（PDF/Word/Excel/压缩包等）
- 下载飞书消息中的图片/附件

## 凭证

脚本从 `~/.openclaw/openclaw.json` 自动读取飞书凭证，无需手动设置环境变量。

## 脚本

主脚本：`scripts/feishu-media.py`

```bash
cd ~/.openclaw/workspace/skills/feishu-media/scripts
```

### 发送图片

```bash
# 发送到群
python3 feishu-media.py send-image /path/to/image.jpg oc_xxx

# 发送到用户
python3 feishu-media.py send-image /path/to/image.jpg ou_xxx --type open_id
```

### 发送视频（播放器形式）

```bash
# 自动生成封面（从视频第1秒截取）
python3 feishu-media.py send-video /path/to/video.mp4 oc_xxx

# 指定封面图
python3 feishu-media.py send-video /path/to/video.mp4 oc_xxx --cover /path/cover.jpg

# 带描述文案
python3 feishu-media.py send-video /path/to/video.mp4 oc_xxx --caption "这是视频说明"
```

**关键说明**：OpenClaw `message` 工具发送视频时，视频会被当成文件附件，无法直接播放。本工具使用飞书 `msg_type: media` + `file_key` + `image_key`，发送后可直接在飞书中播放。

### 发送语音（语音条形式）

```bash
# MP3 自动转 AMR（飞书语音格式）
python3 feishu-media.py send-voice /path/to/audio.mp3 oc_xxx
```

**关键说明**：发送音频文件时用 `msg_type: file` 会显示为附件；本工具转 AMR 后用 `msg_type: voice` 发送，显示为语音条，点击播放。

依赖：`ffmpeg`（已安装）

### 发送文件附件

```bash
python3 feishu-media.py send-file /path/to/doc.pdf oc_xxx
python3 feishu-media.py send-file /path/to/report.xlsx oc_xxx
```

### 下载图片

```bash
# 从 URL 下载并上传到飞书
python3 feishu-media.py download-image "https://example.com/photo.jpg"

# 从 image_key 下载
python3 feishu-media.py download-image img_v2_xxx -o local.jpg
```

### 下载消息附件

```bash
# 从消息 ID 下载附件（自动提取 file_key）
python3 feishu-media.py download-resource om_xxx -o output.pdf

# 指定 file_key
python3 feishu-media.py download-resource om_xxx --file-key file_v2_xxx -o output.pdf
```

## 消息类型对比

| 需求 | 正确方式 | 错误方式 |
|------|---------|---------|
| 图片消息 | `msg_type: image` + image_key | `msg_type: file`（附件形式） |
| 视频播放器 | `msg_type: media` + file_key + image_key | `msg_type: file`（下载后播放） |
| 语音条 | `msg_type: voice` + AMR 格式 | `msg_type: file`（音频附件） |
| 文件附件 | `msg_type: file` + file_key | 直接发送路径 |

## 依赖

- `ffmpeg`：用于视频封面截取（`send-video`）和音频格式转换（`send-voice`）
  - macOS：`brew install ffmpeg`
  - Linux：`apt-get install ffmpeg`

### ⚠️ AMR 编码注意

macOS 自带 ffmpeg 只有 AMR **解码器**，没有**编码器**。`send-voice` 需要 AMR 编码能力。

解决方案：
```bash
# 方案1：安装带 AMR 编码支持的 ffmpeg
brew install ffmpeg --with-libopencore-amrnb

# 方案2（推荐）：改用 OPUS 格式替代 AMR
# 修改脚本中 convert_to_amr() 函数，输出 .opus 文件，msg_type 改为 opus
```

## 外部技能来源

| 参考来源 | 吸收内容 |
|---------|---------|
| wulaosiji/feishu-video-sender | 视频上传 + 封面生成 + media 发送 |
| wulaosiji/feishu-voice-sender | MP3→AMR 转换 + voice 发送 |
| m1heng/clawdbot-feishu media.ts | 图片下载 + 消息资源下载 |

## 注意事项

- `send-video` 需要目标用户/群已开启视频消息功能
- `send-voice` 依赖 `ffmpeg`，未安装时无法使用
- 图片下载需要应用有对应资源读取权限
- 文件类型支持：PDF / Word / Excel / PPT / TXT / ZIP / MP3 / MP4 等
