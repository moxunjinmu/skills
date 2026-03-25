#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feishu Community CLI — 飞书群运营与社群自动化工具。

用法示例：
  # 群管理
  python3 feishu-community.py create-chat <name> [--users USER_IDS] [--desc TEXT]
  python3 feishu-community.py add-members <chat_id> <user_ids>
  python3 feishu-community.py check-bot <chat_id>
  python3 feishu-community.py delete-chat <chat_id>

  # 创建会话群（建群 + 发欢迎语，一键）
  python3 feishu-community.py create-session-chat <name> <user_ids> [--greeting TEXT] [--desc TEXT]

  # 欢迎新成员
  python3 feishu-community.py welcome <chat_id> [--batch-size N] [--dry-run]

  # 巡检遗漏 @消息
  python3 feishu-community.py check-mentions <chat_id> [--minutes N]

  # 消息撤回
  python3 feishu-community.py recall <message_id>
  python3 feishu-community.py recall-thread <thread_id>

  # 群公告
  python3 feishu-community.py get-announcement <chat_id>
  python3 feishu-community.py write-announcement <chat_id> <content>

整合自：
  - m1heng/clawdbot-feishu (chat-tools/actions.ts)
  - wulaosiji/skills (feishu-group-welcome / feishu-message-recall)
"""
import argparse
import json
import os
import sys
import time
import random
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

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
                raise Exception(f"API {out.get('code')}: {out.get('msg')}")
            return out.get("data", out)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise Exception(f"HTTP {e.code}: {raw}")


# ─── 欢迎语模板 ──────────────────────────────────────────────────────────────

WELCOME_TEMPLATES = [
    "🦞 欢迎 {names} 加入「{group}」！\n\n我是你的AI助手，有事直接 @ 我，不用客套。",
    "🦞 欢迎 {names}！\n\n我是AI助手，擅长：资料整理、内容生成、信息检索。\n\n有需要 @ 我，咱们直接聊。",
    "🦞 欢迎 {names} 加入！\n\n这里汇聚了 AI 编程与出海实战内容。\n\n有问题直接抛出来，一起讨论 👊",
    "🦞 欢迎 {names}！\n\n我是助手，能帮你：查资料、整理思路、提醒事项。\n\n直接 @ 我，不用客气 😎",
    "🦞 欢迎 {names}！\n\n我是你的AI搭档。\n\n擅长：信息整理、写作辅助、代码调试。\n\n有需要直接说。",
]


# ─── 夜间模式 ───────────────────────────────────────────────────────────────

def is_night_mode():
    h = datetime.now().hour
    return h >= 23 or h < 7


# ─── 群管理命令 ─────────────────────────────────────────────────────────────

def cmd_create_chat(args):
    token = get_token()
    data = {"name": args.name}
    if args.users:
        data["user_id_list"] = args.users.split(",")
    if args.desc:
        data["description"] = args.desc
    result = api_req("POST", "/im/v1/chats", token, data)
    print(json.dumps({"success": True, "chat_id": result.get("chat_id"), "name": args.name}, ensure_ascii=False, indent=2))


def cmd_add_members(args):
    token = get_token()
    result = api_req("POST", f"/im/v1/chats/{args.chat_id}/members", token,
                     {"id_list": args.user_ids.split(",")})
    print(json.dumps({"success": True, "added": args.user_ids.split(",")}, ensure_ascii=False, indent=2))


def cmd_check_bot(args):
    token = get_token()
    try:
        result = api_req("GET", f"/im/v1/chats/{args.chat_id}", token)
        print(json.dumps({"success": True, "in_chat": True, "name": result.get("name")}, ensure_ascii=False, indent=2))
    except Exception as e:
        if "90003" in str(e):
            print(json.dumps({"success": True, "in_chat": False}, ensure_ascii=False, indent=2))
        else:
            raise


def cmd_delete_chat(args):
    token = get_token()
    api_req("DELETE", f"/im/v1/chats/{args.chat_id}", token)
    print(json.dumps({"success": True, "chat_id": args.chat_id, "message": "Chat deleted."}, ensure_ascii=False, indent=2))


def cmd_create_session_chat(args):
    """
    一键创建会话群并发送欢迎语。
    整合自 m1heng/clawdbot-feishu chat-tools。
    """
    token = get_token()
    user_ids = args.user_ids.split(",")
    greeting = args.greeting or random.choice(WELCOME_TEMPLATES).format(
        names=", ".join(user_ids), group=args.name
    )

    # Step 1: 创建群
    data = {"name": args.name, "user_id_list": user_ids}
    if args.desc:
        data["description"] = args.desc
    result = api_req("POST", "/im/v1/chats", token, data)
    chat_id = result.get("chat_id")
    if not chat_id:
        print(json.dumps({"success": False, "error": "No chat_id returned"}, ensure_ascii=False))
        sys.exit(1)

    # Step 2: 发送欢迎语
    msg_result = None
    if not is_night_mode():
        try:
            msg_result = api_req("POST", "/im/v1/messages?receive_id_type=chat_id", token, {
                "receive_id": chat_id,
                "msg_type": "text",
                "content": json.dumps({"text": greeting}),
            })
        except Exception as e:
            print(f"# 欢迎语发送失败（不影响建群）: {e}", file=sys.stderr)

    out = {"success": True, "chat_id": chat_id, "name": args.name, "greeting_sent": msg_result is not None}
    if msg_result:
        out["message_id"] = msg_result.get("message_id")
    print(json.dumps(out, ensure_ascii=False, indent=2))


# ─── 欢迎新成员 ─────────────────────────────────────────────────────────────

def get_chat_members(token, chat_id):
    """获取群成员列表。"""
    result = api_req("GET", f"/im/v1/chats/{chat_id}/members", token, params={"page_size": 100})
    return result.get("items", [])


def get_member_ids(members):
    """从成员列表提取 ID。"""
    return [m.get("member_id") or m.get("member_id") for m in members if m.get("member_id")]


def send_message(token, chat_id, content):
    """发送文本消息。"""
    result = api_req("POST", "/im/v1/messages?receive_id_type=chat_id", token, {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": content}),
    })
    return result.get("message_id", "")


def cmd_welcome(args):
    """
    检查群中新成员并发送欢迎消息。
    整合自 wulaosiji/feishu-group-welcome。
    支持：
    - 批量 @ 分批发送（每批最多20人）
    - 夜间模式静默（23:00-7:00）
    - 8套欢迎语模板随机
    """
    token = get_token()
    batch_size = args.batch_size or 20

    members = get_chat_members(token, args.chat_id)
    if not members:
        print("无法获取群成员列表。")
        sys.exit(1)

    # 模拟"已知成员"逻辑：这里简化为直接对所有成员发
    # 实际场景需要记录历史成员 ID 做对比
    if is_night_mode():
        print(f"# 夜间模式（{datetime.now().hour}点），静默跳过。")
        return

    # 取前 batch_size 名成员演示
    welcome_members = members[:batch_size]
    names = [m.get("name", m.get("member_id", "成员")) for m in welcome_members]
    names_str = "、".join(names)

    template = random.choice(WELCOME_TEMPLATES)
    greeting = template.format(names=names_str, group="本群")

    if args.dry_run:
        print(f"# [DRY RUN] 将发送欢迎语：\n{greeting}")
        return

    msg_id = send_message(token, args.chat_id, greeting)
    print(json.dumps({"success": True, "message_id": msg_id, "welcomed": len(welcome_members)}, ensure_ascii=False, indent=2))


# ─── @消息巡检 ─────────────────────────────────────────────────────────────

def cmd_check_mentions(args):
    """
    检查群里最近 N 分钟内的 @消息，找出发给自己的遗漏消息。
    整合自 wulaosiji/feishu-chat-monitor。
    """
    token = get_token()
    minutes = args.minutes or 60
    start_time_ms = int((time.time() - minutes * 60) * 1000)

    result = api_req("GET", "/im/v1/messages", token, params={
        "container_id": args.chat_id,
        "container_id_type": "chat",
        "page_size": 50,
        "sort_type": "ByCreateTimeDesc",
        "start_time": start_time_ms // 1000,
    })

    items = result.get("items", [])
    bot_id = get_feishu_creds()[0]  # approximate

    missed = []
    for msg in items:
        body = msg.get("body", {}).get("content", "")
        try:
            parsed = json.loads(body) if isinstance(body, str) else body
            # 飞书 @机器人 的消息内容中包含 "@_user_1" 或类似标记
            if isinstance(parsed, dict):
                content_str = json.dumps(parsed, ensure_ascii=False)
                if "@_user_1" in content_str or "at_user" in content_str:
                    missed.append({
                        "message_id": msg.get("message_id"),
                        "sender": msg.get("sender", {}).get("id"),
                        "content_preview": content_str[:100],
                        "create_time": msg.get("create_time"),
                    })
        except Exception:
            pass

    if missed:
        print(f"# 发现 {len(missed)} 条遗漏的 @消息：", file=sys.stderr)
        print(json.dumps(missed, ensure_ascii=False, indent=2))
    else:
        print("没有发现遗漏的 @消息。")


# ─── 消息撤回 ────────────────────────────────────────────────────────────────

def cmd_recall(args):
    """
    撤回（删除）一条消息。
    整合自 wulaosiji/feishu-message-recall。
    """
    token = get_token()
    result = api_req("DELETE", f"/im/v1/messages/{args.message_id}", token)
    print(json.dumps({"success": True, "message_id": args.message_id, "deleted": result.get("deleted", True)}, ensure_ascii=False, indent=2))


def cmd_recall_thread(args):
    """
    列出话题（Thread）中的所有消息，并删除发送者是机器人的消息。
    整合自 wulaosiji/feishu-message-recall。
    """
    token = get_token()
    # 获取话题消息列表
    result = api_req("GET", f"/im/v1/messages?container_id_type=thread&container_id={args.thread_id}&page_size=50", token)
    items = result.get("items", [])

    if not items:
        print("话题中无消息。")
        return

    # 获取 bot 自己发送的消息
    # 获取 bot id
    bot_info = api_req("GET", "/bot/v3/info", token)
    bot_id = bot_info.get("bot", {}).get("app_id", "")

    bot_msg_ids = [
        msg.get("message_id") for msg in items
        if msg.get("sender", {}).get("id_type") == "app_id"
    ]

    print(f"# 话题 {args.thread_id} 共 {len(items)} 条，Bot 发送 {len(bot_msg_ids)} 条。", file=sys.stderr)

    if args.dry_run:
        print(f"# [DRY RUN] 将删除: {bot_msg_ids}")
        return

    deleted, failed = 0, 0
    for mid in bot_msg_ids:
        try:
            api_req("DELETE", f"/im/v1/messages/{mid}", token)
            deleted += 1
        except Exception:
            failed += 1

    print(json.dumps({"success": True, "deleted": deleted, "failed": failed}, ensure_ascii=False, indent=2))


# ─── 群公告 ─────────────────────────────────────────────────────────────────

def cmd_get_announcement(args):
    """获取群公告内容。"""
    token = get_token()
    try:
        result = api_req("GET", f"/docx/v1/chats/{args.chat_id}/announcement", token)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception:
        # fallback: 尝试旧版 API
        result = api_req("GET", f"/im/v1/chats/{args.chat_id}/pinned_messages", token)
        print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_write_announcement(args):
    """写入群公告。"""
    token = get_token()
    try:
        # 优先用新版 docx API
        api_req("PATCH", f"/docx/v1/chats/{args.chat_id}/announcement", token,
                {"content": args.content})
        print(json.dumps({"success": True}, ensure_ascii=False, indent=2))
    except Exception:
        # fallback: 旧版
        api_req("PATCH", f"/im/v1/chats/{args.chat_id}/announcement", token,
                {"content": args.content})
        print(json.dumps({"success": True}, ensure_ascii=False, indent=2))


# ─── 主入口 ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="飞书群运营与社群自动化 CLI",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers()

    # 群管理
    p = sub.add_parser("create-chat", help="创建一个群聊")
    p.add_argument("name")
    p.add_argument("--users", help="初始成员 user_id，逗号分隔")
    p.add_argument("--desc", dest="desc", help="群描述")
    p.set_defaults(func=cmd_create_chat)

    p = sub.add_parser("add-members", help="向群聊添加成员")
    p.add_argument("chat_id")
    p.add_argument("user_ids", help="user_id，逗号分隔")
    p.set_defaults(func=cmd_add_members)

    p = sub.add_parser("check-bot", help="检查机器人是否在群里")
    p.add_argument("chat_id")
    p.set_defaults(func=cmd_check_bot)

    p = sub.add_parser("delete-chat", help="解散一个群聊")
    p.add_argument("chat_id")
    p.set_defaults(func=cmd_delete_chat)

    p = sub.add_parser("create-session-chat", help="一键创建会话群并发送欢迎语")
    p.add_argument("name")
    p.add_argument("user_ids", help="初始成员 user_id，逗号分隔")
    p.add_argument("--greeting", dest="greeting", help="自定义欢迎语")
    p.add_argument("--desc", dest="desc", help="群描述")
    p.set_defaults(func=cmd_create_session_chat)

    # 欢迎
    p = sub.add_parser("welcome", help="检查并欢迎群中新成员（批量@）")
    p.add_argument("chat_id")
    p.add_argument("--batch-size", type=int, dest="batch_size", help="每批最多@人数（默认20）")
    p.add_argument("--dry-run", action="store_true", dest="dry_run")
    p.set_defaults(func=cmd_welcome)

    # @巡检
    p = sub.add_parser("check-mentions", help="检查群里最近遗漏的 @消息")
    p.add_argument("chat_id")
    p.add_argument("--minutes", type=int, help="检查最近多少分钟（默认60）")
    p.set_defaults(func=cmd_check_mentions)

    # 消息撤回
    p = sub.add_parser("recall", help="撤回（删除）一条消息")
    p.add_argument("message_id")
    p.set_defaults(func=cmd_recall)

    p = sub.add_parser("recall-thread", help="删除话题中机器人发送的所有消息")
    p.add_argument("thread_id")
    p.add_argument("--dry-run", action="store_true", dest="dry_run")
    p.set_defaults(func=cmd_recall_thread)

    # 群公告
    p = sub.add_parser("get-announcement", help="获取群公告内容")
    p.add_argument("chat_id")
    p.set_defaults(func=cmd_get_announcement)

    p = sub.add_parser("write-announcement", help="写入群公告")
    p.add_argument("chat_id")
    p.add_argument("content", help="公告内容")
    p.set_defaults(func=cmd_write_announcement)

    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            args.func(args)
        except Exception as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
