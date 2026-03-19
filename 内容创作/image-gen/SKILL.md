# 图像生成技能 (image-gen)

多模型兼容的 AI 图像生成工具，支持智谱 CogView/GLM-Image 和 OpenAI DALL-E/gpt-image。

## 快速使用

```bash
cd /root/mo-hub/skills/image-gen/scripts

# 基础用法（默认智谱 glm-image）
node generate.js "一只赛博三花猫"

# 指定 provider 和模型
node generate.js "a cyber cat" --provider openai
node generate.js "一只猫" --provider zhipu --model cogview-3-flash

# 指定尺寸
node generate.js "一只猫" --size 1344x768

# 保存到指定路径
node generate.js "一只猫" --output /tmp/cat.png

# 文章插图模式
node generate.js --template article --input /path/to/article.md

# 封面图模式
node generate.js --template cover --input /path/to/article.md

# 封面图 + 指定风格
node generate.js --template cover --input /path/to/article.md --style minimal
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 第一个参数 | 提示词（prompt） | 必填（除非用模板） |
| `--provider` | 图像生成服务商 | zhipu |
| `--model` | 具体模型名 | provider 默认模型 |
| `--size` | 图片尺寸 | 1024x1024 |
| `--style` | 风格 | 无 |
| `--template` | 模板名（article/cover） | 无 |
| `--input` | 模板输入文件路径 | 无 |
| `--output` | 图片保存路径 | /tmp/image-gen/自动命名 |
| `--type` | 文章插图类型 | 自动选择 |

## Provider 配置

配置文件：`config/providers.json`

### 智谱 (zhipu)

- API Key：环境变量 `ZHIPU_API_KEY` 或配置文件
- 支持模型：
  - `glm-image` — 旗舰模型（默认）
  - `cogview-4-250304` — CogView 4
  - `cogview-3-flash` — 免费模型
- 支持尺寸：1024x1024, 768x1344, 864x1152, 1344x768, 1152x864, 1440x720, 720x1440

### OpenAI (openai)

- API Key：环境变量 `OPENAI_API_KEY` 或配置文件
- 支持模型：
  - `gpt-image-1.5` — 默认
  - `dall-e-3`
- dall-e-3 额外支持 `--style` 参数（natural/vivid）

## 模板

### 文章插图 (article)

读取 Markdown 文章，自动分析主题生成插图提示词。

支持插图类型（`--type`）：
- `infographic` — 信息图
- `scene` — 场景图
- `flowchart` — 流程图
- `comparison` — 对比图
- `framework` — 框架图
- `timeline` — 时间线

不指定 `--type` 时自动根据文章内容选择。

### 封面图 (cover)

读取文章标题和摘要，生成封面图提示词。默认尺寸 1344x768（横版）。

支持风格（`--style`）：
- `minimal` — 极简
- `conceptual` — 概念
- `typography` — 字体排版
- `hero` — 主视觉（默认）

## 输出格式

```json
{
  "success": true,
  "url": "https://...",
  "localPath": "/tmp/image-gen/zhipu-1234567890-abc123.png",
  "model": "glm-image",
  "provider": "zhipu",
  "prompt": "一只赛博三花猫",
  "size": "1024x1024",
  "timestamp": "2026-02-15T05:30:00.000Z"
}
```

## 扩展指南：添加新 Provider

1. 在 `scripts/providers/` 下创建新文件（如 `doubao.js`）
2. 继承 `BaseProvider`，实现 `generate()` 和 `getName()`
3. 在 `generate.js` 的 `PROVIDERS` 注册表中添加一行
4. 在 `config/providers.json` 中添加配置

```javascript
// scripts/providers/doubao.js
const BaseProvider = require('./base');

class DoubaoProvider extends BaseProvider {
  getName() { return 'doubao'; }

  async generate(prompt, options = {}) {
    const apiKey = this.getApiKey('DOUBAO_API_KEY');
    // ... 实现 API 调用 ...
    return { success: true, url, localPath, model, provider: this.getName() };
  }
}

module.exports = DoubaoProvider;
```

```javascript
// generate.js 中添加注册
const PROVIDERS = {
  zhipu: () => require('./providers/zhipu'),
  openai: () => require('./providers/openai'),
  doubao: () => require('./providers/doubao')  // 新增
};
```
