#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feishu message tool: read, send, parse, stream, and chunk messages.

Usage:
  # 读取
  python3 feishu_message.py get <message_id>
  python3 feishu_message.py parse <message_id>
  python3 feishu_message.py chat-history <chat_id> [--start-time TS] [--end-time TS] [--limit N]

  # 发送
  python3 feishu_message.py send <chat_id> <text> [--chunk-size N]
  python3 feishu_message.py progress <chat_id> <step> <total> [--label TEXT]

  # 流式处理
  python3 feishu_message.py merge-streaming <prev_text> <next_text>
  python3 feishu_message.py deduplicate <file.json>

Examples:
  python3 feishu_message.py send oc1234abcd "第一段内容，太长会自动分块"
  python3 feishu_message.py progress oc1234abcd 2 5 --label "填写表单中"
  python3 feishu_message.py merge-streaming "上一段" "下一段"
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse

CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")

def api_req(method, url, token, data=None):
    """Make an API request using urllib"""
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

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
    result = api_req("POST",
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        "", {"app_id": app_id, "app_secret": app_secret})
    if result.get("code") != 0:
        print(f"Token error: {result.get('msg')}", file=sys.stderr)
        sys.exit(1)
    return result["tenant_access_token"]

def get_message(message_id):
    token = get_token()
    result = api_req("GET",
        f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}",
        token)
    if result.get("code") != 0:
        print(f"API error {result.get('code')}: {result.get('msg')}", file=sys.stderr)
        sys.exit(1)
    items = result.get("data", {}).get("items", [])
    return items[0] if items else {}

def extract_text(msg_type, content):
    if not content:
        return ""
    try:
        data = json.loads(content) if isinstance(content, str) else content
    except Exception:
        return content if isinstance(content, str) else ""
    if msg_type == "text":
        return data.get("text", "")
    elif msg_type == "post":
        parts = []
        for section in data.get("content", []):
            for item in section:
                if item.get("tag") == "text":
                    parts.append(item.get("text", ""))
        return " ".join(parts)
    elif msg_type == "interactive":
        return "[Interactive Card]"
    return content

def cmd_get(args):
    msg = get_message(args.message_id)
    if not msg:
        print("Message not found")
        sys.exit(1)
    msg_type = msg.get("msg_type", "")
    content = msg.get("body", {}).get("content", "")
    text = extract_text(msg_type, content)
    from datetime import datetime
    ts = int(msg.get("create_time", 0))
    t = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S") if ts else "?"
    sender = msg.get("sender", {}).get("id", "?")
    print(f"[{msg_type}] {t} | sender:{sender}")
    print(f"Content: {text[:500]}")
    if args.raw:
        print(json.dumps(msg, ensure_ascii=False, indent=2))

def cmd_parse(args):
    msg = get_message(args.message_id)
    if not msg:
        print("Message not found")
        sys.exit(1)
    msg_type = msg.get("msg_type", "")
    content = msg.get("body", {}).get("content", "")
    # Try card_parser
    try:
        cp = os.path.expanduser("~/.openclaw/workspace/skills/feishu-card-parser/scripts")
        sys.path.insert(0, cp)
        from card_parser import parse_card_message
        result = parse_card_message(content)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    except Exception:
        pass
    print(json.dumps({"msg_type": msg_type, "content": content,
                       "text": extract_text(msg_type, content)}, ensure_ascii=False, indent=2))

