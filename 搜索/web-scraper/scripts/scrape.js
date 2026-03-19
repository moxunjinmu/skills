#!/usr/bin/env node
/**
 * 通用网页抓取脚本
 * 使用 Puppeteer 无头浏览器抓取网页内容并转为 Markdown
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// 解析命令行参数
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    url: null,
    wait: 2000,
    selector: 'body',
    screenshot: false,
    timeout: 30000
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith('--')) {
      const key = arg.slice(2);
      if (key === 'wait') {
        options.wait = parseInt(args[++i], 10) || 2000;
      } else if (key === 'selector') {
        options.selector = args[++i] || 'body';
      } else if (key === 'screenshot') {
        options.screenshot = true;
      } else if (key === 'timeout') {
        options.timeout = parseInt(args[++i], 10) || 30000;
      }
    } else if (!options.url) {
      options.url = arg;
    }
  }

  return options;
}

// 加载默认配置
function loadConfig() {
  const configPath = path.join(__dirname, '..', 'config', 'default.json');
  try {
    return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  } catch (e) {
    return {
      timeout: 30000,
      waitAfterLoad: 2000,
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      viewport: { width: 1280, height: 800 },
      screenshotDir: '/tmp/screenshots'
    };
  }
}

// HTML 转 Markdown（简化版）
function htmlToMarkdown(html) {
  let md = html;
  
  // 移除 script、style 标签
  md = md.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
  md = md.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
  md = md.replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, '');
  md = md.replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, '');
  md = md.replace(/<header[^>]*>[\s\S]*?<\/header>/gi, '');
  
  // 处理标题
  md = md.replace(/<h1[^>]*>([\s\S]*?)<\/h1>/gi, '\n# $1\n\n');
  md = md.replace(/<h2[^>]*>([\s\S]*?)<\/h2>/gi, '\n## $1\n\n');
  md = md.replace(/<h3[^>]*>([\s\S]*?)<\/h3>/gi, '\n### $1\n\n');
  md = md.replace(/<h4[^>]*>([\s\S]*?)<\/h4>/gi, '\n#### $1\n\n');
  md = md.replace(/<h5[^>]*>([\s\S]*?)<\/h5>/gi, '\n##### $1\n\n');
  md = md.replace(/<h6[^>]*>([\s\S]*?)<\/h6>/gi, '\n###### $1\n\n');
  
  // 处理段落
  md = md.replace(/<p[^>]*>([\s\S]*?)<\/p>/gi, '\n$1\n\n');
  
  // 处理链接
  md = md.replace(/<a[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi, '[$2]($1)');
  
  // 处理图片
  md = md.replace(/<img[^>]*src=["']([^"']+)["'][^>]*alt=["']([^"']+)["'][^>]*\/?>/gi, '![$2]($1)');
  md = md.replace(/<img[^>]*alt=["']([^"']+)["'][^>]*src=["']([^"']+)["'][^>]*\/?>/gi, '![$1]($2)');
  md = md.replace(/<img[^>]*src=["']([^"']+)["'][^>]*\/?>/gi, '![]($1)');
  
  // 处理列表
  md = md.replace(/<li[^>]*>([\s\S]*?)<\/li>/gi, '- $1\n');
  md = md.replace(/<\/?[ou]l[^>]*>/gi, '\n');
  
  // 处理强调
  md = md.replace(/<strong[^>]*>([\s\S]*?)<\/strong>/gi, '**$1**');
  md = md.replace(/<b[^>]*>([\s\S]*?)<\/b>/gi, '**$1**');
  md = md.replace(/<em[^>]*>([\s\S]*?)<\/em>/gi, '*$1*');
  md = md.replace(/<i[^>]*>([\s\S]*?)<\/i>/gi, '*$1*');
  
  // 处理代码
  md = md.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, '`$1`');
  md = md.replace(/<pre[^>]*>([\s\S]*?)<\/pre>/gi, '\n```\n$1\n```\n');
  
  // 处理换行
  md = md.replace(/<br\s*\/?>/gi, '\n');
  md = md.replace(/<div[^>]*>/gi, '\n');
  md = md.replace(/<\/div>/gi, '');
  
  // 处理块引用
  md = md.replace(/<blockquote[^>]*>([\s\S]*?)<\/blockquote>/gi, '\n> $1\n');
  
  // 清理其他标签
  md = md.replace(/<[^>]+>/g, '');
  
  // 解码 HTML 实体
  md = md.replace(/&nbsp;/g, ' ');
  md = md.replace(/&amp;/g, '&');
  md = md.replace(/&lt;/g, '<');
  md = md.replace(/&gt;/g, '>');
  md = md.replace(/&quot;/g, '"');
  md = md.replace(/&#39;/g, "'");
  
  // 清理多余空白
  md = md.replace(/\n{3,}/g, '\n\n');
  md = md.replace(/[ \t]+/g, ' ');
  md = md.trim();
  
  return md;
}

// 提取图片链接
function extractImages(page, selector) {
  return page.evaluate((sel) => {
    const imgs = [];
    const elements = document.querySelectorAll(`${sel} img`);
    elements.forEach(img => {
      const src = img.src || img.getAttribute('data-src');
      if (src && !src.startsWith('data:')) {
        imgs.push({
          src: src,
          alt: img.alt || ''
        });
      }
    });
    return imgs;
  }, selector);
}

// 主函数
async function main() {
  const options = parseArgs();
  const config = loadConfig();
  
  if (!options.url) {
    console.error(JSON.stringify({
      success: false,
      error: '请提供 URL 参数',
      usage: 'node scrape.js <URL> [--wait <ms>] [--selector <css>] [--screenshot] [--timeout <ms>]'
    }));
    process.exit(1);
  }

  let browser = null;
  
  try {
    // 启动浏览器
    browser = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu',
        '--window-size=1280,800'
      ]
    });

    const page = await browser.newPage();
    
    // 设置 User-Agent 和视口
    await page.setUserAgent(config.userAgent);
    await page.setViewport(config.viewport);
    
    // 设置超时
    page.setDefaultTimeout(options.timeout);

    // 导航到页面
    await page.goto(options.url, {
      waitUntil: 'networkidle2',
      timeout: options.timeout
    });

    // 等待选择器出现
    try {
      await page.waitForSelector(options.selector, { timeout: 10000 });
    } catch (e) {
      // 选择器未找到，使用 body
      options.selector = 'body';
    }

    // 额外等待时间
    if (options.wait > 0) {
      await new Promise(resolve => setTimeout(resolve, options.wait));
    }

    // 获取页面标题
    const title = await page.title();

    // 获取内容 HTML
    const contentHtml = await page.evaluate((sel) => {
      const element = document.querySelector(sel);
      return element ? element.innerHTML : '';
    }, options.selector);

    // 转换为 Markdown
    const content = htmlToMarkdown(contentHtml);

    // 提取图片
    const images = await extractImages(page, options.selector);

    // 结果
    const result = {
      success: true,
      title: title,
      content: content,
      url: options.url,
      images: images,
      timestamp: new Date().toISOString()
    };

    // 截图
    if (options.screenshot) {
      const screenshotDir = config.screenshotDir;
      if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir, { recursive: true });
      }
      const screenshotPath = path.join(screenshotDir, `scrape-${Date.now()}.png`);
      await page.screenshot({
        path: screenshotPath,
        fullPage: true
      });
      result.screenshot = screenshotPath;
    }

    console.log(JSON.stringify(result, null, 2));

  } catch (error) {
    console.error(JSON.stringify({
      success: false,
      error: error.message,
      url: options.url
    }));
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

main();
