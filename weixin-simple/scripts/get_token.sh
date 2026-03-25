#!/bin/bash
#
# 获取微信公众号 access_token
# 使用方法: bash get_token.sh
#

# 获取脚本所在目录的父目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# 加载环境变量（兼容 Windows Git Bash）
if [ -f "$PARENT_DIR/.env" ]; then
    # 方式1：使用 set -a
    set -a
    source "$PARENT_DIR/.env"
    set +a
else
    echo "错误: 未找到 .env 配置文件: $PARENT_DIR/.env"
    exit 1
fi

# 检查必需的环境变量
if [ -z "$WECHAT_APPID" ] || [ -z "$WECHAT_APPSECRET" ]; then
    echo "错误: WECHAT_APPID 或 WECHAT_APPSECRET 环境变量未设置"
    echo "请检查 .env 文件配置"
    exit 1
fi

echo "正在获取微信公众号 access_token..."

# 调用微信 API
RESPONSE=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=$WECHAT_APPID&secret=$WECHAT_APPSECRET")

# 提取 access_token
ACCESS_TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$ACCESS_TOKEN" ]; then
    echo "获取成功!"
    echo "access_token: $ACCESS_TOKEN"
    echo "$ACCESS_TOKEN"
else
    echo "错误: 未能获取 access_token"
    echo "响应: $RESPONSE"
    exit 1
fi
