#!/usr/bin/env node

/**
 * 飞书 API 封装
 */

const https = require('https');

class FeishuAPI {
  constructor(tenantToken, appToken = null) {
    this.tenantToken = tenantToken;
    this.appToken = appToken;
    this.apiBase = 'https://open.feishu.cn/open-apis/docx/v1';
  }

  getHeaders() {
    const headers = {
      'Authorization': `Bearer ${this.tenantToken}`,
      'Content-Type': 'application/json'
    };
    return headers;
  }

  /**
   * 创建文档
   */
  async createDocument(options) {
    const {
      title,
      folderToken,
      content
    } = options;

    const payload = {
      title: title,
      parent_type: folderToken ? 'folder_token' : 'root',
      parent_token: folderToken || '',
      blocks: content.blocks || []
    };

    return this._request('/documents', payload);
  }

  /**
   * 创建块
   */
  async createBlocks(documentToken, blocks, index = 0) {
    const payload = {
      document_id: documentToken,
      blocks: blocks,
      index: index
    };

    return this._request('/documents/blocks/batchCreate', payload);
  }

  /**
   * 读取文档内容
   */
  async getDocument(documentToken, obj_token, obj_type) {
    const params = new URLSearchParams({
      document_id: documentToken,
      obj_token: obj_token,
      obj_type: obj_type
    });

    return this._request(`/documents/content?${params}`);
  }

  /**
   * 发送请求
   */
  async _request(path, payload) {
    const options = {
      hostname: 'open.feishu.cn',
      port: 443,
      path: `/open-apis/docx/v1${path}`,
      method: payload ? 'POST' : 'GET',
      headers: this.getHeaders()
    };

    return new Promise((resolve, reject) => {
      const req = https.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            const result = JSON.parse(data);

            if (result.code !== 0) {
              reject(new Error(`飞书 API 错误: ${result.msg}`));
              return;
            }

            resolve(result.data);
          } catch (error) {
            reject(new Error(`解析响应失败: ${error.message}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(new Error(`请求失败: ${error.message}`));
      });

      if (payload) {
        req.write(JSON.stringify(payload));
      }

      req.end();
    });
  }
}

// CLI 接口
if (require.main === module) {
  const args = process.argv.slice(2);
  const command = args[0];

  const tenantToken = process.env.FEISHU_TENANT_ACCESS_TOKEN;

  if (!tenantToken) {
    console.error('错误: 请设置环境变量 FEISHU_TENANT_ACCESS_TOKEN');
    console.error('export FEISHU_TENANT_ACCESS_TOKEN="your_token_here"');
    process.exit(1);
  }

  const api = new FeishuAPI(tenantToken);

  const executeCommand = async () => {
    try {
      if (command === 'create') {
        const filePath = args[1];
        const title = args[2] || '新建文档';

        if (!filePath) {
          console.error('用法: node feishu-api.js create <content-json> [title]');
          console.error('或者: node feishu-api.js create <markdown-file> [title]');
          process.exit(1);
        }

        let content;
        if (filePath.endsWith('.json')) {
          content = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
        } else if (filePath.endsWith('.md')) {
          const markdown = fs.readFileSync(filePath, 'utf-8');
          const converter = require('./markdown-to-blocks.js');
          const MdConverter = converter.MarkdownToFeishu;
          const mdConverter = new MdConverter(markdown);
          content = mdConverter.toFeishuBlocks();
        } else {
          console.error('不支持的文件格式，请使用 .json 或 .md');
          process.exit(1);
        }

        const result = await api.createDocument({
          title: title,
          content: content
        });

        console.log('✅ 文档创建成功！');
        console.log(`标题: ${title}`);
        console.log(`文档 ID: ${result.document.document_id}`);
        console.log(`URL: ${result.url}`);
        console.log('');
        console.log('下一步：');
        console.log(`1. 打开文档: ${result.url}`);
        console.log(`2. 如果需要追加内容，使用以下命令：`);
        console.log(`   node feishu-api.js append ${result.document.document_id} <markdown-file>`);

      } else if (command === 'append') {
        const documentToken = args[1];
        const filePath = args[2];

        if (!documentToken || !filePath) {
          console.error('用法: node feishu-api.js append <document_token> <markdown-file>');
          process.exit(1);
        }

        const markdown = fs.readFileSync(filePath, 'utf-8');
        const converter = require('./markdown-to-blocks.js');
        const MdConverter = converter.MarkdownToFeishu;
        const mdConverter = new MdConverter(markdown);
        const content = mdConverter.toFeishuBlocks();

        const result = await api.createBlocks(documentToken, content.blocks);

        console.log('✅ 内容追加成功！');
        console.log(`文档 ID: ${documentToken}`);
        console.log(`追加的块数量: ${content.blocks.length}`);

      } else if (command === 'read') {
        const documentToken = args[1];
        const obj_token = args[2];
        const obj_type = args[3];

        if (!documentToken || !obj_token || !obj_type) {
          console.error('用法: node feishu-api.js read <document_token> <obj_token> <obj_type>');
          process.exit(1);
        }

        const result = await api.getDocument(documentToken, obj_token, obj_type);

        console.log('文档内容：');
        console.log(JSON.stringify(result, null, 2));

      } else {
        console.error('未知命令:', command);
        console.log('');
        console.log('可用命令：');
        console.log('  create <content-json|markdown-file> [title]  - 创建新文档');
        console.log('  append <document_token> <markdown-file>       - 追加内容到文档');
        console.log('  read <document_token> <obj_token> <obj_type> - 读取文档');
        process.exit(1);
      }
    } catch (error) {
      console.error('❌ 执行失败:', error.message);
      process.exit(1);
    }
  };

  executeCommand();
}

module.exports = FeishuAPI;
