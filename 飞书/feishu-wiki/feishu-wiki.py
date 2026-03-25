#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feishu Wiki CLI — 飞书知识库操作工具。

用法示例：
  python3 feishu-wiki.py list-spaces
  python3 feishu-wiki.py list-nodes <space_id> [--parent NODE_TOKEN]
  python3 feishu-wiki.py search <keyword>
  python3 feishu-wiki.py get-node <node_token>
  python3 feishu-wiki.py create-node <space_id> <title> [--parent NODE_TOKEN] [--obj-type TYPE] [--obj-token TOKEN]
  python3 feishu-wiki.py rename-node <space_id> <node_token> <new_title>
  python3 feishu-wiki.py move-node <space_id> <node_token> [--target-space SPACE_ID] [--target-parent NODE_TOKEN]
  python3 feishu-wiki.py delete-node <space_id> <node_token>
  python3 feishu-wiki.py node-path <node_token>
  python3 feishu-wiki.py attach-docs <space_id> <parent_node_token> <doc_token>...
  python3 feishu-wiki.py space-tree <space_id> [--depth N]

obj-type 选项：docx(默认) / sheet / bitable / mindnote / file / doc / slides
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

WIKI_BASE = "https://open.feishu.cn/open-apis/wiki/v2"
DOC_BASE  = "https://open.feishu.cn/open-apis/docx/v1"
CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")


# ─── 凭证 ────────────────────────────────────────────────────────────────────

def get_feishu_creds():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        feishu = cfg.get("channels", {}).get("feishu", {})
        accounts = feishu.get("accounts", {})
        main = accounts.get("main", accounts.get("default", {}))
        return main.get("appId") or feishu.get("appId"), main.get("appSecret") or feishu.get("appSecret")
    except Exception as e:
        print(f"Config read error: {e}", file=sys.stderr)
        return None, None


def get_token():
    app_id, app_secret = get_feishu_creds()
    if not app_id or not app_secret:
        print("No Feishu credentials", file=sys.stderr)
        sys.exit(1)
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
        method="POST"
    )
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
    if result.get("code") != 0:
        print(f"Token error: {result.get('msg')}", file=sys.stderr)
        sys.exit(1)
    return result["tenant_access_token"]


# ─── API ─────────────────────────────────────────────────────────────────────

def api_req(method, url, token, data=None, params=None):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            out = json.loads(raw)
            if out.get("code") != 0:
                raise Exception(f"API {out.get('code')}: {out.get('msg')}\n{raw}")
            return out.get("data", out)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise Exception(f"HTTP {e.code}: {raw}")


# ─── 命令 ────────────────────────────────────────────────────────────────────

def cmd_list_spaces(_args):
    token = get_token()
    data = api_req("GET", f"{WIKI_BASE}/spaces", token)
    spaces = data.get("spaces", [])
    print(f"# 共 {len(spaces)} 个知识库空间", file=sys.stderr)
    for s in spaces:
        print(f"{s.get('space_id')}\t{s.get('name')}\t{'wiki' if s.get('node_type')==1 else 'folder'}")


def cmd_list_nodes(args):
    token = get_token()
    params = {"page_size": 50}
    if args.parent:
        params["parent_node_token"] = args.parent
    data = api_req("GET", f"{WIKI_BASE}/spaces/{args.space_id}/nodes", token, params=params)
    nodes = data.get("items", [])
    print(f"# 共 {len(nodes)} 个节点", file=sys.stderr)
    for n in nodes:
        obj_type = n.get("obj_type", "?")
        token_ = n.get("node_token", "?")
        title = n.get("title", "?")
        print(f"{token_}\t{obj_type}\t{title}")