def cmd_chat_history(args):
    token = get_token()
    params = {
        "container_id": args.chat_id,
        "container_id_type": "chat",
        "page_size": min(args.limit, 50)
    }
    if args.start_time:
        params["start_time"] = str(args.start_time)
    if args.end_time:
        params["end_time"] = str(args.end_time)
    url = "https://open.feishu.cn/open-apis/im/v1/messages?" + urllib.parse.urlencode(params)
    result = api_req("GET", url, token)
    if result.get("code") != 0:
        print(f"API error {result.get('code')}: {result.get('msg')}", file=sys.stderr)
        sys.exit(1)
    items = result.get("data", {}).get("items", [])
    print(f"Got {len(items)} messages from {args.chat_id}")
    from datetime import datetime
    for msg in items:
        ts = int(msg.get("create_time", 0))
        t = datetime.fromtimestamp(ts / 1000).strftime("%m-%d %H:%M") if ts else "?"
        text = extract_text(msg.get("msg_type", ""), msg.get("body", {}).get("content", ""))
        print(f"[{t}] {msg.get('msg_type')} | {text[:120]}")
    has_more = result.get("data", {}).get("has_more")
    if has_more:
        print("(more — paginate with page_token)")

def send_message(chat_id, text, token):
    """Send a single text message to a chat."""
    payload = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}),
    }
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    result = api_req("POST", url, token, payload)
    if result.get("code") != 0:
        raise Exception(f"API error {result.get('code')}: {result.get('msg')}")
    return result.get("data", {}).get("message_id", "")


def chunk_text(text, size=1000):
    """
    Split text into chunks of approximately `size` chars.
    Strategy:
    1. Split on double newlines (paragraphs) first
    2. If a paragraph exceeds size, split on sentence endings
    3. If still too long, hard-cut at size
    4. Accumulate remaining paragraphs up to size
    """
    if not text:
        return []

    # Split into paragraphs
    paragraphs = re.split(r"\n\n+", text.strip())
    chunks, buf = [], ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_len = len(para)

        # Paragraph fits in one chunk and buffer has room
        if para_len <= size and (len(buf) + para_len + 1) <= size:
            buf = (buf + "\n" + para).strip()
            continue

        # Flush current buffer
        if buf:
            chunks.append(buf)
            buf = ""

        # Paragraph itself exceeds size — split by sentence, then hard-cut
        if para_len > size:
            # Split by common sentence endings
            parts = re.split(r"(?<=[。！？.!?\n])", para)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if len(part) <= size:
                    if (len(buf) + len(part) + 1) <= size:
                        buf = (buf + "\n" + part).strip()
                    else:
                        if buf:
                            chunks.append(buf)
                            buf = ""
                        # Still too big? hard cut
                        if len(part) > size:
                            for i in range(0, len(part), size):
                                sub = part[i : i + size].strip()
                                if sub:
                                    chunks.append(sub)
                        else:
                            buf = part
                else:
                    # No sentence boundary found — hard cut
                    for i in range(0, len(part), size):
                        sub = part[i : i + size].strip()
                        if sub:
                            chunks.append(sub)
        else:
            # Fits but buffer overflowed — start new buffer
            buf = para

    # Flush remaining
    if buf.strip():
        chunks.append(buf.strip())

    # Absolute fallback
    if not chunks and text.strip():
        for i in range(0, len(text.strip()), size):
            chunk = text.strip()[i : i + size]
            if chunk.strip():
                chunks.append(chunk.strip())

    return chunks


def cmd_send(args):
    token = get_token()
    text = args.text
    # If text is "-", read from stdin
    if text == "-":
        text = sys.stdin.read()

    if not text.strip():
        print("Nothing to send.", file=sys.stderr)
        sys.exit(1)

    size = args.chunk_size or 1000
    chunks = chunk_text(text, size)
    total = len(chunks)

    print(f"[feishu send] {total} chunk(s) to {args.chat_id}", file=sys.stderr)

    for i, chunk in enumerate(chunks, 1):
        try:
            msg_id = send_message(args.chat_id, chunk, token)
            print(f"[{i}/{total}] sent -> {msg_id}", file=sys.stderr)
            if i < total:
                time.sleep(0.3)  # brief pause between chunks
        except Exception as e:
            print(f"[{i}/{total}] FAILED: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Done. {total} message(s) sent.", file=sys.stderr)


