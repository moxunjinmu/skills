#!/usr/bin/env node

/**
 * Markdown to Feishu Blocks Converter
 * 将 Markdown 内容转换为飞书块格式
 */

const fs = require('fs');

class MarkdownToFeishu {
  constructor(markdown) {
    this.markdown = markdown;
    this.lines = markdown.split('\n');
    this.pos = 0;
    this.blocks = [];
  }

  parse() {
    let currentParagraph = null;

    while (this.pos < this.lines.length) {
      const line = this.lines[this.pos];
      const trimmedLine = line.trim();

      // 空行，结束当前段落
      if (!trimmedLine) {
        if (currentParagraph) {
          this.blocks.push(currentParagraph);
          currentParagraph = null;
        }
        this.pos++;
        continue;
      }

      // 标题
      if (trimmedLine.startsWith('#')) {
        if (currentParagraph) {
          this.blocks.push(currentParagraph);
          currentParagraph = null;
        }
        this.parseHeading(trimmedLine);
        this.pos++;
        continue;
      }

      // 无序列表
      if (trimmedLine.startsWith('-') || trimmedLine.startsWith('*') || trimmedLine.startsWith('+')) {
        if (currentParagraph) {
          this.blocks.push(currentParagraph);
          currentParagraph = null;
        }
        this.parseBullet(line);
        this.pos++;
        continue;
      }

      // 有序列表
      if (/^\d+\./.test(trimmedLine)) {
        if (currentParagraph) {
          this.blocks.push(currentParagraph);
          currentParagraph = null;
        }
        this.parseOrdered(line);
        this.pos++;
        continue;
      }

      // 代码块
      if (trimmedLine.startsWith('```')) {
        if (currentParagraph) {
          this.blocks.push(currentParagraph);
          currentParagraph = null;
        }
        this.parseCodeBlock();
        continue;
      }

      // 引用
      if (trimmedLine.startsWith('>')) {
        if (currentParagraph) {
          this.blocks.push(currentParagraph);
          currentParagraph = null;
        }
        this.parseQuote();
        this.pos++;
        continue;
      }

      // 分隔线
      if (trimmedLine.startsWith('---') || trimmedLine.startsWith('***')) {
        if (currentParagraph) {
          this.blocks.push(currentParagraph);
          currentParagraph = null;
        }
        this.blocks.push({
          type: 'Divider'
        });
        this.pos++;
        continue;
      }

      // 普通文本
      if (!currentParagraph) {
        currentParagraph = {
          type: 'Text',
          elements: []
        };
      }
      currentParagraph.elements.push({
        type: 'TextRun',
        content: line
      });

      this.pos++;
    }

    // 最后一个段落
    if (currentParagraph) {
      this.blocks.push(currentParagraph);
    }

    return this.blocks;
  }

  parseHeading(line) {
    const match = line.match(/^(#{1,3})\s+(.+)$/);
    if (!match) return;

    const level = match[1].length;
    const text = match[2];

    let blockType;
    if (level === 1) {
      blockType = 'Heading1';
    } else if (level === 2) {
      blockType = 'Heading2';
    } else if (level === 3) {
      blockType = 'Heading3';
    } else {
      return;
    }

    this.blocks.push({
      type: blockType,
      elements: [{
        type: 'TextRun',
        content: text
      }]
    });
  }

  parseBullet(line) {
    const text = line.replace(/^[-*+]\s*/, '');

    this.blocks.push({
      type: 'Bullet',
      elements: [{
        type: 'TextRun',
        content: text
      }]
    });
  }

  parseOrdered(line) {
    const text = line.replace(/^\d+\.\s*/, '');

    this.blocks.push({
      type: 'Ordered',
      elements: [{
        type: 'TextRun',
        content: text
      }]
    });
  }

  parseCodeBlock() {
    let code = '';
    let language = '';

    // 第一行是 ```language 或 ```
    const firstLine = this.lines[this.pos];
    if (firstLine.startsWith('```')) {
      const match = firstLine.match(/^```(\w+)?$/);
      if (match && match[1]) {
        language = match[1];
      }
    }

    this.pos++;

    // 收集代码内容
    while (this.pos < this.lines.length) {
      const line = this.lines[this.pos];
      if (line.trim() === '```') {
        this.pos++;
        break;
      }
      code += line + '\n';
      this.pos++;
    }

    this.blocks.push({
      type: 'Code',
      elements: [{
        type: 'TextRun',
        content: code
      }],
      language: language
    });
  }

  parseQuote() {
    const text = this.lines[this.pos].replace(/^>\s*/, '');

    this.blocks.push({
      type: 'Quote',
      elements: [{
        type: 'TextRun',
        content: text
      }]
    });
  }

  toFeishuBlocks() {
    return {
      blocks: this.blocks
    };
  }
}

// CLI 接口
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error('Usage: node markdown-to-blocks.js <markdown-file> [output-file]');
    process.exit(1);
  }

  const inputPath = args[0];
  const outputPath = args[1] || null;

  try {
    const markdown = fs.readFileSync(inputPath, 'utf-8');
    const converter = new MarkdownToFeishu(markdown);
    const result = converter.toFeishuBlocks();

    if (outputPath) {
      fs.writeFileSync(outputPath, JSON.stringify(result, null, 2));
      console.log(`转换成功，结果已保存到 ${outputPath}`);
    } else {
      console.log(JSON.stringify(result, null, 2));
    }
  } catch (error) {
    console.error('转换失败:', error.message);
    process.exit(1);
  }
}

module.exports = MarkdownToFeishu;