def cmd_search(args):
    """在所有知识库空间中搜索节点（按标题）。"""
    token = get_token()
    # 先列出所有空间，再在每个空间搜索
    spaces_data = api_req("GET", f"{WIKI_BASE}/spaces", token)
    spaces = spaces_data.get("spaces", [])
    results = []
    for space in spaces:
        sid = space.get("space_id")
        try:
            # 尝试获取根节点，在其下搜索
            params = {"page_size": 50, "token": args.keyword}
            nodes_data = api_req("GET", f"{WIKI_BASE}/spaces/{sid}/nodes", token, params=params)
            for n in nodes_data.get("items", []):
                if args.keyword.lower() in n.get("title", "").lower():
                    results.append((space.get("name"), n))
        except Exception:
            pass

    if not results:
        print("未找到匹配结果。")
        return

    print(f"# 找到 {len(results)} 个匹配节点：", file=sys.stderr)
    for space_name, node in results:
        print(f"[{space_name}]\t{node.get('node_token')}\t{node.get('obj_type')}\t{node.get('title')}")


def cmd_get_node(args):
    token = get_token()
    data = api_req("GET", f"{WIKI_BASE}/nodes/{args.node_token}", token)
    n = data if isinstance(data, dict) else {}
    print(json.dumps({
        "node_token": n.get("node_token"),
        "parent_node_token": n.get("parent_node_token"),
        "space_id": n.get("space_id"),
        "obj_token": n.get("obj_token"),
        "obj_type": n.get("obj_type"),
        "title": n.get("title"),
    }, ensure_ascii=False, indent=2))


def cmd_create_node(args):
    token = get_token()
    body = {"title": args.title}
    if args.parent:
        body["parent_node_token"] = args.parent
    if args.obj_type and args.obj_type != "docx":
        body["obj_type"] = args.obj_type
    if args.obj_token:
        body["obj_token"] = args.obj_token
    data = api_req("POST", f"{WIKI_BASE}/spaces/{args.space_id}/nodes", token, body)
    n = data.get("node", {})
    print(json.dumps({"node_token": n.get("node_token"), "obj_token": n.get("obj_token"), "title": n.get("title")}, ensure_ascii=False, indent=2))


def cmd_rename_node(args):
    token = get_token()
    data = api_req("PATCH", f"{WIKI_BASE}/spaces/{args.space_id}/nodes/{args.node_token}", token,
                    {"title": args.new_title})
    n = data.get("node", {})
    print(json.dumps({"node_token": n.get("node_token"), "title": n.get("title")}, ensure_ascii=False, indent=2))


def cmd_move_node(args):
    token = get_token()
    body = {}
    if args.target_space:
        body["target_space_id"] = args.target_space
    if args.target_parent:
        body["target_parent_node_token"] = args.target_parent
    data = api_req("POST", f"{WIKI_BASE}/spaces/{args.space_id}/nodes/{args.node_token}/move", token, body)
    n = data.get("node", {})
    print(json.dumps({"node_token": n.get("node_token"), "title": n.get("title")}, ensure_ascii=False, indent=2))


def cmd_delete_node(args):
    token = get_token()
    api_req("DELETE", f"{WIKI_BASE}/spaces/{args.space_id}/nodes/{args.node_token}", token)
    print(f"✅ 节点 {args.node_token} 已删除。")


def cmd_node_path(args):
    """获取节点的完整祖先路径（breadcrumb）。"""
    token = get_token()
    # 飞书 wiki API 不直接提供 ancestors 接口，逐级向上爬
    path = []
    current = args.node_token
    visited = set()
    while current and current not in visited:
        visited.add(current)
        try:
            data = api_req("GET", f"{WIKI_BASE}/nodes/{current}", token)
            title = data.get("title", "?")
            obj_type = data.get("obj_type", "?")
            path.append((current, title, obj_type))
            parent = data.get("parent_node_token")
            if not parent or parent == current:
                break
            current = parent
        except Exception:
            break

    path.reverse()
    print(f"# 路径（共 {len(path)} 层）：", file=sys.stderr)
    for i, (nt, title, ot) in enumerate(path):
        indent = "  " * i
        print(f"{indent}{nt} [{ot}] {title}")


