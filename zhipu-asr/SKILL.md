---
name: zhipu-asr
description: 智谱 AI 语音识别 - 使用 GLM-ASR-2512 模型进行语音转文字
homepage: https://open.bigmodel.cn/
metadata: {"clawdbot":{"emoji":"🎤","requires":{"bins":["bash"],"python":["python3"],"pip":["requests"]},"install":[{"id":"pip","kind":"pip","package":"requests","label":"Install Python requests library"},{"id":"copy","kind":"copy","source":"/root/zhipu_asr/zhipu_asr.py","dest":"/root/.openclaw/skills/zhipu-asr/zhipu_asr.py","label":"Copy ASR module"}]}}
---

# 智谱 AI 语音识别 (zhipu-asr)

使用智谱 GLM-ASR-2512 模型进行语音转文字识别。

## 特性

- 支持多种音频格式 (.wav, .mp3)
- 高精度中文语音识别
- 支持热词表，提升特定领域识别率
- 支持上下文提示词
- 支持用户 ID 追踪

## 配置

### 1. 设置 API Key

在 `~/.openclaw/openclaw.json` 中配置：

```json
{
  "skills": {
    "zhipu-asr": {
      "apiKey": "YOUR_ZHIPU_API_KEY"
    }
  }
}
```

或设置环境变量：

```bash
export ZHIPU_API_KEY=YOUR_ZHIPU_API_KEY
```

### 2. 配置音频自动转录

在 `~/.openclaw/openclaw.json` 中添加：

```json
{
  "tools": {
    "media": {
      "audio": {
        "enabled": true,
        "models": [
          {
            "type": "cli",
            "command": "bash",
            "args": ["/root/.openclaw/skills/zhipu-asr/transcribe.sh", "{{MediaPath}}"],
            "timeoutSeconds": 120
          }
        ]
      }
    }
  }
}
```

## 使用方式

### 自动转录（推荐）

配置完成后，当用户发送语音消息时，OpenClaw 会自动：

1. 下载语音文件
2. 调用智谱 ASR 进行识别
3. 将识别结果替换为文本消息
4. AI 模型看到的是识别后的文本

### 手动转录

如果需要手动调用识别脚本：

```bash
# 基本使用
/root/.openclaw/skills/zhipu-asr/transcribe.sh /path/to/audio.wav

# 使用热词
/root/.openclaw/skills/zhipu-asr/transcribe.sh /path/to/audio.wav --hotwords "智谱,AI,语音识别"

# 仅输出文本（安静模式）
/root/.openclaw/skills/zhipu-asr/transcribe.sh /path/to/audio.wav --quiet
```

## 高级配置

### 热词表

热词可以提升特定领域词汇的识别准确率。在识别脚本中可以预设热词：

```bash
# 编辑 transcribe.sh，修改 DEFAULT_HOTWORDS 变量
DEFAULT_HOTWORDS="智谱,AI,语音识别,自然语言处理"
```

### 环境变量

- `ZHIPU_API_KEY`: 智谱 API 密钥（必需）
- `ZHIPU_MODEL`: 模型名称（默认：glm-asr-2512）
- `ZHIPU_MAX_RETRIES`: 最大重试次数（默认：3）

## 限制

- 单个音频文件最大 25MB
- 热词表最多 100 个词
- 上下文提示词建议小于 8000 字
- 用户 ID 长度 6-128 字符

## 故障排除

### 识别失败

1. 检查 API Key 是否正确配置
2. 查看日志：`openclaw logs --follow`
3. 验证网络连接到 `open.bigmodel.cn`
4. 确认音频文件格式（仅支持 .wav 和 .mp3）

### 音频过大

如果音频文件超过 25MB，需要先压缩或分段处理：

```bash
# 使用 ffmpeg 压缩
ffmpeg -i large_audio.wav -ar 16000 -b:a 64k compressed_audio.mp3
```

## API 参考

- 智谱开放平台：https://open.bigmodel.cn/
- GLM-ASR 文档：https://open.bigmodel.cn/dev/api#audio

## 示例

### 识别结果示例

```
🎤 语音识别

任务 ID: asr_xxx
模型: glm-asr-2512

识别文本:
你好，这是一段测试语音内容。

用时: 2.3秒
```

## 注意事项

- 智谱 ASR 服务需要联网使用
- 建议使用 16kHz 采样率的音频以获得最佳效果
- 语音时长建议在 30 秒以内，长语音可能需要更长时间
- 对于多轮对话，可以使用上下文提示词提升准确性
