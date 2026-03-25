# 智谱 ASR OpenClaw 集成 - 完整报告

## 1. OpenClaw 系统分析

### 1.1 消息处理机制

OpenClaw 的消息处理流程：

1. **消息接收**：通过 Gateway 接收来自各渠道的消息（Telegram、Feishu 等）
2. **消息规范化**：将不同渠道的消息统一为内部格式
3. **媒体处理**：检测消息中的媒体附件（图片、音频、视频等）
4. **音频转录**：如果配置了音频转录，自动下载并转录语音
5. **上下文构建**：将转录结果替换为文本消息，构建对话上下文
6. **AI 处理**：将处理后的消息发送给 AI 模型
7. **响应生成**：AI 模型基于文本内容生成回复

### 1.2 技能触发方式

OpenClaw 中语音识别的触发是**自动的**，不需要显式触发：

- 通过 `tools.media.audio.enabled: true` 启用音频处理
- 当收到包含音频附件的消息时，自动触发转录
- 转录结果自动替换消息体，AI 模型看到的是转录文本

### 1.3 响应配置方式

配置位置：`~/.openclaw/openclaw.json`

关键配置项：

```json
{
  "tools": {
    "media": {
      "audio": {
        "enabled": true,
        "models": [...]
      }
    }
  }
}
```

---

## 2. Skill 实现方案

### 2.1 Skill 文件结构

```
/root/.openclaw/skills/zhipu-asr/
├── SKILL.md                    # Skill 文档和描述
├── _meta.json                  # Skill 元数据
├── .env.example               # 环境变量示例
├── zhipu_asr.py               # 智谱 ASR 核心模块
├── transcribe.sh              # 转录脚本（OpenClaw 调用入口）
├── test.sh                    # 测试脚本
└── openclaw-config-example.json # OpenClaw 配置示例
```

### 2.2 触发条件配置

**自动触发（推荐）**：

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

**手动触发**：

```bash
# 直接调用脚本
/root/.openclaw/skills/zhipu-asr/transcribe.sh /path/to/audio.wav
```

### 2.3 自动识别流程设计

```
用户发送语音消息
    ↓
Gateway 接收消息
    ↓
检测到音频附件
    ↓
下载音频到临时文件
    ↓
调用 transcribe.sh {{MediaPath}}
    ↓
transcribe.sh 调用 zhipu_asr.py
    ↓
zhipu_asr.py 调用智谱 API
    ↓
返回识别结果（JSON）
    ↓
提取识别文本
    ↓
替换消息体（Body → 识别文本）
    ↓
AI 模型处理文本消息
    ↓
生成回复
```

---

## 3. 配置文件

### 3.1 SKILL.md 内容

参见 `/root/.openclaw/skills/zhipu-asr/SKILL.md`

主要包含：
- Skill 描述和特性
- 配置说明
- 使用方式
- 高级配置选项
- 故障排除指南

### 3.2 skill.json / _meta.json 内容

```json
{
  "ownerId": "zhipu-asr-skill",
  "slug": "zhipu-asr",
  "version": "1.0.0",
  "publishedAt": 1738988400000,
  "description": "智谱 AI 语音识别 - 使用 GLM-ASR-2512 模型进行语音转文字"
}
```

### 3.3 环境变量说明

必需变量：
- `ZHIPU_API_KEY`: 智谱 API 密钥

可选变量：
- `ZHIPU_MODEL`: 模型名称（默认：glm-asr-2512）
- `ZHIPU_MAX_RETRIES`: 最大重试次数（默认：3）
- `ZHIPU_HOTWORDS`: 默认热词表（逗号分隔）

配置优先级：`openclaw.json` > 环境变量

---

## 4. 安装和配置步骤

### 4.1 部署 Skill

#### 步骤 1：创建技能目录

```bash
mkdir -p /root/.openclaw/skills/zhipu-asr
```

#### 步骤 2：复制文件

```bash
# 复制智谱 ASR 模块
cp /root/zhipu_asr/zhipu_asr.py /root/.openclaw/skills/zhipu-asr/

# 脚本已创建，无需额外操作
```

#### 步骤 3：设置执行权限

```bash
chmod +x /root/.openclaw/skills/zhipu-asr/transcribe.sh
chmod +x /root/.openclaw/skills/zhipu-asr/test.sh
```

#### 步骤 4：安装 Python 依赖

```bash
pip3 install requests
```

### 4.2 配置自动触发

#### 方法 A：编辑配置文件

编辑 `~/.openclaw/openclaw.json`：

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

#### 方法 B：使用环境变量

```bash
export ZHIPU_API_KEY=your_api_key_here
```

### 4.3 重启 Gateway

```bash
# 停止 Gateway
openclaw gateway stop

# 启动 Gateway
openclaw gateway start

# 查看状态
openclaw gateway status
```

### 4.4 测试功能

#### 测试 1：运行自检脚本

```bash
/root/.openclaw/skills/zhipu-asr/test.sh
```

#### 测试 2：手动转录测试

```bash
export ZHIPU_API_KEY=your_api_key
/root/.openclaw/skills/zhipu-asr/transcribe.sh /path/to/test.wav
```

#### 测试 3：发送语音消息

1. 在 Telegram 中向你的机器人发送语音消息
2. 观察 Gateway 日志：`openclaw logs --follow`
3. 查看机器人是否返回正确的回复

---

## 5. 使用说明

### 5.1 如何发送语音消息触发识别

**Telegram**：
1. 打开与机器人的对话
2. 点击麦克风按钮，录制语音
3. 发送语音消息
4. 系统自动识别并回复

