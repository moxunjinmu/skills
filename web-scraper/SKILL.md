---
name: web-scraper
description: 使用无头浏览器抓取网页内容。支持通用网页和微信公众号文章。当需要抓取 web_fetch 无法获取的页面（如微信公众号、有反爬的网站）时使用此技能。
---

# Web Scraper Skill

使用 Puppeteer 无头浏览器抓取网页内容，支持 JavaScript 渲染的页面和反爬网站。

## 使用方式

### 通用网页抓取

```bash
node /root/mo-hub/skills/web-scraper/scripts/scrape.js <URL> [选项]
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `URL` | 要抓取的网页地址（必填） | - |
| `--wait <ms>` | 页面加载后额外等待时间 | 2000 |
| `--selector <css>` | 内容选择器 | body |
| `--screenshot` | 截图保存到 /tmp/screenshots/ | false |
| `--timeout <ms>` | 超时时间 | 30000 |

**示例：**

```bash
# 基础用法
node /root/mo-hub/skills/web-scraper/scripts/scrape.js "https://example.com"

# 等待 5 秒后抓取
node /root/mo-hub/skills/web-scraper/scripts/scrape.js "https://example.com" --wait 5000

# 指定内容选择器
node /root/mo-hub/skills/web-scraper/scripts/scrape.js "https://example.com" --selector ".article-content"

# 抓取并截图
node /root/mo-hub/skills/web-scraper/scripts/scrape.js "https://example.com" --screenshot
```

### 微信公众号文章抓取

```bash
node /root/mo-hub/skills/web-scraper/scripts/wechat.js <URL> [选项]
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `URL` | 微信公众号文章链接（mp.weixin.qq.com）| - |
| `--wait <ms>` | 页面加载后额外等待时间 | 3000 |
| `--screenshot` | 截图保存 | false |
| `--timeout <ms>` | 超时时间 | 30000 |

**示例：**

```bash
# 抓取微信文章
node /root/mo-hub/skills/web-scraper/scripts/wechat.js "https://mp.weixin.qq.com/s/xxxxxx"

# 带截图
node /root/mo-hub/skills/web-scraper/scripts/wechat.js "https://mp.weixin.qq.com/s/xxxxxx" --screenshot
```

## 输出格式

### 通用抓取输出

```json
{
  "success": true,
  "title": "页面标题",
  "content": "# 正文内容\n\n转为 Markdown 格式...",
  "url": "https://example.com",
  "images": [
    {
      "src": "https://example.com/image.jpg",
      "alt": "图片描述"
    }
  ],
  "timestamp": "2026-02-15T02:43:00.000Z",
  "screenshot": "/tmp/screenshots/scrape-1234567890.png"  // 仅当 --screenshot 时
}
```

### 微信公众号输出

```json
{
  "success": true,
  "title": "文章标题",
  "author": "公众号名称",
  "publishTime": "2026-02-15",
  "content": "# 正文内容\n\n转为 Markdown 格式...",
  "images": [
    {
      "src": "https://mmbiz.qpic.cn/...",
      "alt": ""
    }
  ],
  "url": "https://mp.weixin.qq.com/s/xxxxxx",
  "timestamp": "2026-02-15T02:43:00.000Z",
  "screenshot": "/tmp/screenshots/wechat-1234567890.png"  // 仅当 --screenshot 时
}
```

### 错误输出

```json
{
  "success": false,
  "error": "错误信息",
  "url": "https://example.com"
}
```

## 特性

- **JavaScript 渲染**：支持 SPA、动态加载内容的页面
- **反爬处理**：模拟真实浏览器，绕过基础反爬检测
- **Markdown 转换**：自动将 HTML 转为 Markdown 格式
- **图片提取**：自动提取页面中的图片链接
- **微信公众号优化**：
  - 自动处理懒加载图片（data-src 属性）
  - 提取标题、作者、发布时间
  - 针对微信文章结构优化内容提取

## 适用场景

- `web_fetch` 无法抓取的页面（需要 JS 渲染）
- 微信公众号文章
- 有基础反爬的网站
- 需要截图存档的页面

## 注意事项

1. 运行需要 Puppeteer（已安装）
2. 首次运行可能需要下载 Chromium
3. 复杂页面可能需要调整 `--wait` 参数
4. 输出始终是 JSON 格式，便于程序解析
