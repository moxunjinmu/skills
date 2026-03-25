#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feishu Permission CLI — 飞书权限与协作者管理工具。

用法示例：
  # 查询权限成员
  python3 feishu-perm.py list <token> <type>

  # 添加协作者
  python3 feishu-perm.py add <token> <type> <member_id> <member_type> <perm>
  # 示例：
  python3 feishu-perm.py add doc_xxx docx ou_xxx openid edit
  python3 feishu-perm.py add doc_xxx docx oc_xxx openchat view

  # 移除协作者
  python3 feishu-perm.py remove <token> <type> <member_id> <member_type>

  # 批量添加（从 JSON 文件）
  python3 feishu-perm.py batch-add <token> <type> <members.json>

token-type 选项：doc / docx / sheet / bitable / folder / file / wiki / mindnote
member-type 选项：openid / userid / unionid / email / openchat / opendepartmentid
perm 选项：view / edit / full_access

整合自：
  - m1heng/clawdbot-feishu (perm-tools/actions.ts)
  - wulaosiji/skills (feishu-doc-perm)
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

BASE = "https://open.feishu.cn/open-apis"
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
        f"{BASE}/auth/v3/tenant_access_token/internal",
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

def api_req(method, path, token, data=None, params=None):
    url = BASE + path
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


# ─── 校验 ────────────────────────────────────────────────────────────────────

TOKEN_TYPES = {"doc", "docx", "sheet", "bitable", "folder", "file", "wiki", "mindnote"}
MEMBER_TYPES = {"email", "openid", "userid", "unionid", "openchat", "opendepartmentid"}
PERM_LEVELS = {"view", "edit", "full_access"}


def validate_token_type(t):
    if t not in TOKEN_TYPES:
        raise ValueError(f"无效的 token type：{t}，可用值：{TOKEN_TYPES}")


def validate_member_type(t):
    if t not in MEMBER_TYPES:
        raise ValueError(f"无效的 member type：{t}，可用值：{MEMBER_TYPES}")


def validate_perm(p):
    if p not in PERM_LEVELS:
        raise ValueError(f"无效的权限级别：{p}，可用值：{PERM_LEVELS}")


# ─── 命令 ────────────────────────────────────────────────────────────────────

def cmd_list(args):
    """查询权限成员列表。"""
    token = get_token()
    validate_token_type(args.type)
    result = api_req("GET", f"/drive/v1/permissions/{args.token}/members", token,
                     params={"type": args.type})
    members = result.get("items", [])
    print(f"# 共 {len(members)} 个协作者", file=sys.stderr)
    for m in members:
        print(json.dumps({
            "member_type": m.get("member_type"),
            "member_id": m.get("member_id"),
            "perm": m.get("perm"),
            "name": m.get("name"),
        }, ensure_ascii=False, indent=2))


def cmd_add(args):
    """添加协作者。"""
    token = get_token()
    validate_token_type(args.type)
    validate_member_type(args.member_type)
    validate_perm(args.perm)
    result = api_req("POST", f"/drive/v1/permissions/{args.token}/members", token, {
        "member_type": args.member_type,
        "member_id": args.member_id,
        "perm": args.perm,
        "need_notification": False,
    })
    m = result.get("member", {})
    print(json.dumps({
        "success": True,
        "member_id": m.get("member_id"),
        "member_type": m.get("member_type"),
        "perm": m.get("perm"),
    }, ensure_ascii=False, indent=2))


def cmd_remove(args):
    """移除协作者。"""
    token = get_token()
    validate_token_type(args.type)
    validate_member_type(args.member_type)
    api_req("DELETE", f"/drive/v1/permissions/{args.token}/members/{args.member_id}", token,
            params={"type": args.type, "member_type": args.member_type})
    print(json.dumps({"success": True, "removed_member_id": args.member_id}, ensure_ascii=False, indent=2))


def load_members_arg(arg):
    """支持 JSON 字符串或 .json 文件路径。"""
    import os
    if os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(arg)


def cmd_batch_add(args):
    """批量添加协作者（从 JSON 数组）。"""
    token = get_token()
    validate_token_type(args.type)
    members = load_members_arg(args.members)
    if not isinstance(members, list):
        raise ValueError("members 必须是 JSON 数组")

    results = []
    for m in members:
        try:
            result = api_req("POST", f"/drive/v1/permissions/{args.token}/members", token, {
                "member_type": m["member_type"],
                "member_id": m["member_id"],
                "perm": m["perm"],
                "need_notification": False,
            })
            results.append({"success": True, **result.get("member", {})})
        except Exception as e:
            results.append({"success": False, "member_id": m.get("member_id"), "error": str(e)})

    success = sum(1 for r in results if r.get("success"))
    print(f"# 成功 {success}/{len(results)} 条", file=sys.stderr)
    print(json.dumps(results, ensure_ascii=False, indent=2))


# ─── 主入口 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="飞书权限与协作者管理 CLI",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers()

    p = sub.add_parser("list", help="查询权限成员列表")
    p.add_argument("token", help="文件/文档 token")
    p.add_argument("type", help="token 类型（doc/docx/sheet/bitable/folder/file/wiki/mindnote）")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("add", help="添加协作者")
    p.add_argument("token", help="文件/文档 token")
    p.add_argument("type", help="token 类型")
    p.add_argument("member_id", help="协作者 ID（open_id / user_id / chat_id 等）")
    p.add_argument("member_type", help="成员类型（openid/userid/unionid/email/openchat/opendepartmentid）")
    p.add_argument("perm", help="权限级别（view/edit/full_access）")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("remove", help="移除协作者")
    p.add_argument("token", help="文件/文档 token")
    p.add_argument("type", help="token 类型")
    p.add_argument("member_id", help="协作者 ID")
    p.add_argument("member_type", help="成员类型")
    p.set_defaults(func=cmd_remove)

    p = sub.add_parser("batch-add", help="批量添加协作者（JSON 数组）")
    p.add_argument("token", help="文件/文档 token")
    p.add_argument("type", help="token 类型")
    p.add_argument("members", help="协作者 JSON 数组或 .json 文件路径")
    p.set_defaults(func=cmd_batch_add)

    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            args.func(args)
        except Exception as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
