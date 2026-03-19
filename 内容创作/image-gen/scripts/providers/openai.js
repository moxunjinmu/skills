'use strict';

const BaseProvider = require('./base');

class OpenAIProvider extends BaseProvider {
  constructor(config = {}) {
    super(config);
    if (!this.defaultModel) this.defaultModel = 'gpt-image-1.5';
    if (!this.models.length) this.models = ['gpt-image-1.5', 'dall-e-3'];
  }

  getName() {
    return 'openai';
  }

  async generate(prompt, options = {}) {
    const apiKey = this.getApiKey('OPENAI_API_KEY');
    if (!apiKey) {
      throw new Error('OpenAI API Key 未配置。请设置环境变量 OPENAI_API_KEY 或在 providers.json 中配置。');
    }

    const model = options.model || this.defaultModel;
    const size = options.size || '1024x1024';

    const url = `${this.baseUrl || 'https://api.openai.com/v1'}/images/generations`;

    const body = {
      model,
      prompt,
      n: 1,
      size
    };

    // dall-e-3 支持 style 参数
    if (options.style && model === 'dall-e-3') {
      body.style = options.style;
    }

    // dall-e-3 支持 quality 参数
    if (options.quality && model === 'dall-e-3') {
      body.quality = options.quality;
    }

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
      throw new Error(`OpenAI API 错误 (${response.status}): ${errorText}`);
    }

    const data = await response.json();

    if (!data.data || !data.data[0]) {
      throw new Error(`OpenAI API 返回格式异常: ${JSON.stringify(data)}`);
    }

    const imageUrl = data.data[0].url || '';
    const b64Json = data.data[0].b64_json || '';

    let localPath = '';
    const outputDir = options.outputDir || '/tmp/image-gen';
    const savePath = options.savePath || this.generateSavePath(outputDir);

    if (b64Json) {
      // gpt-image 可能返回 base64
      const fs = require('fs');
      const path = require('path');
      const dir = path.dirname(savePath);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(savePath, Buffer.from(b64Json, 'base64'));
      localPath = savePath;
    } else if (imageUrl) {
      localPath = await this.download(imageUrl, savePath);
    }

    return {
      success: true,
      url: imageUrl,
      localPath,
      model,
      provider: this.getName()
    };
  }
}

module.exports = OpenAIProvider;
