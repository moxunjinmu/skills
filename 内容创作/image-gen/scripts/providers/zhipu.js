'use strict';

const BaseProvider = require('./base');

const SUPPORTED_SIZES = [
  '1024x1024', '768x1344', '864x1152',
  '1344x768', '1152x864', '1440x720', '720x1440'
];

class ZhipuProvider extends BaseProvider {
  constructor(config = {}) {
    super(config);
    if (!this.defaultModel) this.defaultModel = 'glm-image';
    if (!this.models.length) this.models = ['glm-image', 'cogview-4-250304', 'cogview-3-flash'];
  }

  getName() {
    return 'zhipu';
  }

  async generate(prompt, options = {}) {
    const apiKey = this.getApiKey('ZHIPU_API_KEY');
    if (!apiKey) {
      throw new Error('智谱 API Key 未配置。请设置环境变量 ZHIPU_API_KEY 或在 providers.json 中配置。');
    }

    const model = options.model || this.defaultModel;
    const size = options.size || '1024x1024';

    if (!SUPPORTED_SIZES.includes(size)) {
      throw new Error(`不支持的尺寸: ${size}。支持: ${SUPPORTED_SIZES.join(', ')}`);
    }

    const url = `${this.baseUrl || 'https://open.bigmodel.cn/api/paas/v4'}/images/generations`;

    const body = { model, prompt, size };

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`智谱 API 错误 (${response.status}): ${errorText}`);
    }

    const data = await response.json();

    if (!data.data || !data.data[0] || !data.data[0].url) {
      throw new Error(`智谱 API 返回格式异常: ${JSON.stringify(data)}`);
    }

    const imageUrl = data.data[0].url;

    // 下载图片（URL 有时效性）
    const outputDir = options.outputDir || '/tmp/image-gen';
    const savePath = options.savePath || this.generateSavePath(outputDir);
    const localPath = await this.download(imageUrl, savePath);

    return {
      success: true,
      url: imageUrl,
      localPath,
      model,
      provider: this.getName()
    };
  }
}

module.exports = ZhipuProvider;
