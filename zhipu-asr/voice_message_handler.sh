#!/bin/bash
# -*- coding: utf-8 -*-
#
# 语音消息处理包装脚本
# 从 OpenClaw 消息元数据中提取聊天信息
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRANSCRIBE_SCRIPT="${SCRIPT_DIR}/transcribe.sh"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# OpenClaw 传递的环境变量（如果有的话）
AUDIO_FILE="$1"
OPENCLAW_MESSAGE_ID="${OPENCLAW_MESSAGE_ID:-}"
OPENCLAW_CHANNEL="${OPENCLAW_CHANNEL:-}"
OPENCLAW_SENDER="${OPENCLAW_SENDER:-}"
OPENCLAW_CHAT_ID="${OPENCLAW_CHAT_ID:-}"

# 默认聊天 ID（可以从 Telegram 获取）
DEFAULT_CHAT_ID="${DEFAULT_CHAT_ID:-}"

# 如果没有 chat_id，尝试从其他变量推断
if [ -z "${OPENCLAW_CHAT_ID}" ]; then
    if [ -n "${OPENCLAW_SENDER}" ]; then
        OPENCLAW_CHAT_ID="${OPENCLAW_SENDER}"
    elif [ -n "${DEFAULT_CHAT_ID}" ]; then
        OPENCLAW_CHAT_ID="${DEFAULT_CHAT_ID}"
    else
        # 如果都没有，使用默认值（需要手动配置）
        OPENCLAW_CHAT_ID="${DEFAULT_CHAT_ID}"
    fi
fi

# 设置环境变量
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-8503419838:AAHxF3eOzDAJhIjhxxATCMekRXQ07h-SriY}"
export ZHIPU_API_KEY="${ZHIPU_API_KEY:-99279526ab6f413fb7ea838a344de8d4}"
export SEND_TO_CHAT="${SEND_TO_CHAT:-false}"

# 调试信息
echo -e "${GREEN}[INFO]${NC} 音频文件: ${AUDIO_FILE}" >&2
echo -e "${GREEN}[INFO]${NC} 聊天 ID: ${OPENCLAW_CHAT_ID}" >&2
echo -e "${GREEN}[INFO]${NC} 消息 ID: ${OPENCLAW_MESSAGE_ID}" >&2
echo -e "${GREEN}[INFO]${NC} 发送到聊天: ${SEND_TO_CHAT}" >&2

# 调用转录脚本
"${TRANSCRIBE_SCRIPT}" \
    "${AUDIO_FILE}" \
    "${OPENCLAW_CHAT_ID}" \
    "${OPENCLAW_MESSAGE_ID}"
