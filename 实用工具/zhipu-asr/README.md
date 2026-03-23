# 智谱 ASR OpenClaw 集成 - 快速开始

## 安装步骤

### 方法 1：自动部署（推荐）

```bash
cd /root/.openclaw/skills/zhipu-asr
sudo ./deploy.sh
```

按照提示输入你的智谱 API Key，脚本会自动：
1. 备份现有配置
2. 更新 OpenClaw 配置
3. 检查依赖
4. 运行测试
5. 重启 Gateway

### 方法 2：手动配置

#### 1. 编辑 OpenClaw 配置

```bash
vim /root/.openclaw/openclaw.json
```

#### 2. 添加以下配置

```json
{
  "skills": {
    "zhipu-asr": {
      "apiKey": "YOUR_ZHIPU_API_KEY_HERE"
    }
  },
  "tools": {
    "media": {
      "audio": {
        "enabled": true,
        "maxBytes": 26214400,
        "models": [
          {
            "type": "cli",
            "command": "bash",
            "args": [
              "/root/.openclaw/skills/zhipu-asr/transcribe.sh",
              "{{MediaPath}}"
            ],
            "timeoutSeconds": 120
          }
        ]
      }
    }
  }
}
```

#### 3. 安装依赖

```bash
pip3 install requests
```

#### 4. 重启 Gateway

```bash
openclaw gateway restart
```

## 测试

### 运行自检

```bash
/root/.openclaw/skills/zhipu-asr/test.sh
```

### 手动测试

```bash
# 设置 API Key
export ZHIPU_API_KEY=your_api_key

# 测试转录
/root/.openclaw/skills/zhipu-asr/transcribe.sh /path/to/audio.wav
```

### 发送语音消息测试

1. 在 Telegram 中向你的机器人发送语音消息
2. 等待识别和回复
3. 查看日志：`openclaw logs --follow`

## 配置说明

### API Key

从 https://open.bigmodel.cn/ 获取智谱 API Key

配置位置：
- `~/.openclaw/openclaw.json` 中的 `skills.zhipu-asr.apiKey`
- 或环境变量：`ZHIPU_API_KEY`

### 热词配置

编辑 `/root/.openclaw/skills/zhipu-asr/transcribe.sh`：

```bash
# 修改 DEFAULT_HOTWORDS 变量
DEFAULT_HOTWORDS="智谱,AI,语音识别,自然语言处理"
```

### 超时配置

在 `openclaw.json` 中调整：

```json
{
  "timeoutSeconds": 180  // 超时时间（秒）
}
```

## 故障排除

### 问题：识别失败

**解决方法：**
1. 检查 API Key 是否正确
2. 查看日志：`openclaw logs --follow`
3. 确认网络连接：`ping open.bigmodel.cn`

### 问题：音频过大

**解决方法：**
```bash
# 压缩音频
ffmpeg -i large_audio.wav -ar 16000 -b:a 64k compressed_audio.mp3
```

### 问题：转录超时

**解决方法：**
增加超时时间或使用更短的音频文件

## 查看日志

```bash
# 实时查看日志
openclaw logs --follow

# 筛选音频转录相关日志
openclaw logs --follow | grep -i "audio\|transcrib"
```

## 卸载

```bash
# 1. 编辑配置，移除 zhipu-asr 相关配置
vim /root/.openclaw/openclaw.json

# 2. 重启 Gateway
openclaw gateway restart

# 3. 可选：删除 Skill 目录
rm -rf /root/.openclaw/skills/zhipu-asr
```

## 相关文档

- 完整集成报告：`INTEGRATION_REPORT.md`
- Skill 文档：`SKILL.md`
- 配置示例：`openclaw-config-example.json`
- 环境变量示例：`.env.example`
