#!/usr/bin/env node
/**
 * 微信公众号文章抓取脚本
 * 针对微信公众号文章页面优化
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// 解析命令行参数
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    url: null,
    wait: 3000,
    screenshot: false,
    timeout: 30000
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith('--')) {
      const key = arg.slice(2);
      if (key === 'wait') {
        options.wait = parseInt(args[++i], 10) || 3000;
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
      userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
      viewport: { width: 390, height: 844, isMobile: true },
      screenshotDir: '/tmp/screenshots'
    };
  }
}

// 微信 HTML 转 Markdown
function htmlToMarkdown(html) {
  let md = html;
  
  // 移除不需要的标签
  md = md.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
  md = md.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
  
  // 处理标题
  md = md.replace(/<h1[^>]*>([\s\S]*?)<\/h1>/gi, '\n# $1\n\n');
  md = md.replace(/<h2[^>]*>([\s\S]*?)<\/h2>/gi, '\n## $1\n\n');
  md = md.replace(/<h3[^>]*>([\s\S]*?)<\/h3>/gi, '\n### $1\n\n');
  md = md.replace(/<h4[^>]*>([\s\S]*?)<\/h4>/gi, '\n#### $1\n\n');
  
  // 处理段落
  md = md.replace(/<p[^>]*>([\s\S]*?)<\/p>/gi, '\n$1\n\n');
  
  // 处理 section 标签（微信常用）
  md = md.replace(/<section[^>]*>([\s\S]*?)<\/section>/gi, '$1\n');
  
  // 处理链接
  md = md.replace(/<a[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi, '[$2]($1)');
  
  // 处理图片（微信使用 data-src 懒加载）
  md = md.replace(/<img[^>]*data-src=["']([^"']+)["'][^>]*\/?>/gi, '![]($1)');
  md = md.replace(/<img[^>]*src=["']([^"']+)["'][^>]*alt=["']([^"']+)["'][^>]*\/?>/gi, '![$2]($1)');
  md = md.replace(/<img[^>]*src=["']([^"']+)["'][^>]*\/?>/gi, '![]($1)');
  
  // 处理列表
  md = md.replace(/<li[^>]*>([\s\S]*?)<\/li>/gi, '- $1\n');
  md = md.replace(/<\/?[ou]l[^>]*>/gi, '\n');
  
  // 处理强调
  md = md.replace(/<strong[^>]*>([\s\S]*?)<\/strong>/gi, '**$1**');
  md = md.replace(/<b[^>]*>([\s\S]*?)<\/b>/gi, '**$1**');
  md = md.replace(/<em[^>]*>([\s\S]*?)<\/em>/gi, '*$1*');
  md = md.replace(/<i[^>]*>([\s\S]*?)<\/i>/gi, '*$1*');
  
  // 处理颜色和字体（保留内容）
  md = md.replace(/<font[^>]*>([\s\S]*?)<\/font>/gi, '$1');
  md = md.replace(/<span[^>]*>([\s\S]*?)<\/span>/gi, '$1');
  
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
  md = md.replace(/&mdash;/g, '—');
  md = md.replace(/&ndash;/g, '–');
  
  // 清理多余空白
  md = md.replace(/\n{3,}/g, '\n\n');
  md = md.replace(/[ \t]+/g, ' ');
  md = md.trim();
  
  return md;
}

// 主函数
async function main() {
  const options = parseArgs();
  const config = loadConfig();
  
  // 微信公众号必须用移动端 UA 才能绕过反爬
  config.userAgent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1';
  config.viewport = { width: 390, height: 844, isMobile: true };
  
  if (!options.url) {
    console.error(JSON.stringify({
      success: false,
      error: '请提供微信公众号文章 URL',
      usage: 'node wechat.js <URL> [--wait <ms>] [--screenshot] [--timeout <ms>]'
    }));
    process.exit(1);
  }

  // 检查是否是微信链接
  if (!options.url.includes('mp.weixin.qq.com')) {
    console.error(JSON.stringify({
      success: false,
      error: '请提供有效的微信公众号文章链接（mp.weixin.qq.com）',
      url: options.url
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

    // 等待微信文章内容加载
    try {
      await page.waitForSelector('#js_content', { timeout: 15000 });
    } catch (e) {
      throw new Error('微信文章内容加载失败，可能是文章不存在或链接无效');
    }

    // 额外等待时间（确保图片等资源加载）
    if (options.wait > 0) {
      await new Promise(resolve => setTimeout(resolve, options.wait));
    }

    // 提取文章信息
    const articleInfo = await page.evaluate(() => {
      // 标题
      const titleEl = document.querySelector('#activity-name');
      const title = titleEl ? titleEl.textContent.trim() : '';
      
      // 作者/公众号名称
      const authorEl = document.querySelector('#js_name');
      const author = authorEl ? authorEl.textContent.trim() : '';
      
      // 发布时间
      const timeEl = document.querySelector('#publish_time');
      const publishTime = timeEl ? timeEl.textContent.trim() : '';
      
      // 正文 HTML
      const contentEl = document.querySelector('#js_content');
      const contentHtml = contentEl ? contentEl.innerHTML : '';
      
      // 提取图片（包括懒加载）
      const images = [];
      if (contentEl) {
        const imgElements = contentEl.querySelectorAll('img');
        imgElements.forEach(img => {
          // 优先使用 data-src（微信懒加载），其次使用 src
          const src = img.getAttribute('data-src') || img.src;
          if (src && !src.startsWith('data:')) {
            images.push({
              src: src,
              alt: img.alt || ''
            });
          }
        });
      }
      
      return {
        title,
        author,
        publishTime,
        contentHtml,
        images
      };
    });

    // 转换为 Markdown
    const content = htmlToMarkdown(articleInfo.contentHtml);

    // 结果
    const result = {
      success: true,
      title: articleInfo.title,
      author: articleInfo.author,
      publishTime: articleInfo.publishTime,
      content: content,
      images: articleInfo.images,
      url: options.url,
      timestamp: new Date().toISOString()
    };

    // 截图
    if (options.screenshot) {
      const screenshotDir = config.screenshotDir;
      if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir, { recursive: true });
      }
      const screenshotPath = path.join(screenshotDir, `wechat-${Date.now()}.png`);
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
