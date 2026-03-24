#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import urllib.parse
import urllib.request

BASE = "https://open.feishu.cn/open-apis/bitable/v1"
TOKEN = os.getenv("FEISHU_TENANT_ACCESS_TOKEN") or os.getenv("FEISHU_USER_ACCESS_TOKEN")


def eprint(*args):
    print(*args, file=sys.stderr)


def die(msg, code=1):
    eprint(msg)
    sys.exit(code)


def headers():
    if not TOKEN:
        die("错误: 请设置 FEISHU_TENANT_ACCESS_TOKEN 或 FEISHU_USER_ACCESS_TOKEN")
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json; charset=utf-8",
    }


def request(method, path, body=None, query=None):
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in headers().items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            out = json.loads(raw)
            if out.get("code") != 0:
                die(f"飞书 API 错误: {out.get('msg')}\n{raw}")
            return out.get("data", out)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        die(f"HTTP {e.code}: {raw}")


def load_json_arg(s):
    if os.path.isfile(s):
        with open(s, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(s)


def cmd_list_records(args):
    if len(args) < 2:
        die("用法: feishu-bitable.py list-records <app_token> <table_id> [page_size]")
    app_token, table_id = args[0], args[1]
    page_size = int(args[2]) if len(args) > 2 else 100
    page_token = None
    all_records = []
    while True:
        q = {"page_size": page_size}
        if page_token:
            q["page_token"] = page_token
        data = request("GET", f"/apps/{app_token}/tables/{table_id}/records", query=q)
        all_records.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
    print(json.dumps(all_records, ensure_ascii=False, indent=2))


def cmd_create_record(args):
    if len(args) < 3:
        die("用法: feishu-bitable.py create-record <app_token> <table_id> <fields_json|fields.json>")
    app_token, table_id = args[0], args[1]
    fields = load_json_arg(args[2])
    data = request("POST", f"/apps/{app_token}/tables/{table_id}/records", body={"fields": fields})
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_update_record(args):
    if len(args) < 4:
        die("用法: feishu-bitable.py update-record <app_token> <table_id> <record_id> <fields_json|fields.json>")
    app_token, table_id, record_id = args[0], args[1], args[2]
    fields = load_json_arg(args[3])
    data = request("PUT", f"/apps/{app_token}/tables/{table_id}/records/{record_id}", body={"fields": fields})
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_delete_record(args):
    if len(args) < 3:
        die("用法: feishu-bitable.py delete-record <app_token> <table_id> <record_id>")
    app_token, table_id, record_id = args[0], args[1], args[2]
    data = request("DELETE", f"/apps/{app_token}/tables/{table_id}/records/{record_id}")
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_batch_delete_records(args):
    if len(args) < 3:
        die("用法: feishu-bitable.py batch-delete-records <app_token> <table_id> <record_ids_json|record_ids.json>")
    app_token, table_id = args[0], args[1]
    record_ids = load_json_arg(args[2])
    if not isinstance(record_ids, list):
        die("record_ids 必须是 JSON 数组")
    if len(record_ids) > 500:
        die("一次最多删除 500 条记录")
    data = request("POST", f"/apps/{app_token}/tables/{table_id}/records/batch_delete", body={"records": record_ids})
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_create_field(args):
    if len(args) < 4:
        die("用法: feishu-bitable.py create-field <app_token> <table_id> <field_name> <type> [property_json]")
    app_token, table_id, field_name, field_type = args[0], args[1], args[2], int(args[3])
    body = {"field_name": field_name, "type": field_type}
    if len(args) > 4:
        body["property"] = load_json_arg(args[4])
    data = request("POST", f"/apps/{app_token}/tables/{table_id}/fields", body=body)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_create_duplex_link(args):
    if len(args) < 4:
        die("用法: feishu-bitable.py create-duplex-link <app_token> <table_id> <field_name> <target_table_id>")
    app_token, table_id, field_name, target_table_id = args[0], args[1], args[2], args[3]
    body = {
        "field_name": field_name,
        "type": 21,
        "property": {"table_id": target_table_id},
    }
    data = request("POST", f"/apps/{app_token}/tables/{table_id}/fields", body=body)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_help(_args):
    print("""feishu-bitable.py - 飞书多维表格 CLI

命令:
  list-records <app_token> <table_id> [page_size]
  create-record <app_token> <table_id> <fields_json|fields.json>
  update-record <app_token> <table_id> <record_id> <fields_json|fields.json>
  delete-record <app_token> <table_id> <record_id>
  batch-delete-records <app_token> <table_id> <record_ids_json|record_ids.json>
  create-field <app_token> <table_id> <field_name> <type> [property_json]
  create-duplex-link <app_token> <table_id> <field_name> <target_table_id>

示例:
  python3 feishu-bitable.py delete-record app_xxx tbl_xxx rec_xxx
  python3 feishu-bitable.py batch-delete-records app_xxx tbl_xxx '["rec1","rec2"]'
  python3 feishu-bitable.py create-duplex-link app_xxx tbl_src '关联提示词' tbl_target
""")


COMMANDS = {
    "help": cmd_help,
    "list-records": cmd_list_records,
    "create-record": cmd_create_record,
    "update-record": cmd_update_record,
    "delete-record": cmd_delete_record,
    "batch-delete-records": cmd_batch_delete_records,
    "create-field": cmd_create_field,
    "create-duplex-link": cmd_create_duplex_link,
}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        cmd_help([])
        sys.exit(0 if len(sys.argv) >= 2 and sys.argv[1] in {"help", "-h", "--help"} else 1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
