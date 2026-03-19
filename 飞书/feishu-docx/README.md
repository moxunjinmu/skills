# 飞书文档技能

帮助用户创建、读取、更新飞书文档。支持将 Markdown 内容转换为飞书块格式。

## 功能特性

✅ **Markdown 转飞书块格式**：自动将 Markdown 转换为飞书支持的块类型
✅ **创建新文档**：从 Markdown 文件一键创建飞书文档
✅ **追加内容**：向现有文档追加 Markdown 内容
✅ **读取文档**：读取飞书文档内容

## 安装

### 1. 克隆或下载技能
技能位置：`~/.agents/skills/feishu-docx/`

### 2. 安装依赖
```bash
cd ~/.agents/skills/feishu-docx/scripts
npm install
```

### 3. 配置环境变量

在 `~/.bashrc` 或 `~/.zshrc` 中添加：
```bash
export FEISHU_TENANT_ACCESS_TOKEN="your_token_here"
```

然后重新加载配置：
```bash
source ~/.bashrc
# 或
source ~/.zshrc
```

### 4. 获取飞书 Token

1. 访问飞书开放平台：https://open.feishu.cn
2. 创建应用
3. 获取租户访问令牌
4. 设置环境变量

## 使用方法

### 方式 1：命令行工具

#### 创建新文档
```bash
cd ~/.agents/skills/feishu-docx/scripts
node index.js create /path/to/file.md "文档标题"
```

#### 追加内容到现有文档
```bash
node index.js append <document_token> /path/to/addendum.md
```

#### 读取文档内容
```bash
node index.js read <document_token> <obj_token> <obj_type>
```

#### 转换 Markdown 为飞书块格式
```bash
node index.js convert /path/to/file.md output.json
```

### 方式 2：作为 OpenClaw 技能使用

在对话中直接使用：

```
请帮我创建一个飞书文档，文件是 /root/my-assistant/docs/seedance-storyboard-prompts.md
```

或

```
请将这个 Markdown 文件的内容追加到飞书文档 [document_token]：/root/my-assistant/docs/chapter1.md
```

## Markdown 语法支持

### 标题
```markdown
# 一级标题 → Heading1 块
## 二级标题 → Heading2 块
### 三级标题 → Heading3 块
```

### 列表
```markdown
- 无序列表项 → Bullet 块
1. 有序列表项 → Ordered 块
```

### 代码块
```markdown
\`\`\`
代码内容
\`\`\`
→ Code 块
```

### 引用
```markdown
> 引用内容 → Quote 块
```

### 分隔线
```markdown
---
或
***
→ Divider 块
```

## 注意事项

1. **Markdown 格式**
   - 使用标准 Markdown 语法
   - 标题使用 `#`, `##`, `###`
   - 列表项以 `-` 或数字开头
   - 代码块使用三个反引号包裹

2. **块类型限制**
   - 飞书支持的块类型有限
   - 复杂嵌套可能需要简化
   - 表格需要特殊处理（当前版本不支持）

3. **访问权限**
   - 确保创建的文档在指定文件夹中
   - 检查用户是否有足够的权限
   - Token 需要定期更新

4. **性能考虑**
   - 大文件可能分块创建
   - 考虑使用异步操作
   - 网络超时时间：30 秒

## 常见问题

### Q: Token 过期了怎么办？
A: 重新获取飞书 Token 并更新环境变量，然后重新加载配置。

### Q: 文档创建成功了，但是格式不对？
A: 检查 Markdown 文件的语法是否符合规范，特别是标题和列表的格式。

### Q: 如何在文档中插入图片？
A: 当前版本支持文本块转换。插入图片需要使用飞书 API 的图片上传功能，后续版本可能会支持。

### Q: 支持表格吗？
A: 当前版本不支持自动转换表格。需要手动在飞书文档中创建表格。

### Q: 如何获取 document_token？
A: 创建文档后，会返回 document_token，保存下来以便后续追加内容。

## 示例工作流

### 1. 创建新文档
```bash
node index.js create README.md "项目文档"
```

输出：
```
正在创建文档...
文件: README.md
标题: 项目文档
✅ 文档创建成功！
文档 ID: doxcnxxxxxxxxxxxxxx
URL: https://feishu.cn/docx/xxxxxxxxxxxxxx

下一步:
1. 打开文档: https://feishu.cn/docx/xxxxxxxxxxxxxx
2. 如果需要追加内容，使用以下命令：
   node index.js append doxcnxxxxxxxxxxxxxx chapter2.md
```

### 2. 追加内容
```bash
node index.js append doxcnxxxxxxxxxxxxxx chapter2.md
```

输出：
```
正在追加内容...
文档 ID: doxcnxxxxxxxxxxxxxx
文件: chapter2.md
✅ 内容追加成功！
创建的块数量: 15
```

### 3. 读取文档
```bash
node index.js read doxcnxxxxxxxxxxxxxx
```

输出：
```
正在读取文档...
文档 ID: doxcnxxxxxxxxxxxxxx
✅ 文档读取成功！

文档内容:
{ "blocks": [...] }
```

## 技术实现

### 文件结构
```
feishu-docx/
├── SKILL.md                 # 技能定义
├── README.md                # 本文件
└── scripts/
    ├── index.js             # 主脚本
    ├── markdown-to-blocks.js  # Markdown 转换器
    └── feishu-api.js        # 飞书 API 封装
```

### 核心组件

1. **MarkdownToFeishu**: Markdown 解析和转换类
   - 解析 Markdown 行
   - 识别标题、列表、代码块等
   - 生成飞书块格式

2. **FeishuAPI**: 飞书 API 封装类
   - 创建文档
   - 创建块
   - 读取文档
   - 处理认证和错误

3. **FeishuDocSkill**: 主技能类
   - 整合所有功能
   - 提供命令行接口
   - 错误处理和日志

## 依赖

- Node.js >= 14
- npm
- https（Node.js 内置）

## 许可证

Proprietary. LICENSE.txt has complete terms.

## 更新日志

### v1.0.0 (2026-02-11)
- ✅ 初始版本发布
- ✅ 支持 Markdown 转飞书块格式
- ✅ 支持创建新文档
- ✅ 支持追加内容到现有文档
- ✅ 支持读取文档内容
