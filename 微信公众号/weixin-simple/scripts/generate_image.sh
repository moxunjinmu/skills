#!/bin/bash
#
# 调用 n8n 即梦 API 生成公众号封面图（增强版，支持设计哲学，支持智谱降级）
# 使用方法: bash generate_image.sh "图片提示词" [文章类型]
# 示例: bash generate_image.sh "AI教育" "干货教程"
#
# 降级策略: n8n未配置 → 智谱AI → 失败
#

# 获取脚本所在目录的父目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# 加载环境变量（兼容 Windows Git Bash）
if [ -f "$PARENT_DIR/.env" ]; then
    set -a
    source "$PARENT_DIR/.env"
    set +a
else
    echo "错误: 未找到 .env 配置文件: $PARENT_DIR/.env"
    exit 1
fi

# 获取图片提示词
IMAGE_PROMPT="$1"
ARTICLE_TYPE="$2"

if [ -z "$IMAGE_PROMPT" ]; then
    echo "使用方法: bash generate_image.sh \"图片提示词\" [文章类型]"
    echo ""
    echo "示例:"
    echo "  bash generate_image.sh \"AI教育\""
    echo "  bash generate_image.sh \"AI教育\" \"干货教程\""
    echo ""
    echo "文章类型选项（可选，用于应用设计哲学）:"
    echo "  干货教程, 观点评论, 案例分析, 热点追踪, 科技前沿, 情感故事, 商务分析"
    exit 1
fi

# 如果提供了文章类型，使用设计哲学增强提示词
if [ -n "$ARTICLE_TYPE" ]; then
    echo "应用设计哲学: $ARTICLE_TYPE"
    PHILOSOPHY_PROMPT=$(bash "$SCRIPT_DIR/design-philosophy.sh" "$ARTICLE_TYPE" "$IMAGE_PROMPT")
    FINAL_PROMPT="$PHILOSOPHY_PROMPT"
else
    # 使用基础提示词
    FINAL_PROMPT="$IMAGE_PROMPT, professional poster design, 900x500 pixels, clean composition"
fi

echo "正在生成封面图..."
echo "主题: $IMAGE_PROMPT"
[ -n "$ARTICLE_TYPE" ] && echo "文章类型: $ARTICLE_TYPE"
echo "提示词: $FINAL_PROMPT"
echo "---"

# 调用 API（优先 n8n，降级到智谱）
if [ -n "$N8N_WEBHOOK_URL" ] && [[ "$N8N_WEBHOOK_URL" != *"your-n8n-instance"* ]]; then
    echo "使用 n8n 即梦 API..."
    # 调用 n8n API
    if [ -n "$N8N_USERNAME" ] && [ -n "$N8N_PASSWORD" ]; then
        RESPONSE=$(curl -s -X POST "$N8N_WEBHOOK_URL" \
            -u "$N8N_USERNAME:$N8N_PASSWORD" \
            -H "Content-Type: application/json" \
            -d "{\"image_prompt\": \"$FINAL_PROMPT\"}")
    else
        RESPONSE=$(curl -s -X POST "$N8N_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"image_prompt\": \"$FINAL_PROMPT\"}")
    fi
    # 提取图片URL
    IMAGE_URL=$(echo "$RESPONSE" | grep -o '"randomImg":"[^"]*' | cut -d'"' -f4)
elif [ -n "$ZHIPU_API_KEY" ] && [[ "$ZHIPU_API_KEY" != *"your_zhipu_api_key"* ]]; then
    echo "⚠️  n8n 未配置，使用智谱AI GLM-Image..."
    # 调用智谱API
    RESPONSE=$(curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/images/generations" \
        -H "Authorization: Bearer $ZHIPU_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"glm-image\",
            \"prompt\": \"$FINAL_PROMPT\",
            \"size\": \"1024x1024\"
        }")
    # 提取图片URL
    IMAGE_URL=$(echo "$RESPONSE" | grep -o '"url":"[^"]*' | cut -d'"' -f4 | head -1)
else
    echo "❌ 错误: 未配置图片生成服务"
    echo ""
    echo "请配置以下任一服务:"
    echo "1. n8n 即梦 API (推荐):"
    echo "   N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/jimeng"
    echo ""
    echo "2. 智谱AI GLM-Image (备用):"
    echo "   ZHIPU_API_KEY=your_api_key"
    echo ""
    echo "配置后请重新运行此脚本"
    exit 1
fi

if [ -n "$IMAGE_URL" ]; then
    echo "✅ 封面图生成成功!"
    echo "图片URL: $IMAGE_URL"
    echo "$IMAGE_URL"
else
    echo "❌ 错误: 未能获取图片URL"
    echo "响应: $RESPONSE"
    exit 1
fi
