#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feishu Bitable CLI — 多维表格底层操作工具。

用法示例：
  python3 feishu-bitable.py list-records <app_token> <table_id> [--page-size N]
  python3 feishu-bitable.py create-record <app_token> <table_id> <fields.json>
  python3 feishu-bitable.py update-record <app_token> <table_id> <record_id> <fields.json>
  python3 feishu-bitable.py delete-record <app_token> <table_id> <record_id>
  python3 feishu-bitable.py batch-delete-records <app_token> <table_id> <record_ids.json>
  python3 feishu-bitable.py list-fields <app_token> <table_id>
  python3 feishu-bitable.py create-field <app_token> <table_id> <field_name> <type> [--property FILE]
  python3 feishu-bitable.py delete-field <app_token> <table_id> <field_id>
  python3 feishu-bitable.py create-duplex-link <app_token> <table_id> <field_name> <target_table_id> [--back-name NAME]
  python3 feishu-bitable.py cleanup-empty <app_token> <table_id> [--dry-run]
  python3 feishu-bitable.py field-types <app_token> <table_id>
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

BASE = "https://open.feishu.cn/open-apis/bitable/v1"
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
        print("No Feishu credentials found in openclaw.json", file=sys.stderr)
        sys.exit(1)
    # Get tenant access token
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
        method="POST"
    )
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        print(f"Token HTTP error {e.code}: {raw}", file=sys.stderr)
        sys.exit(1)
    if result.get("code") != 0:
        print(f"Token error: {result.get('msg')}", file=sys.stderr)
        sys.exit(1)
    return result["tenant_access_token"]


# ─── API 基础 ────────────────────────────────────────────────────────────────

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


