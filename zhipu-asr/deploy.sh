#!/bin/bash
# -*- coding: utf-8 -*-
#
# 智谱 ASR 部署脚本
# 一键部署到 OpenClaw
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}智谱 ASR 部署脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请使用 sudo 或以 root 用户运行此脚本${NC}"
    exit 1
fi

SKILL_DIR="/root/.openclaw/skills/zhipu-asr"
CONFIG_FILE="/root/.openclaw/openclaw.json"
BACKUP_FILE="/root/.openclaw/openclaw.json.backup.$(date +%Y%m%d%H%M%S)"

# 检查 Skill 是否存在
if [ ! -d "${SKILL_DIR}" ]; then
    echo -e "${RED}错误: Skill 目录不存在: ${SKILL_DIR}${NC}"
    echo "请确保已完成以下步骤："
    echo "  1. 创建 Skill 目录"
    echo "  2. 复制 zhipu_asr.py"
    echo "  3. 创建相关脚本和配置文件"
    exit 1
fi

echo -e "${GREEN}✓ Skill 目录存在${NC}"

# 检查配置文件
if [ ! -f "${CONFIG_FILE}" ]; then
    echo -e "${RED}错误: OpenClaw 配置文件不存在: ${CONFIG_FILE}${NC}"
    exit 1
fi

echo -e "${GREEN}✓ OpenClaw 配置文件存在${NC}"
echo ""

# 备份配置文件
echo -e "${YELLOW}备份现有配置文件...${NC}"
cp "${CONFIG_FILE}" "${BACKUP_FILE}"
echo -e "${GREEN}✓ 配置已备份到: ${BACKUP_FILE}${NC}"
echo ""

# 询问 API Key
echo -e "${YELLOW}请输入智谱 API Key:${NC}"
echo "  (从 https://open.bigmodel.cn/ 获取)"
read -p "API Key: " API_KEY

if [ -z "${API_KEY}" ]; then
    echo -e "${RED}错误: API Key 不能为空${NC}"
    echo "已取消配置"
    exit 1
fi

# 使用 Python 修改配置文件
echo -e "${YELLOW}配置 OpenClaw...${NC}"

python3 << EOF
import json

# 读取现有配置
with open('${CONFIG_FILE}', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 确保 skills 配置存在
if 'skills' not in config:
    config['skills'] = {}

# 添加或更新 zhipu-asr 配置
config['skills']['zhipu-asr'] = {
    'apiKey': '${API_KEY}'
}

# 确保 tools.media.audio 配置存在
if 'tools' not in config:
    config['tools'] = {}
if 'media' not in config['tools']:
    config['tools']['media'] = {}
if 'audio' not in config['tools']['media']:
    config['tools']['media']['audio'] = {}

# 启用音频处理
config['tools']['media']['audio']['enabled'] = True

# 配置模型
config['tools']['media']['audio']['maxBytes'] = 26214400

# 添加智谱 ASR 模型
audio_models = config['tools']['media']['audio'].get('models', [])

# 检查是否已存在智谱 ASR 配置
exists = False
for model in audio_models:
    if isinstance(model, dict) and model.get('type') == 'cli':
        command = model.get('command', '')
        if 'zhipu-asr' in command:
            exists = True
            # 更新现有配置
            model['command'] = 'bash'
            model['args'] = ['${SKILL_DIR}/transcribe.sh', '{{MediaPath}}']
            model['timeoutSeconds'] = 120
            break

if not exists:
    # 添加到列表开头（优先使用）
    audio_models.insert(0, {
        'type': 'cli',
        'command': 'bash',
        'args': ['${SKILL_DIR}/transcribe.sh', '{{MediaPath}}'],
        'timeoutSeconds': 120
    })

config['tools']['media']['audio']['models'] = audio_models

# 保存配置
with open('${CONFIG_FILE}', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("配置已更新")
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 配置已更新${NC}"
else
    echo -e "${RED}✗ 配置更新失败${NC}"
    echo "正在恢复备份..."
    cp "${BACKUP_FILE}" "${CONFIG_FILE}"
    exit 1
fi
echo ""

# 检查 Python 依赖
echo -e "${YELLOW}检查 Python 依赖...${NC}"
if python3 -c "import requests" 2>/dev/null; then
    echo -e "${GREEN}✓ requests 库已安装${NC}"
else
    echo -e "${YELLOW}  requests 库未安装，正在安装...${NC}"
    pip3 install requests
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ requests 库安装成功${NC}"
    else
        echo -e "${RED}✗ requests 库安装失败${NC}"
        exit 1
    fi
fi
echo ""

# 运行测试
echo -e "${YELLOW}运行测试...${NC}"
if "${SKILL_DIR}/test.sh" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 测试通过${NC}"
else
    echo -e "${RED}✗ 测试失败${NC}"
    echo "请检查日志"
    exit 1
fi
echo ""

# 询问是否重启 Gateway
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "配置已成功添加到 OpenClaw"
echo ""
echo "下一步："
echo "  1. 重启 Gateway 使配置生效"
echo "  2. 在 Telegram 发送语音消息测试"
echo ""
read -p "是否现在重启 Gateway? (y/n): " RESTART

if [ "${RESTART}" = "y" ] || [ "${RESTART}" = "Y" ]; then
    echo ""
    echo -e "${YELLOW}重启 Gateway...${NC}"
    openclaw gateway restart
    echo ""
    echo -e "${GREEN}✓ Gateway 已重启${NC}"
    echo ""
    echo "查看状态: openclaw gateway status"
    echo "查看日志: openclaw logs --follow"
else
    echo ""
    echo -e "${YELLOW}请手动重启 Gateway:${NC}"
    echo "  openclaw gateway restart"
fi
