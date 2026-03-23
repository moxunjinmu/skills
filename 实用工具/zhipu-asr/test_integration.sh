#!/bin/bash
# -*- coding: utf-8 -*-
#
# 集成测试脚本
# 测试智谱 ASR 聊天集成功能
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRANSCRIBE_SCRIPT="${SCRIPT_DIR}/transcribe.sh"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}智谱 ASR 聊天集成测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 测试计数
PASSED=0
FAILED=0

# 测试函数
test_case() {
    local name="$1"
    local command="$2"

    echo -e "${BLUE}测试:${NC} ${name}"
    if eval "${command}"; then
        echo -e "${GREEN}  ✓ 通过${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}  ✗ 失败${NC}"
        FAILED=$((FAILED + 1))
    fi
    echo ""
}

# 1. 检查文件存在
test_case "transcribe.sh 文件存在" "[ -f '${TRANSCRIBE_SCRIPT}' ]"
test_case "zhipu_asr.py 文件存在" "[ -f '${SCRIPT_DIR}/zhipu_asr.py' ]"

# 2. 检查脚本语法
test_case "transcribe.sh 语法正确" "bash -n '${TRANSCRIBE_SCRIPT}'"

# 3. 检查依赖
test_case "python3 已安装" "command -v python3 &> /dev/null"
test_case "curl 已安装" "command -v curl &> /dev/null"
test_case "jq 已安装" "command -v jq &> /dev/null"

# 4. 检查 Python 库
test_case "requests 库已安装" "python3 -c 'import requests' 2>&1"

# 5. 检查环境变量
echo -e "${BLUE}环境变量检查:${NC}"
if [ -n "${ZHIPU_API_KEY}" ]; then
    echo -e "${GREEN}  ✓ ZHIPU_API_KEY 已设置${NC}"
else
    echo -e "${YELLOW}  ⚠ ZHIPU_API_KEY 未设置（使用配置文件中的值）${NC}"
fi

if [ -n "${TELEGRAM_BOT_TOKEN}" ]; then
    echo -e "${GREEN}  ✓ TELEGRAM_BOT_TOKEN 已设置${NC}"
else
    echo -e "${YELLOW}  ⚠ TELEGRAM_BOT_TOKEN 未设置（使用配置文件中的值）${NC}"
fi
echo ""

# 6. 检查 OpenClaw 配置
echo -e "${BLUE}OpenClaw 配置检查:${NC}"
if grep -q '"media"' ~/.openclaw/openclaw.json; then
    echo -e "${GREEN}  ✓ media 配置已添加${NC}"
else
    echo -e "${RED}  ✗ media 配置未添加${NC}"
    FAILED=$((FAILED + 1))
fi

if grep -q '"audio"' ~/.openclaw/openclaw.json && grep -q '"enabled": true' ~/.openclaw/openclaw.json; then
    echo -e "${GREEN}  ✓ audio 已启用${NC}"
else
    echo -e "${RED}  ✗ audio 未启用${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# 7. 测试 API 连通性
echo -e "${BLUE}API 连通性测试:${NC}"

# 智谱 API 测试（不实际调用，只检查域名解析）
if host open.bigmodel.cn &> /dev/null; then
    echo -e "${GREEN}  ✓ open.bigmodel.cn 可解析${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}  ⚠ open.bigmodel.cn 解析失败（可能需要网络）${NC}"
fi

# Telegram API 测试
TELEGRAM_TOKEN="${TELEGRAM_BOT_TOKEN:-8503419838:AAHxF3eOzDAJhIjhxxATCMekRXQ07h-SriY}"
if curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe" | grep -q '"ok":true'; then
    echo -e "${GREEN}  ✓ Telegram Bot API 可访问${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}  ✗ Telegram Bot API 不可访问${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}测试总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "通过: ${GREEN}${PASSED}${NC}"
echo -e "失败: ${RED}${FAILED}${NC}"
echo ""

if [ ${FAILED} -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过${NC}"
    echo ""
    echo "下一步："
    echo "  1. 重启 OpenClaw Gateway:"
    echo "     openclaw gateway restart"
    echo ""
    echo "  2. 发送语音消息到 Telegram 机器人进行测试"
    echo ""
    echo "  3. 查看日志:"
    echo "     openclaw logs --follow"
    exit 0
else
    echo -e "${RED}✗ 部分测试失败，请检查上述错误${NC}"
    exit 1
fi
