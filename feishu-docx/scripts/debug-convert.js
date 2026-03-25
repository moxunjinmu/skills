#!/usr/bin/env node

const fs = require('fs');
const MarkdownToFeishu = require('./markdown-to-blocks');

const markdown = fs.readFileSync('/root/my-assistant/docs/feishu-test.md', 'utf-8');

console.log('=== 调试信息 ===');
console.log('Markdown 文件路径:', '/root/my-assistant/docs/feishu-test.md');
console.log('Markdown 内容前 200 字符:');
console.log(markdown.substring(0, 200));
console.log('');
console.log('=== 开始转换 ===');

const converter = new MarkdownToFeishu(markdown);
const result = converter.toFeishuBlocks();

console.log('');
console.log('=== 转换结果 ===');
console.log('块数量:', result.blocks.length);
console.log('');
console.log('=== 块详情 ===');
result.blocks.forEach((block, index) => {
  console.log(`块 ${index + 1}:`);
  console.log(`  类型: ${block.type}`);
  if (block.elements) {
    console.log(`  元素数量: ${block.elements.length}`);
    block.elements.forEach((element, elemIndex) => {
      console.log(`    元素 ${elemIndex + 1}: ${element.type}`);
      if (element.content) {
        const preview = element.content.length > 50
          ? element.content.substring(0, 50) + '...'
          : element.content;
        console.log(`      内容: "${preview}"`);
      }
    });
  }
  if (block.language) {
    console.log(`  语言: ${block.language}`);
  }
  console.log('');
});
