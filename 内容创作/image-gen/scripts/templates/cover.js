'use strict';

/**
 * 封面图提示词模板
 * 读取文章标题和摘要，生成封面图提示词
 */

const COVER_STYLES = {
  minimal: {
    name: '极简',
    prefix: 'A minimalist, clean cover image representing',
    suffix: 'simple geometric shapes, muted color palette, lots of white space, elegant and modern'
  },
  conceptual: {
    name: '概念',
    prefix: 'A conceptual, abstract cover image symbolizing',
    suffix: 'metaphorical visual elements, artistic composition, bold colors, thought-provoking imagery'
  },
  typography: {
    name: '字体排版',
    prefix: 'A typography-focused cover design inspired by',
    suffix: 'creative text layout, decorative elements, balanced composition, no actual text, visual rhythm'
  },
  hero: {
    name: '主视觉',
    prefix: 'A striking hero image for an article about',
    suffix: 'dramatic lighting, high contrast, cinematic feel, professional photography style, wide aspect ratio'
  }
};

/**
 * 从文章中提取标题和摘要
 */
function extractCoverInfo(content) {
  const lines = content.split('\n');
  let title = '';
  let subtitle = '';
  const paragraphs = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!title && trimmed.startsWith('# ')) {
      title = trimmed.replace(/^#+\s*/, '');
    } else if (!subtitle && trimmed.startsWith('## ')) {
      subtitle = trimmed.replace(/^#+\s*/, '');
    } else if (trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('```') && !trimmed.startsWith('|') && !trimmed.startsWith('-')) {
      paragraphs.push(trimmed);
    }
  }

  const summary = paragraphs.slice(0, 3).join(' ').substring(0, 300);

  return { title, subtitle, summary };
}

/**
 * 生成封面图提示词
 * @param {string} content - 文章 Markdown 内容
 * @param {object} options
 * @param {string} [options.style] - 封面风格，默认 hero
 * @returns {{prompt: string, style: string, title: string, size: string}}
 */
function generateCoverPrompt(content, options = {}) {
  const info = extractCoverInfo(content);
  const style = options.style || 'hero';
  const template = COVER_STYLES[style];

  if (!template) {
    throw new Error(`不支持的封面风格: ${style}。支持: ${Object.keys(COVER_STYLES).join(', ')}`);
  }

  const topic = info.title || info.summary.substring(0, 100) || 'a technology article';
  const context = info.subtitle ? `, focusing on ${info.subtitle}` : '';
  const summaryHint = info.summary ? `. Context: ${info.summary.substring(0, 150)}` : '';

  const prompt = `${template.prefix} "${topic}"${context}${summaryHint}. ${template.suffix}`;

  return {
    prompt,
    style,
    title: info.title || 'Untitled',
    size: '1344x768' // 横版封面默认尺寸
  };
}

module.exports = { generateCoverPrompt, COVER_STYLES, extractCoverInfo };
