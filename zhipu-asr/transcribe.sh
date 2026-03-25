#!/bin/bash
# -*- coding: utf-8 -*-
#
# 智谱 ASR 转录脚本（聊天集成版）
# 用于 OpenClaw 音频自动转录，支持将识别结果直接发送到聊天
#

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZHIPU_ASR_PY="${SCRIPT_DIR}/zhipu_asr.py"
DEFAULT_MODEL="glm-asr-2512"
DEFAULT_HOTWORDS=""
MAX_RETRIES="${ZHIPU_MAX_RETRIES:-3}"
SEND_TO_CHAT="${SEND_TO_CHAT:-false}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"

# 颜色输出（如果支持）
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# 检查依赖
check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        log_error "python3 未安装，请先安装 Python 3"
        exit 1
    fi

    if ! command -v curl &> /dev/null; then
        log_error "curl 未安装"
        exit 1
    fi

    if [ ! -f "${ZHIPU_ASR_PY}" ]; then
        log_error "智谱 ASR 模块不存在: ${ZHIPU_ASR_PY}"
        exit 1
    fi
}

# 验证音频文件
validate_audio_file() {
    local audio_file="$1"

    if [ ! -f "${audio_file}" ]; then
        log_error "音频文件不存在: ${audio_file}"
        return 1
    fi

    # 检查文件扩展名
    local ext="${audio_file##*.}"
    if [[ ! "${ext,,}" =~ ^(wav|mp3|ogg|m4a)$ ]]; then
        log_warn "音频格式: .${ext}，可能不支持，尝试转换"
    fi

    # 检查文件大小（25MB）
    local file_size=$(stat -c%s "${audio_file}" 2>/dev/null || stat -f%z "${audio_file}" 2>/dev/null)
    local max_size=$((25 * 1024 * 1024))
    if [ "${file_size}" -gt "${max_size}" ]; then
        local size_mb=$((file_size / 1024 / 1024))
        log_error "音频文件过大: ${size_mb}MB，最大支持 25MB"
        return 1
    fi

    return 0
}

# 发送消息到 Telegram
send_to_telegram() {
    local text="$1"
    local chat_id="$2"
    local reply_to_message_id="$3"

    if [ -z "${TELEGRAM_BOT_TOKEN}" ]; then
        log_error "TELEGRAM_BOT_TOKEN 未设置，无法发送消息到聊天"
        return 1
    fi

    if [ -z "${chat_id}" ]; then
        log_error "chat_id 未提供"
        return 1
    fi

    # 构造 API 请求
    local api_url="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"

    # 使用 jq 进行 URL 编码（更可靠）
    if command -v jq &> /dev/null; then
        local encoded_text=$(echo -n "${text}" | jq -sRr @uri)
    else
        # 简单的 URL 编码（备用方案）
        local encoded_text=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''${text}'''))")
    fi

    # 构造请求 URL
    local request_url="${api_url}?chat_id=${chat_id}&text=${encoded_text}"

    if [ -n "${reply_to_message_id}" ]; then
        request_url="${request_url}&reply_to_message_id=${reply_to_message_id}"
    fi

    # 发送请求
    log_info "发送识别结果到聊天: ${chat_id}"
    local response=$(curl -s -X GET "${request_url}")

    # 检查响应
    if echo "${response}" | jq -e '.ok' > /dev/null 2>&1; then
        log_info "消息发送成功"
        return 0
    else
        log_error "消息发送失败: ${response}"
        return 1
    fi
}

# 执行转录
transcribe() {
    local audio_file="$1"
    local quiet_mode="$2"
    local hotwords="$3"

    local args=()
    args+=("${audio_file}")

    # 添加热词
    if [ -n "${hotwords}" ]; then
        args+=("--hotwords" "${hotwords}")
    elif [ -n "${DEFAULT_HOTWORDS}" ]; then
        args+=("--hotwords" "${DEFAULT_HOTWORDS}")
    fi

    # 安静模式
    if [ "${quiet_mode}" = "true" ]; then
        args+=("--quiet")
    fi

    # 执行 Python 脚本
    python3 "${ZHIPU_ASR_PY}" "${args[@]}"
}

# 主函数
main() {
    local audio_file=""
    local chat_id=""
    local message_id=""
    local quiet_mode="false"
    local hotwords=""

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quiet|-q)
                quiet_mode="true"
                shift
                ;;
            --hotwords)
                if [ -n "$2" ] && [[ ! "$2" =~ ^- ]]; then
                    hotwords="$2"
                    shift 2
                else
                    log_error "--hotwords 需要参数"
                    exit 1
                fi
                ;;
            --chat-id)
                if [ -n "$2" ] && [[ ! "$2" =~ ^- ]]; then
                    chat_id="$2"
                    shift 2
                else
                    log_error "--chat-id 需要参数"
                    exit 1
                fi
                ;;
            --message-id)
                if [ -n "$2" ] && [[ ! "$2" =~ ^- ]]; then
                    message_id="$2"
                    shift 2
                else
                    log_error "--message-id 需要参数"
                    exit 1
                fi
                ;;
            *)
                if [ -z "${audio_file}" ]; then
                    audio_file="$1"
                elif [ -z "${chat_id}" ]; then
                    chat_id="$1"
                elif [ -z "${message_id}" ]; then
                    message_id="$1"
                fi
                shift
                ;;
        esac
    done

    # 检查必需参数
    if [ -z "${audio_file}" ]; then
        log_error "缺少音频文件参数"
        echo "用法: $0 <audio_file> [chat_id] [message_id] [--quiet] [--hotwords \"word1,word2\"]" >&2
        exit 1
    fi

    # 检查依赖
    check_dependencies

    # 验证音频文件
    if ! validate_audio_file "${audio_file}"; then
        exit 1
    fi

    # 重试逻辑
    local retry=0
    local result=""
    local exit_code=0
    local recognized_text=""

    while [ ${retry} -lt ${MAX_RETRIES} ]; do
        if [ ${retry} -gt 0 ]; then
            log_warn "重试 (${retry}/${MAX_RETRIES})..."
            sleep 1
        fi

        # 执行转录
        if result=$(transcribe "${audio_file}" "true" "${hotwords}"); then
            exit_code=0
            recognized_text="${result}"
            break
        else
            exit_code=$?
            retry=$((retry + 1))
        fi
    done

    # 输出结果
    if [ ${exit_code} -eq 0 ]; then
        # 识别成功
        log_info "识别成功: ${recognized_text}"

        # 如果启用了发送到聊天
        if [ "${SEND_TO_CHAT}" = "true" ] && [ -n "${chat_id}" ]; then
            # 格式化识别文本
            local display_text="🎤 语音识别结果：\n\n${recognized_text}"

            # 发送到 Telegram
            if send_to_telegram "${display_text}" "${chat_id}" "${message_id}"; then
                log_info "识别结果已发送到聊天"
            else
                log_warn "发送失败，但识别成功"
            fi
        fi

        # 输出识别文本（用于 OpenClaw 处理）
        echo "${recognized_text}"
    else
        log_error "转录失败，已重试 ${MAX_RETRIES} 次"

        # 如果启用了发送到聊天，发送错误消息
        if [ "${SEND_TO_CHAT}" = "true" ] && [ -n "${chat_id}" ]; then
            send_to_telegram "❌ 语音识别失败，请重试" "${chat_id}" "${message_id}"
        fi

        exit 1
    fi

    exit ${exit_code}
}

# 运行主函数
main "$@"
