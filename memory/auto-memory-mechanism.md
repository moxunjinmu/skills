# 自动记忆机制

## 触发时机

- **会话结束信号**：/new、/reset、"先这样"、"下次再说"等
- **任务完成**：完成重要任务后立即记录
- **定期触发**：PCEC 周期（3 小时）

## 记录内容

### 1. 任务记录（memory/YYYY-MM-DD.md）

格式：
```
## [任务名称] - HH:MM
**任务**: [1-2 句描述]
**执行**:
- ✅/⚠️/❌ [结果]
- [关键产出: 文件/commit/数据]
**经验**: [可选，经验教训]
```

### 2. 重要经验（AIVectorMemory）

触发条件：可复用的经验教训 / 工具/API 的非预期行为 / 性能优化发现 / 新的最佳实践 / 跨系统集成关键配置

调用方式：
直接编辑 `shared-memory/pitfalls.md` 或 `shared-memory/services.md`，触发词写入对应文件。

## 存储位置

- **每日记忆**：`memory/YYYY-MM-DD.md`（追加，≤4KB）
- **长期记忆**：`MEMORY.md`（薄索引版）
- **向量记忆**：AIVectorMemory（智谱 Embedding-3）

## 自动化流程

### 会话结束时

1. 追加任务记录到 `memory/YYYY-MM-DD.md`
2. 重要经验 → aivectorMemory
3. 整理当日 memory（≤4KB）
4. 更新 MEMORY.md「上次会话摘要」
5. commit + push（失败则下次重试）

### 任务完成时

1. 触发检测（任务完成）
2. 立即追记任务记录
3. 如有重要经验 → aivectorMemory
4. 继续（不等会话结束）

### PCEC 周期

1. 触发检测（每 3 小时）
2. 回顾本周期内的任务
3. 提取可复用经验
4. 存入 aivectorMemory

## 记忆分域

| 域 | 用途 | 示例 |
|----|------|------|
| shared | 公共经验 | 飞书插件配置流程 |
| dev | 开发经验 | Next.js 16 部署坑 |
| content | 内容经验 | 公众号标题公式 |
| publish | 发布经验 | 小红书去水印技巧 |
