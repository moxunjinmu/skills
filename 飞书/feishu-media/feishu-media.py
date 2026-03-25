#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feishu Media CLI — 飞书媒体文件发送与下载工具。

用法示例：
  # 图片
  python3 feishu-media.py send-image <image_path> <target_id> [--type open_id|chat_id]

  # 视频（自动生成封面，发送播放器形式）
  python3 feishu-media.py send-video <video_path> <target_id> [--cover PATH] [--caption TEXT] [--type open_id|chat_id]

  # 语音（MP3转AMR，发送语音条形式）
  python3 feishu-media.py send-voice <audio_path> <target_id> [--type open_id|chat_id]

  # 文件（发送附件）
  python3 feishu-media.py send-file <file_path> <target_id> [--type open_id|chat_id]

  # 下载图片
  python3 feishu-media.py download-image <image_url_or_key> [--output PATH]

  # 下载消息附件
  python3 feishu-media.py download-resource <message_id> [--file-key KEY] [--output PATH]

整合自：
  - wulaosiji/skills（feishu-video-sender）
  - wulaosiji/skills（feishu-voice-sender）
  - m1heng/clawdbot-feishu（media.ts）
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
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
    except Exception:
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

def api_req(method, path, token, data=None, files=None, params=None):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    boundary = None
    body = None

    if files:
        # Multipart upload
        import uuid
        boundary = uuid.uuid4().hex
        parts = []
        # JSON data fields
        for k, v in (data or {}).items():
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}".encode()
            )
        # File fields
        for field_name, (filename, content, mime_type) in files.items():
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field_name}\"; filename=\"{filename}\"\r\n"
                f"Content-Type: {mime_type}\r\n\r\n".encode() + content
            )
        parts.append(f"--{boundary}--".encode())
        body = b"\r\n".join(parts)
        content_type = f"multipart/form-data; boundary={boundary}"
    elif data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        content_type = "application/json; charset=utf-8"
    else:
        content_type = "application/json; charset=utf-8"

    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            out = json.loads(raw)
            if out.get("code") != 0:
                raise Exception(f"API {out.get('code')}: {out.get('msg')}")
            return out.get("data", out)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise Exception(f"HTTP {e.code}: {raw}")


# ─── 通用上传 ────────────────────────────────────────────────────────────────

def upload_file(file_path, token, file_type):
    """上传任意文件，返回 file_key。"""
    filename = os.path.basename(file_path)
    # 探测 MIME 类型
    import mimetypes
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    with open(file_path, "rb") as f:
        content = f.read()

    result = api_req("POST", "/im/v1/files", token, data={
        "file_name": filename,
        "file_type": file_type,
    }, files={
        "file": (filename, content, mime_type)
    })
    return result.get("file_key", "")


def upload_image(image_path, token):
    """上传图片，返回 image_key。"""
    filename = os.path.basename(image_path)
    mime = "image/jpeg"
    with open(image_path, "rb") as f:
        content = f.read()
    result = api_req("POST", "/im/v1/images", token, data={"image_type": "message"}, files={
        "image": (filename, content, mime)
    })
    return result.get("image_key", "")


def upload_video(video_path, token):
    """上传视频，返回 file_key。"""
    filename = os.path.basename(video_path)
    with open(video_path, "rb") as f:
        content = f.read()
    result = api_req("POST", "/im/v1/files", token, data={
        "file_name": filename,
        "file_type": "mp4",
    }, files={
        "file": (filename, content, "video/mp4")
    })
    return result.get("file_key", "")


# ─── 视频封面 ────────────────────────────────────────────────────────────────

def generate_cover(video_path, output_path=None):
    """从视频第1秒画面生成封面图。"""
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".jpg")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-ss", "00:00:01",
        "-vframes", "1",
        output_path, "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"封面生成失败: {result.stderr}")
    return output_path


# ─── 语音转换 ───────────────────────────────────────────────────────────────

