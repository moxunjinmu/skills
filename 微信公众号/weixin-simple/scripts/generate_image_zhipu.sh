#!/bin/bash
#
# 调用智谱AI (ZhipuAI) GLM-Image 模型生成公众号封面图
# 使用方法: bash generate_image_zhipu.sh "图片提示词"
#

# 获取脚本所在目录的父目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# 加载环境变量
if [ -f "$PARENT_DIR/.env" ]; then
    set -a
    source "$PARENT_DIR/.env"
    set +a
else
    echo "错误: 未找到 .env 配置文件: $PARENT_DIR/.env"
    exit 1
fi

# 检查必需的环境变量
if [ -z "$ZHIPU_API_KEY" ]; then
    echo "错误: ZHIPU_API_KEY 环境变量未设置"
    echo "请在 .env 文件中配置: ZHIPU_API_KEY=your_api_key"
    exit 1
fi

# 获取图片提示词
IMAGE_PROMPT="$1"

if [ -z "$IMAGE_PROMPT" ]; then
    echo "使用方法: bash generate_image_zhipu.sh \"图片提示词\""
    echo ""
    echo "示例:"
    echo "  bash generate_image_zhipu.sh \"一只可爱的小猫咪，坐在阳光明媚的窗台上\""
    exit 1
fi

# 模型选择：glm-image (旗舰) 或 cogview-4 (免费)
MODEL="${ZHIPU_MODEL:-glm-image}"

# 图片尺寸（公众号推荐横版）
SIZE="${ZHIPU_SIZE:-1024x1024}"

echo "正在使用智谱AI生成封面图..."
echo "模型: $MODEL"
echo "提示词: $IMAGE_PROMPT"
echo "尺寸: $SIZE"
echo "---"

# 调用智谱AI API生成图片
RESPONSE=$(curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/images/generations" \
    -H "Authorization: Bearer $ZHIPU_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL\",
        \"prompt\": \"$IMAGE_PROMPT\",
        \"size\": \"$SIZE\"
    }")

# 提取图片URL
IMAGE_URL=$(echo "$RESPONSE" | grep -o '"url":"[^"]*' | cut -d'"' -f4 | head -1)

if [ -n "$IMAGE_URL" ]; then
    echo "✅ 封面图生成成功!"
    echo "图片URL: $IMAGE_URL"
    echo ""
    echo "💡 提示: 智谱AI生成的是图片URL，可以使用以下命令下载:"
    echo "   curl -o cover.png \"$IMAGE_URL\""
    echo "$IMAGE_URL"
else
    echo "❌ 错误: 未能获取图片URL"
    echo "响应: $RESPONSE"
    exit 1
fi
