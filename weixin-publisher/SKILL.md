---
name: weixin-publisher
description: 微信公众号发布工具。提供获取 access_token、上传封面图到素材库、准备草稿 JSON 等功能，用于将排版好的文章发布到微信公众号。当用户需要将文章上传到微信公众号时使用此技能。
version: 1.0.0
dependencies: []
---
# 微信公众号发布工具

## 功能

通过微信公众号 API 完成文章发布的最后一步：获取 token、上传素材、创建草稿。

## 前置配置

需要在 `{skill_root}/.env` 中配置：

```env
WECHAT_APPID=你的公众号AppID
WECHAT_APPSECRET=你的公众号AppSecret
```

## 脚本说明

### 1. 获取 access_token

```bash
bash {skill_root}/scripts/get_token.sh
```

调用微信 API 获取 access_token（有效期 2 小时）。

### 2. 上传封面图

```bash
bash {skill_root}/scripts/upload_image.sh <access_token> <图片文件路径>
```

将本地图片上传到微信素材库，返回 media_id。

### 3. 准备草稿

```bash
bash {skill_root}/scripts/prepare_draft.sh <access_token> <文章标题> <HTML文件路径> <封面media_id>
```

生成完整的草稿 JSON 到 `/tmp/wechat_draft.json`，并提供上传 curl 命令。

## 完整发布流程

```
1. bash scripts/get_token.sh → 获取 access_token
2. 准备封面图（使用 image-gen 技能或手动）
3. bash scripts/upload_image.sh $token cover.png → 获取 media_id
4. bash scripts/prepare_draft.sh $token "标题" article.html $media_id
5. 使用输出的 curl 命令上传草稿，或手动在公众号后台操作
```

## 注意事项

- access_token 有效期 2 小时，过期需重新获取
- 每日 API 调用有频率限制
- 草稿上传后需在公众号后台手动发布
- 作者名默认为「墨香异境」，可在 prepare_draft.sh 中修改
