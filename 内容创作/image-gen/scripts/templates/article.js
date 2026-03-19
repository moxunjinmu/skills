'use strict';

/**
 * 文章插图提示词模板
 * 读取文章 Markdown 内容，分析主题，生成适合的插图提示词
 */

const ILLUSTRATION_TYPES = {
  infographic: {
    name: '信息图',
    prefix: 'A clean, modern infographic illustration showing',
    suffix: 'minimalist style, flat design, professional color palette, no text'
  },
  scene: {
    name: '场景图',
    prefix: 'A vivid, detailed scene depicting',
    suffix: 'cinematic lighting, rich colors, photorealistic style'
  },
  flowchart: {
    name: '流程图',
    prefix: 'A visual flowchart or diagram illustrating',
    suffix: 'clean lines, clear hierarchy, modern design, no text labels'
  },
  comparison: {
    name: '对比图',
    prefix: 'A side-by-side visual comparison showing',
    suffix: 'split composition, contrasting elements, clear visual distinction'
  },
  framework: {
    name: '框架图',
    prefix: 'A conceptual framework visualization showing',
    suffix: 'structured layout, interconnected elements, professional diagram style'
  },
  timeline: {
    name: '时间线',
    prefix: 'A visual timeline illustration showing',
    suffix: 'horizontal progression, milestone markers, clean modern design'
  }
};

/**
 * 从文章内容中提取关键信息
 */
function extractArticleInfo(content) {
  const lines = content.split('\n');
  let title = '';
  const headings = [];
  const keywords = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!title && trimmed.startsWith('# ')) {
      title = trimmed.replace(/^#+\s*/, '');
    } else if (trimmed.match(/^#{2,3}\s/)) {
      headings.push(trimmed.replace(/^#+\s*/, ''));
    }
  }

  // 提取粗体关键词
  const boldMatches = content.match(/\*\*([^*]+)\*\*/g);
  if (boldMatches) {
    keywords.push(...boldMatches.map(m => m.replace(/\*\*/g, '')).slice(0, 10));
  }

  // 取前 500 字作为摘要
  const plainText = content.replace(/[#*`\[\]()>-]/g, ' ').replace(/\s+/g, ' ').trim();
  const summary = plainText.substring(0, 500);

  return { title, headings, keywords, summary };
}

/**
 * 自动选择最合适的插图类型
 */
function autoSelectType(info) {
  const text = `${info.title} ${info.headings.join(' ')} ${info.summary}`.toLowerCase();

  if (text.match(/流程|步骤|step|process|pipeline/)) return 'flowchart';
  if (text.match(/对比|比较|vs|versus|compare/)) return 'comparison';
  if (text.match(/框架|架构|structure|framework|system/)) return 'framework';
  if (text.match(/历史|发展|演变|timeline|evolution|history/)) return 'timeline';
  if (text.match(/数据|统计|分析|data|analytics|metrics/)) return 'infographic';
  return 'scene';
}

/**
 * 生成文章插图提示词
 * @param {string} content - 文章 Markdown 内容
 * @param {object} options
 * @param {string} [options.type] - 插图类型，不指定则自动选择
 * @returns {{prompt: string, type: string, title: string}}
 */
function generateArticlePrompt(content, options = {}) {
  const info = extractArticleInfo(content);
  const type = options.type || autoSelectType(info);
  const template = ILLUSTRATION_TYPES[type];

  if (!template) {
    throw new Error(`不支持的插图类型: ${type}。支持: ${Object.keys(ILLUSTRATION_TYPES).join(', ')}`);
  }

  const topicParts = [];
  if (info.title) topicParts.push(info.title);
  if (info.headings.length) topicParts.push(info.headings.slice(0, 3).join(', '));
  if (info.keywords.length) topicParts.push(`key concepts: ${info.keywords.slice(0, 5).join(', ')}`);

  const topic = topicParts.join('. ') || info.summary.substring(0, 200);

  const prompt = `${template.prefix} the concept of: ${topic}. ${template.suffix}`;

  return {
    prompt,
    type,
    title: info.title || 'Untitled'
  };
}

module.exports = { generateArticlePrompt, ILLUSTRATION_TYPES, extractArticleInfo };