**Feishu**：
1. 在支持的应用中发送语音消息
2. 系统自动识别

### 5.2 如何查看识别结果

识别结果会自动注入到对话上下文中，你可以：

1. 在回复中看到 AI 基于识别文本的响应
2. 通过日志查看识别过程：`openclaw logs --follow`
3. 在日志中查找 `[Audio]` 标记的转录结果

### 5.3 如何配置热词和参数

#### 配置热词

**方法 1：在 OpenClaw 配置中**（暂不支持，需要修改脚本）

**方法 2：编辑 transcribe.sh**：

```bash
# 编辑脚本
vim /root/.openclaw/skills/zhipu-asr/transcribe.sh

# 修改 DEFAULT_HOTWORDS 变量
DEFAULT_HOTWORDS="智谱,AI,语音识别,自然语言处理,机器学习"
```

**方法 3：手动调用时指定**：

```bash
/root/.openclaw/skills/zhipu-asr/transcribe.sh /path/to/audio.wav --hotwords "智谱,AI"
```

#### 其他参数配置

超时时间：在 `openclaw.json` 中配置 `timeoutSeconds`

```json
{
  "args": ["...", "{{MediaPath}}"],
  "timeoutSeconds": 120  # 调整为 180 秒等
}
```

重试次数：设置环境变量

```bash
export ZHIPU_MAX_RETRIES=5
```

---

## 6. 高级配置和故障排除

### 6.1 添加备选转录方案

可以配置多个转录模型，按顺序尝试：

```json
{
  "tools": {
    "media": {
      "audio": {
        "models": [
          {
            "_comment": "首选：智谱 ASR",
            "type": "cli",
            "command": "bash",
            "args": ["...", "{{MediaPath}}"]
          },
          {
            "_comment": "备选：OpenAI Whisper API",
            "type": "cli",
            "command": "bash",
            "args": ["...", "{{MediaPath}}"]
          },
          {
            "_comment": "备选：本地 Whisper CLI",
            "type": "cli",
            "command": "whisper",
            "args": ["--model", "base", "{{MediaPath}}"]
          }
        ]
      }
    }
  }
}
```

### 6.2 限制转录范围

```json
{
  "tools": {
    "media": {
      "audio": {
        "scope": {
          "default": "allow",
          "rules": [
            {
              "_comment": "仅允许私聊转录",
              "action": "allow",
              "match": {
                "chatType": "direct"
              }
            }
          ]
        }
      }
    }
  }
}
```

### 6.3 常见问题

**Q: 识别失败，提示 API Key 错误**
- 检查 API Key 是否正确配置
- 确认 API Key 有效且未过期
- 查看 Gateway 日志：`openclaw logs --follow`

**Q: 音频过大，提示文件大小限制**
- 压缩音频文件（使用 ffmpeg）
- 调整 `maxBytes` 配置（最大 25MB）

**Q: 转录超时**
- 增加超时时间：`timeoutSeconds: 180`
- 检查网络连接到 `open.bigmodel.cn`
- 考虑使用较短的音频

**Q: 识别准确度不高**
- 添加热词表
- 提供上下文提示词（需要修改脚本）
- 使用更高质量的音频（16kHz 采样率）

---

## 7. 技术细节

### 7.1 API 调用流程

```
transcribe.sh
    ↓
python3 zhipu_asr.py
    ↓
requests.post("https://open.bigmodel.cn/api/paas/v4/audio/transcriptions")
    ↓
返回 JSON：{ "text": "识别文本", ... }
    ↓
提取 text 字段并输出
```

### 7.2 数据流

```
语音文件 (Telegram OGG) → 下载 → 转换 (如需要) → WAV/MP3 → 智谱 API → JSON → 文本
```

### 7.3 支持的音频格式

- `.wav` - 推荐格式
- `.mp3` - 支持格式

注：Telegram 发送的语音通常是 OGG 格式，OpenClaw 会自动转换

---

## 8. 总结

### 8.1 已完成工作

1. ✅ 分析 OpenClaw 聊天系统架构
2. ✅ 创建 Skill 包装器（transcribe.sh）
3. ✅ 配置自动响应机制
4. ✅ 创建完整的配置文件
5. ✅ 提供测试脚本
6. ✅ 编写详细文档

### 8.2 核心文件清单

- `/root/.openclaw/skills/zhipu-asr/SKILL.md` - Skill 文档
- `/root/.openclaw/skills/zhipu-asr/_meta.json` - 元数据
- `/root/.openclaw/skills/zhipu-asr/transcribe.sh` - 转录脚本
- `/root/.openclaw/skills/zhipu-asr/zhipu_asr.py` - ASR 模块
- `/root/.openclaw/skills/zhipu-asr/test.sh` - 测试脚本
- `/root/.openclaw/skills/zhipu-asr/.env.example` - 环境变量示例
- `/root/.openclaw/skills/zhipu-asr/openclaw-config-example.json` - 配置示例

### 8.3 下一步建议

1. **配置 API Key**：在 `openclaw.json` 中配置智谱 API Key
2. **重启 Gateway**：使配置生效
3. **发送测试语音**：验证自动转录功能
4. **优化热词表**：根据使用场景调整热词
5. **监控日志**：定期检查转录性能和错误

### 8.4 扩展可能

- 支持更多音频格式（OGG, M4A）
- 添加上下文提示词配置
- 支持实时流式识别
- 添加语音合成（TTS）功能
- 多语言识别支持

---

**集成完成时间**：2025-02-08
**版本**：1.0.0
**作者**：OpenClaw Subagent
