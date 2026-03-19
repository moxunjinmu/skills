# Get笔记 知识库维护工具

## 文件结构

```
getnote-knowledge/
├── SKILL.md          # 本文件 - 使用说明
├── README.md         # 快速参考
└── scripts/
    └── getnote_kb.py  # 主脚本
```

## 快速命令

```bash
# 查看知识库列表
python3 scripts/getnote_kb.py list

# 分析笔记分布（只读不写）
python3 scripts/getnote_kb.py analyze

# 全量拉取并分类（输出到 ~/.getnote_cats_*.txt）
python3 scripts/getnote_kb.py classify

# 批量加入知识库（ID列表文件每行一个note_id）
python3 scripts/getnote_kb.py add <knowledge_id> <note_ids_file>

# 新建知识库
python3 scripts/getnote_kb.py create "新库名"
```

## 凭证配置

脚本自动从 `~/.getnote_config.json` 读取，或从 `~/.openclaw/openclaw.json` 的 skills.entries.getnote 读取。

## 当前知识库

| ID | 名称 | 笔记数 |
|----|------|--------|
| eYzxQByJ | 公众号来源 | 0 |
| Q0GADwvn | B站来源 | 0 |
| rYMPABkn | 工作录音 | 0 |
| EJlAyMdn | 哲学思考 | 0 |

## 分类流程

1. `python3 getnote_kb.py classify` → 生成分类 ID 文件
2. 确认分类结果
3. `python3 getnote_kb.py add <kb_id> ~/.getnote_cats_公众号来源.txt`