def cmd_progress(args):
    """
    Send a progress indicator message.
    Format: [■□□□□] Step 2/5 — 填写表单中
    """
    token = get_token()
    step = args.step
    total = args.total
    label = args.label or f"Step {step}/{total}"

    # Build progress bar
    filled = "■" * step
    empty = "□" * (total - step)
    bar = f"[{filled}{empty}]"

    text = f"{bar} {label}"
    try:
        msg_id = send_message(args.chat_id, text, token)
        print(f"Progress sent: {msg_id}", file=sys.stderr)
    except Exception as e:
        print(f"Progress FAILED: {e}", file=sys.stderr)
        sys.exit(1)


# ─── 流式处理 ─────────────────────────────────────────────────────────────

def merge_streaming_text(previous_text, next_text):
    """
    合并两个流式文本块，处理重复问题。

    来源：m1heng/clawdbot-feishu streaming-card.ts mergeStreamingText

    常见情况：
    - next_text 完全包含 previous_text → 直接返回 next_text
    - previous_text 完全包含 next_text → 直接返回 previous_text
    - 两段有部分重叠（工具调用中常见）→ 去掉重叠部分后拼接
    - 两段完全不重叠 → 直接拼接

    最大重叠检测长度：500 字符（避免过高开销）
    """
    prev = previous_text or ""
    next = next_text or ""

    if not next:
        return prev
    if not prev or next == prev or next.startswith(prev):
        return next
    if prev.startswith(next):
        return prev

    # 找最大重叠后缀
    max_check = min(500, min(len(prev), len(next)))
    overlap = 0
    for i in range(1, max_check + 1):
        if prev[-i:] == next[:i]:
            overlap = i

    if overlap > 0:
        return prev + next[overlap:]
    return prev + next


def cmd_merge_streaming(args):
    """合并两个流式文本块，处理重复。"""
    result = merge_streaming_text(args.prev_text, args.next_text)
    print(result)


def cmd_deduplicate(args):
    """
    从流式日志 JSON 文件中还原去重后的完整文本。
    输入格式：每行一个 JSON 对象，含 prev_text / next_text 字段
    （用于处理 streaming card 的增量输出日志）
    """
    import json
    result = ""
    with open(args.file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                result = merge_streaming_text(result, obj.get("text", ""))
            except Exception:
                continue
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feishu message tool")
    sub = parser.add_subparsers()
    p = sub.add_parser("get", help="Get message by ID")
    p.add_argument("message_id")
    p.add_argument("--raw", action="store_true")
    p.set_defaults(func=cmd_get)
    p2 = sub.add_parser("parse", help="Get and parse message (uses card_parser)")
    p2.add_argument("message_id")
    p2.set_defaults(func=cmd_parse)
    p3 = sub.add_parser("chat-history", help="Get recent messages from chat")
    p3.add_argument("chat_id")
    p3.add_argument("--start-time", type=int)
    p3.add_argument("--end-time", type=int)
    p3.add_argument("--limit", type=int, default=20)
    p3.set_defaults(func=cmd_chat_history)
    p4 = sub.add_parser("send", help="Send text to chat (auto-chunked)")
    p4.add_argument("chat_id")
    p4.add_argument("text", help="'-' to read from stdin")
    p4.add_argument("--chunk-size", type=int, help="Max chars per chunk (default 1000)")
    p4.set_defaults(func=cmd_send)
    p5 = sub.add_parser("progress", help="Send a progress indicator message")
    p5.add_argument("chat_id")
    p5.add_argument("step", type=int)
    p5.add_argument("total", type=int)
    p5.add_argument("--label", type=str, help="Custom label text")
    p5.set_defaults(func=cmd_progress)
    p6 = sub.add_parser("merge-streaming", help="合并两个流式文本块，处理重复（来源：streaming-card.ts）")
    p6.add_argument("prev_text", help="上一段文本")
    p6.add_argument("next_text", help="下一段文本")
    p6.set_defaults(func=cmd_merge_streaming)
    p7 = sub.add_parser("deduplicate", help="从流式日志 JSON 文件还原去重后的完整文本")
    p7.add_argument("file", help="JSON 日志文件路径")
    p7.set_defaults(func=cmd_deduplicate)
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