def convert_to_amr(mp3_path, amr_path=None):
    """将 MP3 转换为 AMR 格式（飞书语音格式）。"""
    if amr_path is None:
        amr_path = tempfile.mktemp(suffix=".amr")
    cmd = [
        "ffmpeg", "-i", mp3_path,
        "-ac", "1",           # 单声道
        "-ar", "8000",        # 8kHz
        "-ab", "12.2k",
        amr_path, "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"AMR 转换失败: {result.stderr}")
    return amr_path


# ─── 发送消息 ───────────────────────────────────────────────────────────────

def send_message(token, target_id, msg_type, content):
    """
    发送各类消息。
    msg_type: text / image / media / file / voice
    content: 格式因类型而异
    """
    payload = {
        "receive_id": target_id,
        "msg_type": msg_type,
        "content": json.dumps(content, ensure_ascii=False),
    }
    result = api_req("POST", "/im/v1/messages?receive_id_type=chat_id", token, payload)
    return result.get("message_id", "")


# ─── 命令 ────────────────────────────────────────────────────────────────────

def cmd_send_image(args):
    token = get_token()
    image_key = upload_image(args.image_path, token)
    msg_id = send_message(token, args.target_id, "image",
                         {"image_key": image_key})
    print(json.dumps({"success": True, "message_id": msg_id, "image_key": image_key}, ensure_ascii=False, indent=2))


def cmd_send_video(args):
    token = get_token()

    # 生成封面
    if args.cover:
        cover_path = args.cover
    else:
        cover_path = generate_cover(args.video_path)
        print(f"# 自动生成封面: {cover_path}", file=sys.stderr)

    # 上传
    file_key = upload_video(args.video_path, token)
    image_key = upload_image(cover_path, token)

    # 发送
    content = {
        "file_key": file_key,
        "image_key": image_key,
    }
    if args.caption:
        content["caption"] = args.caption

    msg_id = send_message(token, args.target_id, "media", content)
    print(json.dumps({
        "success": True, "message_id": msg_id,
        "file_key": file_key, "image_key": image_key
    }, ensure_ascii=False, indent=2))


def cmd_send_voice(args):
    token = get_token()

    # 转换为 AMR
    amr_path = convert_to_amr(args.audio_path)
    print(f"# 已转换为 AMR: {amr_path}", file=sys.stderr)

    # 上传 AMR
    filename = os.path.basename(amr_path)
    with open(amr_path, "rb") as f:
        content = f.read()
    result = api_req("POST", "/im/v1/files", token, data={
        "file_name": filename, "file_type": "opus"
    }, files={"file": (filename, content, "audio/amr")})
    file_key = result.get("file_key", "")

    # 发送语音
    msg_id = send_message(token, args.target_id, "voice", {"file_key": file_key})
    print(json.dumps({"success": True, "message_id": msg_id, "file_key": file_key}, ensure_ascii=False, indent=2))

    # 清理临时文件
    if not args.audio_path.endswith(".amr"):
        try:
            os.remove(amr_path)
        except Exception:
            pass


def cmd_send_file(args):
    token = get_token()
    file_type_map = {
        "pdf": "pdf", "doc": "doc", "docx": "docx",
        "xls": "xls", "xlsx": "xlsx", "ppt": "ppt", "pptx": "pptx",
        "txt": "txt", "zip": "zip", "mp3": "mp3", "mp4": "mp4",
    }
    ext = os.path.splitext(args.file_path)[1].lower().lstrip(".")
    file_type = file_type_map.get(ext, "streamfile")

    file_key = upload_file(args.file_path, token, file_type)
    content = {"file_key": file_key}
    msg_id = send_message(token, args.target_id, "file", content)
    print(json.dumps({"success": True, "message_id": msg_id, "file_key": file_key}, ensure_ascii=False, indent=2))


def cmd_download_image(args):
    token = get_token()
    image_key = args.image_url_or_key

    # 如果是 URL，先下载再上传获取 image_key
    if image_key.startswith("http"):
        import urllib.request as req2
        with req2.urlopen(image_key, timeout=30) as r:
            data = r.read()
        # 保存到临时文件
        suffix = ".jpg"
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            if ext in image_key.lower():
                suffix = ext
                break
        tmp_path = tempfile.mktemp(suffix=suffix)
        with open(tmp_path, "wb") as f:
            f.write(data)
        image_key = upload_image(tmp_path, token)
        os.remove(tmp_path)

    # 下载：直接用 image_key 构造 URL
    url = f"{BASE}/im/v1/images/{image_key}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except urllib.error.HTTPError:
        # 尝试下载消息中的图片资源
        print(f"# image_key 下载失败，尝试作为 resource 下载", file=sys.stderr)
        raise

    output = args.output or f"image_{image_key[:8]}.jpg"
    with open(output, "wb") as f:
        f.write(data)
    print(json.dumps({"success": True, "output": output, "size": len(data)}, ensure_ascii=False, indent=2))


def cmd_download_resource(args):
    """下载消息中的附件（图片/视频/文件）。"""
    token = get_token()
    message_id = args.message_id
    file_key = args.file_key  # 可选，消息内含 file_key 时使用

    # 获取消息内容拿到 file_key
    if not file_key:
        msg_data = api_req("GET", f"/im/v1/messages/{message_id}", token)
        body = msg_data.get("items", [{}])[0].get("body", {}).get("content", "{}")
        try:
            parsed = json.loads(body)
            file_key = parsed.get("file_key") or parsed.get("key")
        except Exception:
            raise Exception("无法从消息中提取 file_key，请用 --file-key 参数指定")

    # 下载
    url = f"{BASE}/im/v1/messages/{message_id}/resources/{file_key}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
        content_disposition = resp.headers.get("Content-Disposition", "")
        filename = "download"
        if "filename=" in content_disposition:
            import re
            m = re.search(r'filename="?([^";\n]+)', content_disposition)
            if m:
                filename = m.group(1)
                filename = urllib.parse.unquote(filename)

    output = args.output or filename
    with open(output, "wb") as f:
        f.write(data)
    print(json.dumps({"success": True, "output": output, "size": len(data)}, ensure_ascii=False, indent=2))


# ─── 主入口 ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="飞书媒体文件发送与下载 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers()

    p = sub.add_parser("send-image", help="发送图片消息")
    p.add_argument("image_path")
    p.add_argument("target_id")
    p.add_argument("--type", dest="msg_type", default="chat_id",
                   choices=["open_id", "chat_id"])
    p.set_defaults(func=cmd_send_image)

    p = sub.add_parser("send-video", help="发送视频（播放器形式）")
    p.add_argument("video_path")
    p.add_argument("target_id")
    p.add_argument("--cover", help="封面图路径（默认自动从视频第1秒生成）")
    p.add_argument("--caption", help="视频描述文案")
    p.add_argument("--type", dest="msg_type", default="chat_id",
                   choices=["open_id", "chat_id"])
    p.set_defaults(func=cmd_send_video)

    p = sub.add_parser("send-voice", help="发送语音（MP3转AMR，语音条形式）")
    p.add_argument("audio_path")
    p.add_argument("target_id")
    p.add_argument("--type", dest="msg_type", default="chat_id",
                   choices=["open_id", "chat_id"])
    p.set_defaults(func=cmd_send_voice)

    p = sub.add_parser("send-file", help="发送文件附件")
    p.add_argument("file_path")
    p.add_argument("target_id")
    p.add_argument("--type", dest="msg_type", default="chat_id",
                   choices=["open_id", "chat_id"])
    p.set_defaults(func=cmd_send_file)

    p = sub.add_parser("download-image", help="下载图片")
    p.add_argument("image_url_or_key", help="图片 URL 或 image_key")
    p.add_argument("--output", "-o", dest="output", help="保存路径")
    p.set_defaults(func=cmd_download_image)

    p = sub.add_parser("download-resource", help="下载消息附件")
    p.add_argument("message_id")
    p.add_argument("--file-key", dest="file_key", help="文件 key（可省略，从消息中自动提取）")
    p.add_argument("--output", "-o", dest="output", help="保存路径")
    p.set_defaults(func=cmd_download_resource)

    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            args.func(args)
        except Exception as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