def cmd_attach_docs(args):
    """将已有文档（doc）批量挂入知识库指定节点下（创建 wiki 节点引用）。"""
    token = get_token()
    created = []
    for doc_token in args.doc_tokens:
        try:
            body = {
                "obj_type": "docx",
                "obj_token": doc_token,
                "parent_node_token": args.parent_node_token,
            }
            data = api_req("POST", f"{WIKI_BASE}/spaces/{args.space_id}/nodes", token, body)
            n = data.get("node", {})
            print(f"✅ {n.get('node_token')} <- {doc_token} ({n.get('title', '')})", file=sys.stderr)
            created.append({"node_token": n.get("node_token"), "obj_token": doc_token})
        except Exception as e:
            print(f"❌ {doc_token}: {e}", file=sys.stderr)
    print(json.dumps(created, ensure_ascii=False, indent=2))


def cmd_space_tree(args):
    """递归打印知识库空间目录树（最大 depth 层）。"""
    token = get_token()
    max_depth = args.depth or 99

    def print_tree(parent_token, indent):
        if indent > max_depth:
            return
        params = {"page_size": 50}
        if parent_token:
            params["parent_node_token"] = parent_token
        try:
            data = api_req("GET", f"{WIKI_BASE}/spaces/{args.space_id}/nodes", token, params=params)
        except Exception as e:
            print(f"{'  '*indent}❌ {e}")
            return
        for n in data.get("items", []):
            nt = n.get("node_token", "?")
            title = n.get("title", "?")
            obj_type = n.get("obj_type", "?")
            print(f"{'  '*indent}{nt} [{obj_type}] {title}")
            print_tree(nt, indent + 1)

    print(f"# 知识库空间: {args.space_id}", file=sys.stderr)
    print_tree(None, 0)


# ─── 主入口 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="飞书知识库（Wiki）CLI",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers()

    p = sub.add_parser("list-spaces", help="列出所有知识库空间")
    p.set_defaults(func=cmd_list_spaces)

    p = sub.add_parser("list-nodes", help="列出空间下的节点")
    p.add_argument("space_id")
    p.add_argument("--parent", dest="parent")
    p.set_defaults(func=cmd_list_nodes)

    p = sub.add_parser("search", help="在所有知识库中按标题搜索节点")
    p.add_argument("keyword")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("get-node", help="获取节点详情")
    p.add_argument("node_token")
    p.set_defaults(func=cmd_get_node)

    p = sub.add_parser("create-node", help="在知识库中创建节点")
    p.add_argument("space_id")
    p.add_argument("title")
    p.add_argument("--parent")
    p.add_argument("--obj-type", dest="obj_type")
    p.add_argument("--obj-token", dest="obj_token")
    p.set_defaults(func=cmd_create_node)

    p = sub.add_parser("rename-node", help="重命名节点")
    p.add_argument("space_id")
    p.add_argument("node_token")
    p.add_argument("new_title")
    p.set_defaults(func=cmd_rename_node)

    p = sub.add_parser("move-node", help="移动节点到其他位置")
    p.add_argument("space_id")
    p.add_argument("node_token")
    p.add_argument("--target-space", dest="target_space")
    p.add_argument("--target-parent", dest="target_parent")
    p.set_defaults(func=cmd_move_node)

    p = sub.add_parser("delete-node", help="删除节点")
    p.add_argument("space_id")
    p.add_argument("node_token")
    p.set_defaults(func=cmd_delete_node)

    p = sub.add_parser("node-path", help="获取节点的祖先路径（breadcrumb）")
    p.add_argument("node_token")
    p.set_defaults(func=cmd_node_path)

    p = sub.add_parser("attach-docs", help="批量将已有文档挂入知识库节点下")
    p.add_argument("space_id")
    p.add_argument("parent_node_token")
    p.add_argument("doc_tokens", nargs="+")
    p.set_defaults(func=cmd_attach_docs)

    p = sub.add_parser("space-tree", help="递归打印知识库目录树")
    p.add_argument("space_id")
    p.add_argument("--depth", type=int)
    p.set_defaults(func=cmd_space_tree)

    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            args.func(args)
        except Exception as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
