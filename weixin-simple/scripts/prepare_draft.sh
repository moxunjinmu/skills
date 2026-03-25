#!/bin/bash
#
# 准备微信公众号草稿发布信息
# 使用方法: bash prepare_draft.sh <access_token> <文章标题> <HTML文件路径> <封面media_id>
#

ACCESS_TOKEN="$1"
TITLE="$2"
HTML_FILE="$3"
MEDIA_ID="$4"

if [ -z "$ACCESS_TOKEN" ] || [ -z "$TITLE" ] || [ -z "$HTML_FILE" ] || [ -z "$MEDIA_ID" ]; then
    echo "使用方法: bash prepare_draft.sh <access_token> <文章标题> <HTML文件路径> <封面media_id>"
    echo ""
    echo "示例:"
    echo "  bash prepare_draft.sh \"your_token\" \"文章标题\" \"article.html\" \"media_id_xxx\""
    exit 1
fi

if [ ! -f "$HTML_FILE" ]; then
    echo "错误: HTML 文件不存在: $HTML_FILE"
    exit 1
fi

# 读取 HTML 内容
HTML_CONTENT=$(cat "$HTML_FILE")

# 准备 JSON 数据
cat > /tmp/wechat_draft.json <<EOF
{
  "articles": [{
    "article_type": "news",
    "title": "$TITLE",
    "author": "墨香异境",
    "content": $(echo "$HTML_CONTENT" | jq -Rs .),
    "thumb_media_id": "$MEDIA_ID",
    "show_cover_pic": 1,
    "need_open_comment": 1,
    "only_fans_can_comment": 0,
    "auto_publish": false
  }]
}
EOF

echo "已准备好草稿发布信息"
echo ""
echo "access_token: $ACCESS_TOKEN"
echo "文章标题: $TITLE"
echo "封面 media_id: $MEDIA_ID"
echo ""
echo "完整的 JSON 数据已保存到: /tmp/wechat_draft.json"
echo ""
echo "你可以:"
echo "1. 手动复制内容到微信公众号后台"
echo "2. 使用 curl 命令上传:"
echo ""
echo "curl -X POST \\"
echo "  \"https://api.weixin.qq.com/cgi-bin/draft/add?access_token=$ACCESS_TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d @/tmp/wechat_draft.json"
