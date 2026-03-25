# 自动记忆绝对守则

违反此守则 = 记忆系统失效 = 重复犯错

---

## 🔴 绝对守则（不可违反）

### 1. 会话启动时必须检查

顺序（严格按此执行）：
1. 读取 `memory/YYYY-MM-DD.md`（今天的日记）
2. 读取 `MEMORY.md`「上次会话摘要」
3. 调用 `memory_search` 搜索相关主题
4. 然后才能回答用户

### 2. 任务完成时立即记录

触发条件：完成一个完整任务 / 做出重要决策 / 发现可复用经验 / 踩坑并找到解决方案

记录位置：`memory/YYYY-MM-DD.md`（追加）

### 3. 重要经验立即存入向量记忆

```bash
python3 scripts/memory-api.py remember "域" "内容" "标签"
```

### 4. 会话结束时必须总结

触发信号：/new、/reset、"先这样"、"下次再说"

必须执行：
1. 追加今日任务总结到 `memory/YYYY-MM-DD.md`
2. 更新 `MEMORY.md`「上次会话摘要」
3. 重要经验存入 aivectorMemory
4. git add + commit + push

---

## 执行检查清单

### 会话启动时（/new）

- [ ] 读取 `memory/YYYY-MM-DD.md`
- [ ] 读取 `MEMORY.md`「上次会话摘要」
- [ ] 调用 `memory_search` 搜索相关主题
- [ ] 然后才能回答用户

### 任务完成时

- [ ] 立即追记到 `memory/YYYY-MM-DD.md`
- [ ] 如有重要经验 → aivectorMemory
- [ ] 不等会话结束

### 会话结束时

- [ ] 追加今日任务总结
- [ ] 更新 `MEMORY.md`「上次会话摘要」
- [ ] 重要经验存入 aivectorMemory
- [ ] commit + push
