---
name: getnote-knowledge
description: |
  Get笔记 知识库维护工具。

  ## 触发词
  「整理知识库」「批量归类」「维护笔记」「分类笔记」

  ## 工具脚本
  `~/.openclaw/skills/getnote-knowledge/scripts/getnote_kb.py`

  ## 凭证
  从 `~/.getnote_config.json` 或 `~/.openclaw/openclaw.json` 自动读取。

  ## 当前知识库

  | ID | 名称 | 用途 |
  |----|------|------|
  | eYzxQByJ | 公众号来源 | 微信公众号文章 |
  | Q0GADwvn | B站来源 | B站视频笔记 |
  | rYMPABkn | 工作录音 | 工作会议录音 |
  | EJlAyMdn | 哲学思考 | 个人哲学思考 |

  ## 完整操作流程

  ### 第一步：分析
  ```bash
  python3 ~/.openclaw/skills/getnote-knowledge/scripts/getnote_kb.py analyze
  ```

  ### 第二步：分类
  ```bash
  python3 ~/.openclaw/skills/getnote-knowledge/scripts/getnote_kb.py classify
  # 生成文件：~/.getnote_cats_公众号来源.txt 等
  ```

  ### 第三步：确认
  查看生成的 ID 文件内容，确认分类无误

  ### 第四步：批量加入
  ```bash
  python3 ~/.openclaw/skills/getnote-knowledge/scripts/getnote_kb.py add eYzxQByJ ~/.getnote_cats_公众号来源.txt
  python3 ~/.openclaw/skills/getnote-knowledge/scripts/getnote_kb.py add Q0GADwvn ~/.getnote_cats_B站来源.txt
  python3 ~/.openclaw/skills/getnote-knowledge/scripts/getnote_kb.py add rYMPABkn ~/.getnote_cats_工作录音.txt
  python3 ~/.openclaw/skills/getnote-knowledge/scripts/getnote_kb.py add EJlAyMdn ~/.getnote_cats_哲学思考.txt
  ```
