#!/usr/bin/env node

/**
 * 飞书文档技能主脚本
 * 提供统一的命令行接口
 */

const fs = require('fs');
const path = require('path');
const MarkdownToFeishu = require('./markdown-to-blocks');
const FeishuAPI = require('./feishu-api');

class FeishuDocSkill {
  constructor() {
    this.tenantToken = process.env.FEISHU_TENANT_ACCESS_TOKEN;
    if (!this.tenantToken) {
      throw new Error('错误: 请设置环境变量 FEISHU_TENANT_ACCESS_TOKEN');
    }
    this.api = new FeishuAPI(this.tenantToken);
  }

  /**
   * 从 Markdown 创建新文档
   */
  async createFromMarkdown(markdownPath, title) {
    const markdown = fs.readFileSync(markdownPath, 'utf-8');
    const converter = new MarkdownToFeishu(markdown);
    const content = converter.toFeishuBlocks();

    const result = await this.api.createDocument({
      title: title || path.basename(markdownPath, '.md'),
      content: content
    });

    return result;
  }

  /**
   * 追加 Markdown 内容到现有文档
   */
  async appendToDocument(documentToken, markdownPath) {
    const markdown = fs.readFileSync(markdownPath, 'utf-8');
    const converter = new MarkdownToFeishu(markdown);
    const content = converter.toFeishuBlocks();

    const result = await this.api.createBlocks(documentToken, content.blocks);

    return result;
  }

  /**
   * 读取文档内容
   */
  async readDocument(documentToken, objToken, objType) {
    const result = await this.api.getDocument(documentToken, objToken, objType);
    return result;
  }

  /**
   * 显示帮助信息
   */
  showHelp() {
    console.log(`
📚 飞书文档技能 - 命令行工具

用法: node index.js <command> [options...]

命令:
  create <markdown-file> [title]              - 从 Markdown 文件创建新文档
  append <document-token> <markdown-file>   - 追加 Markdown 内容到现有文档
  read <document-token> [obj-token] [obj-type] - 读取文档内容
  convert <markdown-file> [output-file]        - 将 Markdown 转换为飞书块格式

环境变量:
  FEISHU_TENANT_ACCESS_TOKEN              - 必需，飞书访问令牌

示例:
  # 创建新文档
  node index.js create README.md "即梦分镜提示词"

  # 追加内容
  node index.js append doc_xxxxxxxxxx addendum.md

  # 读取文档
  node index.js read doc_xxxxxxxxxx

  # 转换 Markdown
  node index.js convert README.md output.json
    `);
  }

  /**
   * 执行命令
   */
  async execute() {
    const args = process.argv.slice(2);

    if (args.length === 0) {
      this.showHelp();
      return;
    }

    const command = args[0];

    try {
      switch (command) {
        case 'create': {
          if (args.length < 2) {
            console.error('错误: 请指定 Markdown 文件路径');
            this.showHelp();
            process.exit(1);
          }

          const markdownPath = args[1];
          const title = args[2] || null;

          console.log(`正在创建文档...`);
          console.log(`文件: ${markdownPath}`);
          if (title) console.log(`标题: ${title}`);

          const result = await this.createFromMarkdown(markdownPath, title);

          console.log('✅ 文档创建成功！');
          console.log(`文档 ID: ${result.document.document_id}`);
          console.log(`文档 URL: ${result.url}`);
          console.log('');
          console.log('下一步:');
          console.log(`1. 打开文档: ${result.url}`);
          console.log(`2. 如果需要追加内容，使用: node index.js append ${result.document.document_id} <markdown-file>`);
          break;
        }

        case 'append': {
          if (args.length < 3) {
            console.error('错误: 请指定文档 Token 和 Markdown 文件路径');
            this.showHelp();
            process.exit(1);
          }

          const documentToken = args[1];
          const markdownPath = args[2];

          console.log(`正在追加内容...`);
          console.log(`文档 ID: ${documentToken}`);
          console.log(`文件: ${markdownPath}`);

          const result = await this.appendToDocument(documentToken, markdownPath);

          console.log('✅ 内容追加成功！');
          console.log(`创建的块数量: ${result.data.block_ids.length}`);
          break;
        }

        case 'read': {
          if (args.length < 2) {
            console.error('错误: 请指定文档 Token');
            this.showHelp();
            process.exit(1);
          }

          const documentToken = args[1];
          const objToken = args[2];
          const objType = args[3];

          console.log(`正在读取文档...`);
          console.log(`文档 ID: ${documentToken}`);

          const result = await this.readDocument(documentToken, objToken, objType);

          console.log('✅ 文档读取成功！');
          console.log('');
          console.log('文档内容:');
          console.log(JSON.stringify(result, null, 2));
          break;
        }

        case 'convert': {
          if (args.length < 2) {
            console.error('错误: 请指定 Markdown 文件路径');
            this.showHelp();
            process.exit(1);
          }

          const markdownPath = args[1];
          const outputPath = args[2] || null;

          console.log(`正在转换 Markdown...`);
          console.log(`文件: ${markdownPath}`);

          const markdown = fs.readFileSync(markdownPath, 'utf-8');
          const converter = new MarkdownToFeishu(markdown);
          const result = converter.toFeishuBlocks();

          if (outputPath) {
            fs.writeFileSync(outputPath, JSON.stringify(result, null, 2));
            console.log(`✅ 转换成功，结果已保存到 ${outputPath}`);
          } else {
            console.log('✅ 转换成功！');
            console.log('');
            console.log('飞书块格式:');
            console.log(JSON.stringify(result, null, 2));
          }
          break;
        }

        default: {
          console.error(`未知命令: ${command}`);
          console.log('');
          this.showHelp();
          process.exit(1);
        }
      }
    } catch (error) {
      console.error('❌ 执行失败:', error.message);
      console.error('');
      console.error('调试信息:');
      console.error(error.stack);
      process.exit(1);
    }
  }
}

// 执行主函数
if (require.main === module) {
  const skill = new FeishuDocSkill();
  skill.execute();
}

module.exports = FeishuDocSkill;
