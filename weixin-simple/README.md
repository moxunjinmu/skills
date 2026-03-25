# 微信公众号简化助手（无Python依赖）

这是一个极简版的微信公众号运营助手，**无需安装 Python**，所有功能由 Claude 直接处理或使用 Bash 脚本调用 API。

## 核心特性

- 无需 Python 环境
- Claude 直接处理文案生成和仿写
- 使用 Bash + curl 调用外部 API
- 极简配置，开箱即用

## 功能对比

| 功能 | 简化版 | 完整版 |
|------|--------|--------|
| 文案生成 | Claude直接处理 | Claude直接处理 |
| 文案仿写 | Claude直接处理 | Python脚本处理 |
| 排版 | 简单HTML+模板 | 专业排版模板 |
| 封面生成 | curl调用API | Python调用API |
| 自动发布 | 提供发布信息 | 完整自动发布 |
| 依赖环境 | **无** | Python 3.8+ |

## 目录结构

```
weixin_simple/
├── SKILL.md              # 技能配置文件
├── README.md             # 项目说明
├── .env.example          # 环境变量示例
├── scripts/              # Bash 脚本
│   ├── generate_image.sh     # 生成封面图
│   ├── get_token.sh          # 获取微信 token
│   ├── upload_image.sh       # 上传图片到素材库
│   └── prepare_draft.sh      # 准备草稿信息
├── templates/            # 排版模板
│   ├── defaultlayout.md      # 默认排版
│   └── techlayout.md         # 科技排版
└── references/           # 参考文档
    └── 违禁词库.md           # 违禁词库
```

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件（可选，如果不需要自动生成封面或发布，可以不配置）：

```env
WECHAT_APPID=your_appid
WECHAT_APPSECRET=your_secret
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/jimeng
```

### 2. 赋予脚本执行权限

```bash
chmod +x scripts/*.sh
```

### 3. 使用技能

在 Claude Code 中直接使用，例如：

- "帮我写一篇关于 AI 教育的公众号文章"
- "仿写这篇文案，主题改成 xxx"
- "为这篇文案生成一个封面图"

## 使用示例

### 生成封面图

```bash
bash scripts/generate_image.sh "一个现代化的科技风格封面图，蓝色渐变背景"
```

### 获取微信 access_token

```bash
bash scripts/get_token.sh
```

### 上传图片到素材库

```bash
# 先下载图片
curl -o cover.png "https://example.com/cover.png"

# 上传
bash scripts/upload_image.sh "your_access_token" "cover.png"
```

### 准备草稿发布信息

```bash
bash scripts/prepare_draft.sh \
  "your_access_token" \
  "文章标题" \
  "article.html" \
  "media_id_xxx"
```

## 工作流程

### 完整文章创作流程

```
1. 用户输入主题
   ↓
2. Claude 直接生成文章（无需Python）
   ↓
3. 保存为 Markdown 文件
   ↓
4. Claude 转换为 HTML（简单排版）
   ↓
5. 生成封面图提示词
   ↓
6. 调用 API 生成封面（使用curl）
   ↓
7. 获取发布信息
   ↓
8. 提供完整信息供手动发布
```

## 为什么选择简化版？

### 优点
- 无需安装 Python
- 配置极简
- Claude 直接处理，响应更快
- 适合快速创作和仿写

### 适用场景
- 主要需要文案生成和仿写
- 不需要自动发布功能
- 希望快速上手使用

### 不适用场景
- 需要专业排版效果
- 需要完全自动化发布
- 需要批量处理大量文章

## 常见问题

### Q1：真的不需要 Python 吗？
A：是的，完全不需要。所有功能由 Claude 直接处理或使用 Bash 脚本。

### Q2：如何自动发布文章？
A：简化版提供完整的发布信息，你可以手动复制到微信公众号后台，或使用提供的 curl 命令完成发布。

### Q3：排版效果如何？
A：简化版提供基础排版，如需专业排版建议使用完整版。

### Q4：封面图必须用 n8n 吗？
A：不是必须的。简化版会生成封面提示词，你可以使用任何 AI 绘图工具生成封面。

## 与完整版对比

| 特性 | 简化版 | 完整版 |
|------|--------|--------|
| 安装难度 | 无需安装 | 需要配置Python环境 |
| 文案生成 | | 两者相同 |
| 文案仿写 | Claude直接处理 | Python脚本辅助 |
| 排版效果 | 基础HTML | 专业模板 |
| 封面生成 | curl调用 | Python调用 |
| 发布方式 | 提供信息 | 自动上传 |
| 学习成本 | 极低 | 中等 |

## 技术栈

- Bash 脚本
- curl（HTTP 请求）
- Claude Code（AI 处理）
- Markdown（文章格式）

## 更新日志

### v1.0.0 (2025-01-28)
- 初始版本发布
- 无需 Python 依赖
- 支持文案生成和仿写
- 支持封面生成（使用curl）
- 支持获取发布信息

## 许可证

MIT License
