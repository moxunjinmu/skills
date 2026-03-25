'use strict';

const fs = require('fs');
const path = require('path');

// --- 加载配置 ---
const CONFIG_PATH = path.join(__dirname, '..', 'config', 'providers.json');

function loadConfig() {
  try {
    return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
  } catch (e) {
    console.error(`配置文件加载失败: ${CONFIG_PATH}\n${e.message}`);
    process.exit(1);
  }
}

// --- Provider 注册表 ---
const PROVIDERS = {
  zhipu: () => require('./providers/zhipu'),
  openai: () => require('./providers/openai')
};

function createProvider(name, config) {
  const factory = PROVIDERS[name];
  if (!factory) {
    throw new Error(`未知 provider: ${name}。可用: ${Object.keys(PROVIDERS).join(', ')}`);
  }
  const ProviderClass = factory();
  return new ProviderClass(config.providers[name] || {});
}

// --- 参数解析 ---
function parseArgs(argv) {
  const args = {
    prompt: '',
    provider: '',
    model: '',
    size: '',
    style: '',
    template: '',
    input: '',
    output: '',
    type: ''
  };

  let i = 0;
  while (i < argv.length) {
    const arg = argv[i];
    if (arg.startsWith('--')) {
      const key = arg.slice(2);
      const val = argv[i + 1] || '';
      if (key in args) {
        args[key] = val;
        i += 2;
      } else {
        console.error(`未知参数: ${arg}`);
        i++;
      }
    } else if (!args.prompt) {
      args.prompt = arg;
      i++;
    } else {
      i++;
    }
  }

  return args;
}

// --- 模板处理 ---
function processTemplate(templateName, inputPath, args) {
  if (!inputPath) {
    throw new Error(`使用模板 ${templateName} 时必须指定 --input 参数`);
  }

  if (!fs.existsSync(inputPath)) {
    throw new Error(`输入文件不存在: ${inputPath}`);
  }

  const content = fs.readFileSync(inputPath, 'utf-8');

  if (templateName === 'article') {
    const { generateArticlePrompt } = require('./templates/article');
    const result = generateArticlePrompt(content, { type: args.type || undefined });
    return { prompt: result.prompt, size: args.size || '1024x1024', meta: result };
  }

  if (templateName === 'cover') {
    const { generateCoverPrompt } = require('./templates/cover');
    const result = generateCoverPrompt(content, { style: args.style || undefined });
    return { prompt: result.prompt, size: args.size || result.size, meta: result };
  }

  throw new Error(`未知模板: ${templateName}。支持: article, cover`);
}

// --- 主流程 ---
async function main() {
  const args = parseArgs(process.argv.slice(2));
  const config = loadConfig();

  // 确定 prompt
  let prompt = args.prompt;
  let size = args.size || '1024x1024';
  let templateMeta = null;

  if (args.template) {
    const tmpl = processTemplate(args.template, args.input, args);
    prompt = tmpl.prompt;
    size = tmpl.size;
    templateMeta = tmpl.meta;
  }

  if (!prompt) {
    console.error('用法: node generate.js "提示词" [--provider zhipu] [--model cogview-3-flash] [--size 1024x1024]');
    console.error('      node generate.js --template article --input /path/to/article.md');
    console.error('      node generate.js --template cover --input /path/to/article.md');
    process.exit(1);
  }

  // 确定 provider
  const providerName = args.provider || config.defaultProvider || 'zhipu';
  const provider = createProvider(providerName, config);

  // 确保输出目录存在
  const outputDir = config.outputDir || '/tmp/image-gen';
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // 生成图片
  const options = {
    model: args.model || undefined,
    size,
    style: args.style || undefined,
    savePath: args.output || undefined,
    outputDir
  };

  const result = await provider.generate(prompt, options);

  // 输出结果
  const output = {
    ...result,
    prompt,
    size,
    timestamp: new Date().toISOString()
  };

  if (templateMeta) {
    output.template = args.template;
    if (templateMeta.type) output.illustrationType = templateMeta.type;
    if (templateMeta.style) output.coverStyle = templateMeta.style;
    if (templateMeta.title) output.articleTitle = templateMeta.title;
  }

  console.log(JSON.stringify(output, null, 2));
}

main().catch(err => {
  console.error(JSON.stringify({
    success: false,
    error: err.message,
    timestamp: new Date().toISOString()
  }, null, 2));
  process.exit(1);
});
