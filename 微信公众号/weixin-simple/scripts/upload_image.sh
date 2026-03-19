#!/bin/bash
#
# 上传图片到微信公众号素材库
# 使用方法: bash upload_image.sh <access_token> <图片文件路径>
#

ACCESS_TOKEN="$1"
IMAGE_PATH="$2"

if [ -z "$ACCESS_TOKEN" ]; then
    echo "使用方法: bash upload_image.sh <access_token> <图片文件路径>"
    exit 1
fi

if [ -z "$IMAGE_PATH" ]; then
    echo "使用方法: bash upload_image.sh <access_token> <图片文件路径>"
    exit 1
fi

if [ ! -f "$IMAGE_PATH" ]; then
    echo "错误: 图片文件不存在: $IMAGE_PATH"
    exit 1
fi

echo "正在上传图片到微信公众号素材库..."
echo "文件: $IMAGE_PATH"

# 调用微信 API 上传图片
RESPONSE=$(curl -s -X POST \
    "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=$ACCESS_TOKEN&type=image" \
    -F "media=@$IMAGE_PATH")

# 提取 media_id
MEDIA_ID=$(echo "$RESPONSE" | grep -o '"media_id":"[^"]*' | cut -d'"' -f4)

if [ -n "$MEDIA_ID" ]; then
    echo "上传成功!"
    echo "media_id: $MEDIA_ID"
    echo "$MEDIA_ID"
else
    echo "错误: 未能获取 media_id"
    echo "响应: $RESPONSE"
    exit 1
fi
