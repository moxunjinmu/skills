#!/usr/bin/env python3
"""
Get笔记 知识库管理脚本
用法:
  python3 getnote_kb.py list                    # 查看知识库
  python3 getnote_kb.py create <name>           # 新建知识库
  python3 getnote_kb.py classify                # 拉取全量笔记并分类
  python3 getnote_kb.py add <knowledge_id> <note_ids>  # 批量加入知识库
  python3 getnote_kb.py analyze                 # 分析笔记分布（不修改）
"""

import urllib.request
import urllib.error
import json
import time
import sys
import os
from collections import defaultdict

CONFIG_PATH = os.path.expanduser("~/.getnote_config.json")
API_BASE = "https://openapi.biji.com"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        # 尝试从 openclaw.json 读取
        openclaw_cfg = os.path.expanduser("~/.openclaw/openclaw.json")
        if os.path.exists(openclaw_cfg):
            with open(openclaw_cfg) as f:
                d = json.load(f)
            entries = d.get("skills", {}).get("entries", {})
            if "getnote" in entries:
                e = entries["getnote"]
                return {
                    "api_key": e.get("apiKey", ""),
                    "client_id": e.get("env", {}).get("GETNOTE_CLIENT_ID", "")
                }
        raise FileNotFoundError(f"请先配置 {CONFIG_PATH}")

    with open(CONFIG_PATH) as f:
        return json.load(f)


def api_headers(cfg):
    return {
        "Authorization": cfg["api_key"],
        "X-Client-ID": cfg["client_id"]
    }


def get(url, cfg):
    req = urllib.request.Request(url, headers=api_headers(cfg))
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()[:200]}", file=sys.stderr)
        return None


def post(url, cfg, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        **api_headers(cfg),
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()[:200]}", file=sys.stderr)
        return None


# ── 知识库操作 ──────────────────────────────────────────

def cmd_list(cfg):
    d = get(f"{API_BASE}/open/api/v1/resource/knowledge/list", cfg)
    if not d:
        return
    topics = d["data"]["topics"]
    print(f"知识库列表（共 {len(topics)} 个）：")
    for t in topics:
        s = t["stats"]
        print(f"  [{t['id']}] {t['name']}  笔记:{s['note_count']} 文件:{s['file_count']} 博主:{s['blogger_count']}")


def cmd_create(cfg, name, description=""):
    d = post(f"{API_BASE}/open/api/v1/resource/knowledge/create", cfg, {
        "name": name,
        "description": description
    })
    if d:
        t = d["data"]
        print(f"✅ 创建成功：{t['name']} (id={t['id']})")


# ── 笔记拉取 ──────────────────────────────────────────

def fetch_all_notes(cfg, delay=2.5):
    """拉取全量笔记，返回列表"""
    all_notes = []
    cursor = 0

    while True:
        url = f"{API_BASE}/open/api/v1/resource/note/list?since_id={cursor}"
        d = get(url, cfg)
        if not d:
            break

        notes = d["data"]["notes"]
        all_notes.extend(notes)
        print(f"  已获取 {len(all_notes)} 条...", flush=True)

        if not d["data"]["has_more"]:
            break
        cursor = d["data"]["next_cursor"]
        time.sleep(delay)

    return all_notes


def classify_notes(notes):
    """按来源分类笔记"""
    categories = {
        "公众号来源": [],
        "B站来源": [],
        "工作录音": [],
        "哲学思考": [],
        "其他": []
    }

    for n in notes:
        nid = str(n["id"])
        title = n.get("title", "")
        tags = [t["name"] for t in n.get("tags", [])]
        note_type = n.get("note_type", "")

        # 获取详情（URL信息）
        url = ""
        # 尝试从 content 中提取 URL
        content = n.get("content", "")
        if "mp.weixin.qq.com" in content or "weixin.qq.com" in content:
            url = "wechat"
        elif "bilibili.com" in content or "b23.tv" in content:
            url = "bilibili"
        elif "xiaohongshu.com" in content or "xhslink.com" in content:
            url = "red"

        # 分类判断
        if note_type == "meeting" or "录音" in title or "会议" in title:
            categories["工作录音"].append(nid)
        elif url == "wechat" or any("公众号" in t for t in tags):
            categories["公众号来源"].append(nid)
        elif url == "bilibili" or any("b站" in t.lower() or "bilibili" in t.lower() for t in tags):
            categories["B站来源"].append(nid)
        elif any(k in title for k in ["哲学", "思考", "反思", "世界观", "人生观", "生命", "存在", "意义"]):
            categories["哲学思考"].append(nid)
        else:
            categories["其他"].append(nid)

    return categories