def load_json_arg(s):
    """支持直接传 JSON 字符串或文件路径。"""
    if os.path.isfile(s):
        with open(s, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(s)


# ─── 命令 ────────────────────────────────────────────────────────────────────

def cmd_list_records(args):
    token = get_token()
    app_token, table_id = args.app_token, args.table_id
    all_records, page_token = [], None
    page_size = args.page_size or 100
    while True:
        q = {"page_size": min(page_size, 500)}
        if page_token:
            q["page_token"] = page_token
        data = api_req("GET", f"/apps/{app_token}/tables/{table_id}/records", token, params=q)
        all_records.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
    print(f"# 共 {len(all_records)} 条记录", file=sys.stderr)
    print(json.dumps(all_records, ensure_ascii=False, indent=2))


def cmd_create_record(args):
    token = get_token()
    fields = load_json_arg(args.fields)
    data = api_req("POST", f"/apps/{args.app_token}/tables/{args.table_id}/records",
                    token, {"fields": fields})
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_update_record(args):
    token = get_token()
    fields = load_json_arg(args.fields)
    data = api_req("PUT",
                    f"/apps/{args.app_token}/tables/{args.table_id}/records/{args.record_id}",
                    token, {"fields": fields})
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_delete_record(args):
    token = get_token()
    data = api_req("DELETE",
                    f"/apps/{args.app_token}/tables/{args.table_id}/records/{args.record_id}",
                    token)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_batch_delete_records(args):
    token = get_token()
    record_ids = load_json_arg(args.record_ids)
    if not isinstance(record_ids, list):
        print("record_ids 必须是 JSON 数组", file=sys.stderr)
        sys.exit(1)
    if len(record_ids) > 500:
        print("一次最多删除 500 条记录", file=sys.stderr)
        sys.exit(1)
    print(f"# 批量删除 {len(record_ids)} 条记录...", file=sys.stderr)
    data = api_req("POST",
                    f"/apps/{args.app_token}/tables/{args.table_id}/records/batch_delete",
                    token, {"records": record_ids})
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_list_fields(args):
    token = get_token()
    data = api_req("GET",
                    f"/apps/{args.app_token}/tables/{args.table_id}/fields",
                    token)
    items = data.get("items", [])
    print(f"# 共 {len(items)} 个字段", file=sys.stderr)
    print(json.dumps(items, ensure_ascii=False, indent=2))


def cmd_create_field(args):
    token = get_token()
    body = {"field_name": args.field_name, "type": args.type}
    if args.property:
        body["property"] = load_json_arg(args.property)
    data = api_req("POST",
                    f"/apps/{args.app_token}/tables/{args.table_id}/fields",
                    token, body)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_delete_field(args):
    token = get_token()
    data = api_req("DELETE",
                    f"/apps/{args.app_token}/tables/{args.table_id}/fields/{args.field_id}",
                    token)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_create_duplex_link(args):
    token = get_token()
    prop = {"table_id": args.target_table_id}
    if args.back_name:
        prop["back_field_name"] = args.back_name
    body = {"field_name": args.field_name, "type": 21, "property": prop}
    data = api_req("POST",
                    f"/apps/{args.app_token}/tables/{args.table_id}/fields",
                    token, body)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_cleanup_empty(args):
    """
    清理空白记录（所有文本字段均为空的记录）。
    支持 --dry-run：只报告，不删除。
    """
    token = get_token()
    app_token, table_id = args.app_token, args.table_id

    # Step 1: 拉所有字段，找出文本类字段（type=1）
    fields_data = api_req("GET", f"/apps/{app_token}/tables/{table_id}/fields", token)
    fields = fields_data.get("items", []) if fields_data else []
    text_field_ids = {f["field_id"] for f in fields if f.get("type") == 1}
    print(f"# 文本字段: {[f['field_name'] for f in fields if f['field_id'] in text_field_ids]}", file=sys.stderr)

    # Step 2: 拉所有记录
    all_records, page_token = [], None
    while True:
        q = {"page_size": 500}
        if page_token:
            q["page_token"] = page_token
        data = api_req("GET", f"/apps/{app_token}/tables/{table_id}/records", token, params=q)
        # 防御：API 返回 data 可能是 None
        data = data or {}
        all_records.extend(data.get("items") or [])
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")

    # Step 3: 找出空白记录
    empty_ids = []
    for rec in all_records:
        vals = rec.get("fields") or {}
        # 全部字段都是空的（或 None / 空列表）
        if all(v is None or v == "" or v == [] for v in vals.values()):
            empty_ids.append(rec["record_id"])

    print(f"# 发现 {len(empty_ids)} 条空白记录（/{len(all_records)} 总数）", file=sys.stderr)
    if not empty_ids:
        print("没有空白记录需要清理。")
        return

    if args.dry_run:
        print(f"# [DRY RUN] 将删除: {empty_ids}", file=sys.stderr)
        print(json.dumps(empty_ids, ensure_ascii=False, indent=2))
        return

    # Step 4: 批量删除（每批500）
    deleted = 0
    for i in range(0, len(empty_ids), 500):
        batch = empty_ids[i:i+500]
        api_req("POST",
                f"/apps/{app_token}/tables/{table_id}/records/batch_delete",
                token, {"records": batch})
        deleted += len(batch)
        print(f"# 已删除 {deleted}/{len(empty_ids)}...", file=sys.stderr)

    print(f"✅ 清理完成，共删除 {deleted} 条空白记录。")


def cmd_field_types(args):
    """列出每个字段的名称、ID 和类型（带中文解释）。"""
    token = get_token()
    data = api_req("GET", f"/apps/{args.app_token}/tables/{args.table_id}/fields", token)
    fields = data.get("items", [])

    TYPE_NAMES = {
        1: "文本", 2: "数字", 3: "单选", 4: "多选",
        5: "日期", 7: "复选框", 11: "用户", 13: "电话",
        15: "URL", 17: "附件", 18: "关联", 19: "查我",
        20: "公式", 21: "双向关联", 22: "地理位置",
        23: "群组", 1001: "创建时间", 1002: "修改时间",
        1003: "创建人", 1004: "修改人", 1005: "自动编号",
    }
    for f in fields:
        fid = f.get("field_id", "?")
        fname = f.get("field_name", "?")
        ftype = f.get("type", "?")
        tname = TYPE_NAMES.get(ftype, f"未知({ftype})")
        primary = " [主键]" if f.get("is_primary") else ""
        print(f"{fid}\t{ftype}\t{tname}{primary}\t{fname}")


# ─── 主入口 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="飞书多维表格（Bitable）CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers()

    # list-records
    p = sub.add_parser("list-records", help="列出表中所有记录（自动翻页）")
    p.add_argument("app_token")
    p.add_argument("table_id")
    p.add_argument("--page-size", type=int, dest="page_size")
    p.set_defaults(func=cmd_list_records)

    # create-record
    p = sub.add_parser("create-record", help="创建一条记录")
    p.add_argument("app_token")
    p.add_argument("table_id")
    p.add_argument("fields", help="字段 JSON 或 .json 文件路径")
    p.set_defaults(func=cmd_create_record)

    # update-record
    p = sub.add_parser("update-record", help="更新一条记录")
    p.add_argument("app_token")
    p.add_argument("table_id")
    p.add_argument("record_id")
    p.add_argument("fields", help="字段 JSON 或 .json 文件路径")
    p.set_defaults(func=cmd_update_record)

    # delete-record
    p = sub.add_parser("delete-record", help="删除一条记录")
    p.add_argument("app_token")
    p.add_argument("table_id")
    p.add_argument("record_id")
    p.set_defaults(func=cmd_delete_record)

    # batch-delete-records
    p = sub.add_parser("batch-delete-records", help="批量删除记录（最多500条/次）")
    p.add_argument("app_token")
    p.add_argument("table_id")
    p.add_argument("record_ids", help="record_id 数组 JSON 或 .json 文件路径")
    p.set_defaults(func=cmd_batch_delete_records)

    # list-fields
    p = sub.add_parser("list-fields", help="列出表中所有字段")
    p.add_argument("app_token")
    p.add_argument("table_id")
    p.set_defaults(func=cmd_list_fields)

    # create-field
    p = sub.add_parser("create-field", help="创建一个字段")
    p.add_argument("app_token")
    p.add_argument("table_id")
    p.add_argument("field_name")
    p.add_argument("type", type=int, help="字段类型 ID（1=文本, 3=单选, 4=多选, 5=日期, 21=双向关联…）")
    p.add_argument("--property", dest="property", help="字段 property JSON 或 .json 文件路径")
    p.set_defaults(func=cmd_create_field)

    # delete-field
    p = sub.add_parser("delete-field", help="删除一个字段")
    p.add_argument("app_token")
    p.add_argument("table_id")
    p.add_argument("field_id")
    p.set_defaults(func=cmd_delete_field)

    # create-duplex-link
    p = sub.add_parser("create-duplex-link", help="创建双向关联字段（DuplexLink）")
    p.add_argument("app_token")
    p.add_argument("table_id")
    p.add_argument("field_name")
    p.add_argument("target_table_id")
    p.add_argument("--back-name", dest="back_name", help="反向字段名")
    p.set_defaults(func=cmd_create_duplex_link)

    # cleanup-empty
    p = sub.add_parser("cleanup-empty", help="清理空白记录（所有文本字段为空的记录）")
    p.add_argument("app_token")
    p.add_argument("table_id")
    p.add_argument("--dry-run", action="store_true", dest="dry_run",
                   help="仅报告，不实际删除")
    p.set_defaults(func=cmd_cleanup_empty)

    # field-types
    p = sub.add_parser("field-types", help="列出字段类型（格式化表格视图）")
    p.add_argument("app_token")
    p.add_argument("table_id")
    p.set_defaults(func=cmd_field_types)

    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            args.func(args)
        except Exception as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
