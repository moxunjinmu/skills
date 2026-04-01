---
name: aipoju-checkin
description: AI破局俱乐部训练营自动打卡。通过浏览器自动化完成每日打卡提交。触发词：「打卡」「checkin」「每日打卡」。支持两个训练营：OpenClaw自媒体IP获客 + AI编程产品出海。使用 openclaw browser profile 执行。
---

## 1. 概述

本 skill 用于自动完成 AI破局俱乐部 两个训练营的每日打卡。

- **IP训练营**：OpenClaw自媒体IP获客
- **出海训练营**：AI编程产品出海（含OpenClaw）

每日 23:59 前必须完成打卡，否则视为缺勤。

## 2. 环境要求

- **浏览器**：openclaw profile（已登录 aipoju.com）
- **验证方式**：先 navigate 到 `https://aipoju.com/user/joined`，确认能正常加载

## 3. 训练营配置

| 字段 | IP训练营 | 出海训练营 |
|------|---------|-----------|
| 名称 | OpenClaw自媒体IP获客 | AI编程产品出海（含OpenClaw） |
| 训练营详情页 | https://aipoju.com/details/1d1141a3-e374-479f-97ab-f1e4f5f818af/a402921c-15cb-4ab4-ad39-cb91a275eba8 | https://aipoju.com/details/1d1141a3-e374-479f-97ab-f1e4f5f818af/88f0b501-c2e8-4bfa-a66a-630588c9df41 |
| 打卡页URL | https://aipoju.com/user/task-clock-in/1d1141a3-e374-479f-97ab-f1e4f5f818af/a402921c-15cb-4ab4-ad39-cb91a275eba8/OpenClaw自媒体IP获客 | https://aipoju.com/user/task-clock-in/1d1141a3-e374-479f-97ab-f1e4f5f818af/88f0b501-c2e8-4bfa-a66a-630588c9df41/AI编程产品出海（含OpenClaw） |
| 内容方向 | 国内平台运营、微信公众号、知乎、B站、小红书、抖音/视频号、私域获客、AI工具实测、独立开发实战 | 出海产品增长、技术产品开发、独立开发者经验、SEO、内容营销、商业模式 |

## 4. 执行步骤（SOP）

### Step 1: 生成打卡内容

- 读取当日 `memory/YYYY-MM-DD.md` 获取今日活动摘要
- 按 `references/content-rules.md` 中的规则分别生成两个训练营的内容
- 每个字段 ≥ 50 字

### Step 2: 打开打卡页面

- browser navigate 到打卡页 URL（profile: "openclaw"）
- 等页面加载完成后 snapshot

### Step 3: 定位表单字段

- snapshot 获取页面结构
- **字段按 label 定位（不是按 ref 编号！ref 每次渲染会变）**：
  - 包含 "今日行动" 的 textbox → 今日行动
  - 包含 "今日复盘" 的 textbox → 今日复盘
  - 包含 "好事分享" 的 textbox → 好事分享（选填）
  - 包含 "下一步行动" 的 textbox → 下一步行动
  - 提交按钮：text 为 "打 卡" 的 button

### Step 4: 填写表单

- 逐个 click textbox → type 内容
- 每个字段填完后确认字数 ≥ 50

### Step 5: 提交

- click "打 卡" 按钮
- snapshot 检查是否出现"行动海报"或按钮变为 disabled
- 若提示"请填写至少50个字" → 补充对应字段内容后重新提交

### Step 6: 收尾

- 确认打卡成功后，browser close 关闭当前 tab
- 更新 `memory/YYYY-MM-DD.md` 打卡状态为 ✅

### Step 7: 重复 Step 2-6 打第二个训练营

## 5. 重要注意事项

- 页面是 SPA（Ant Design），URL 跳转必须用浏览器 navigate，不能直接跳
- ref 编号每次渲染会变，必须按 label/文本内容定位字段
- 填写速度要快，页面可能自动刷新清空表单
- 打卡完成后必须关闭 tab，不能留着
- 已打卡的页面按钮会变为 disabled（"今日已打卡"），此时跳过
- 两个训练营内容不能完全一样，需根据各自方向调整

## 6. 错误处理

| 错误 | 处理 |
|------|------|
| 页面未加载 | 重试一次 navigate |
| 字段被清空 | 重新填写，这次填写后立即点提交 |
| "请填写至少50个字" | 补充对应字段内容 |
| 按钮已 disabled | 说明今日已打卡，跳过 |