def cmd_classify(cfg, delay=2.5):
    print("📡 开始拉取笔记（请耐心）...")
    notes = fetch_all_notes(cfg, delay)
    print(f"\n共获取 {len(notes)} 条笔记\n")

    cats = classify_notes(notes)
    for cat, ids in cats.items():
        print(f"  {cat}: {len(ids)} 条")
        if ids:
            # 保存到文件
            out_path = os.path.expanduser(f"~/.getnote_cats_{cat}.txt")
            with open(out_path, "w") as f:
                f.write("\n".join(ids))
            print(f"    → ID 已保存到 {out_path}")


def cmd_analyze(cfg, delay=2.5):
    """只分析不存储"""
    print("📡 拉取中...")
    notes = fetch_all_notes(cfg, delay)
    print(f"\n共 {len(notes)} 条笔记\n")

    from collections import Counter
    type_ctr = Counter()
    tag_ctr = Counter()

    for n in notes:
        type_ctr[n.get("note_type", "unknown")] += 1
        for t in n.get("tags", []):
            tag_ctr[t["name"]] += 1

    print("笔记类型分布：")
    for k, v in type_ctr.most_common():
        print(f"  {k}: {v}")

    print("\nTop 30 标签：")
    for t, c in tag_ctr.most_common(30):
        print(f"  {t}: {c}")

    cats = classify_notes(notes)
    print("\n分类预估：")
    for cat, ids in cats.items():
        print(f"  {cat}: {len(ids)} 条")


# ── 批量加入知识库 ──────────────────────────────────────

def cmd_add(cfg, knowledge_id, note_ids):
    """批量加入知识库，每批20条"""
    if isinstance(note_ids, str):
        # 如果是文件路径
        with open(os.path.expanduser(note_ids)) as f:
            note_ids = [l.strip() for l in f if l.strip()]

    total = len(note_ids)
    print(f"准备加入 {total} 条笔记到知识库 {knowledge_id}...")

    for i in range(0, total, 20):
        batch = note_ids[i:i+20]
        d = post(f"{API_BASE}/open/api/v1/resource/knowledge/note/batch-add", cfg, {
            "topic_id": knowledge_id,
            "note_ids": batch
        })
        if d and d.get("success"):
            print(f"  ✅ 批次 {i//20+1}: 加入 {len(batch)} 条")
        else:
            print(f"  ❌ 批次 {i//20+1} 失败: {d}")
        time.sleep(2)


# ── 主入口 ──────────────────────────────────────────

if __name__ == "__main__":
    cfg = load_config()

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        cmd_list(cfg)

    elif cmd == "create" and len(sys.argv) >= 3:
        name = sys.argv[2]
        desc = sys.argv[3] if len(sys.argv) >= 4 else ""
        cmd_create(cfg, name, desc)

    elif cmd == "classify":
        delay = float(sys.argv[2]) if len(sys.argv) >= 3 else 2.5
        cmd_classify(cfg, delay)

    elif cmd == "analyze":
        delay = float(sys.argv[2]) if len(sys.argv) >= 3 else 2.5
        cmd_analyze(cfg, delay)

    elif cmd == "add" and len(sys.argv) >= 4:
        kb_id = sys.argv[2]
        ids = sys.argv[3:]
        cmd_add(cfg, kb_id, ids)

    else:
        print(__doc__)
