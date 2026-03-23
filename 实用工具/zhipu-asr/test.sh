#!/bin/bash
# -*- coding: utf-8 -*-
#
# 智谱 ASR 测试脚本
# 用于测试语音识别功能
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRANSCRIBE_SCRIPT="${SCRIPT_DIR}/transcribe.sh"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}智谱 ASR 测试脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 API Key
if [ -z "${ZHIPU_API_KEY}" ]; then
    echo -e "${YELLOW}警告: ZHIPU_API_KEY 环境变量未设置${NC}"
    echo "请先设置 API Key:"
    echo "  export ZHIPU_API_KEY=your_api_key_here"
    echo ""
fi

# 检查依赖
echo -e "${GREEN}1. 检查依赖...${NC}"
if command -v python3 &> /dev/null; then
    echo "  ✓ python3 已安装"
    python3 --version
else
    echo "  ✗ python3 未安装"
    exit 1
fi

if [ -f "${SCRIPT_DIR}/zhipu_asr.py" ]; then
    echo "  ✓ zhipu_asr.py 模块存在"
else
    echo "  ✗ zhipu_asr.py 模块不存在"
    exit 1
fi

if [ -f "${TRANSCRIBE_SCRIPT}" ]; then
    echo "  ✓ transcribe.sh 脚本存在"
else
    echo "  ✗ transcribe.sh 脚本不存在"
    exit 1
fi
echo ""

# 测试脚本语法
echo -e "${GREEN}2. 测试脚本语法...${NC}"
if bash -n "${TRANSCRIBE_SCRIPT}"; then
    echo "  ✓ transcribe.sh 语法正确"
else
    echo "  ✗ transcribe.sh 语法错误"
    exit 1
fi
echo ""

# 检查 Python 模块
echo -e "${GREEN}3. 测试 Python 模块...${NC}"
if python3 -c "import sys; sys.path.insert(0, '${SCRIPT_DIR}'); import zhipu_asr; print('  ✓ zhipu_asr 模块导入成功')" 2>&1; then
    :
else
    echo "  ✗ zhipu_asr 模块导入失败"
    echo "  请检查 requests 库是否安装: pip3 install requests"
    exit 1
fi
echo ""

# 测试参数解析
echo -e "${GREEN}4. 测试参数解析...${NC}"
echo "测试 --help 参数:"
if "${TRANSCRIBE_SCRIPT}" --help 2>&1 | grep -q "用法"; then
    echo "  ✓ 参数解析正常"
else
    echo "  ⚠ 无法显示帮助信息"
fi
echo ""

# 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 基础测试通过${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "下一步："
echo "  1. 设置 API Key: export ZHIPU_API_KEY=your_key"
echo "  2. 准备测试音频文件（.wav 或 .mp3）"
echo "  3. 运行测试:"
echo "     ${TRANSCRIBE_SCRIPT} /path/to/test.wav"
echo ""
