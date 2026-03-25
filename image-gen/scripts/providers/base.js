'use strict';

/**
 * BaseProvider - 图像生成 Provider 基类
 * 所有 provider 必须继承此类并实现所有方法
 */
class BaseProvider {
  constructor(config = {}) {
    this.config = config;
    this.apiKey = config.apiKey || '';
    this.baseUrl = config.baseUrl || '';
    this.defaultModel = config.defaultModel || '';
    this.models = config.models || [];
  }

  /**
   * 生成图片
   * @param {string} prompt - 提示词
   * @param {object} options - 选项
   * @param {string} [options.model] - 模型名
   * @param {string} [options.size] - 尺寸，默认 1024x1024
   * @param {string} [options.style] - 风格
   * @param {string} [options.savePath] - 保存路径
   * @returns {Promise<{success: boolean, url: string, localPath: string, model: string, provider: string}>}
   */
  async generate(prompt, options = {}) {
    throw new Error('generate() must be implemented by subclass');
  }

  /**
   * 下载图片到本地
   * @param {string} url - 图片 URL
   * @param {string} savePath - 本地保存路径
   * @returns {Promise<string>} 本地文件路径
   */
  async download(url, savePath) {
    const fs = require('fs');
    const path = require('path');

    // 确保目录存在
    const dir = path.dirname(savePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status} ${response.statusText}`);
    }

    const buffer = Buffer.from(await response.arrayBuffer());
    fs.writeFileSync(savePath, buffer);
    return savePath;
  }

  /**
   * 返回支持的模型列表
   * @returns {string[]}
   */
  getModels() {
    return this.models;
  }

  /**
   * 返回 provider 名称
   * @returns {string}
   */
  getName() {
    throw new Error('getName() must be implemented by subclass');
  }

  /**
   * 获取 API Key（优先环境变量）
   * @param {string} envKey - 环境变量名
   * @returns {string}
   */
  getApiKey(envKey) {
    return process.env[envKey] || this.apiKey;
  }

  /**
   * 生成默认保存路径
   * @param {string} outputDir - 输出目录
   * @param {string} [ext=png] - 文件扩展名
   * @returns {string}
   */
  generateSavePath(outputDir, ext = 'png') {
    const path = require('path');
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 8);
    return path.join(outputDir, `${this.getName()}-${timestamp}-${random}.${ext}`);
  }
}

module.exports = BaseProvider;
