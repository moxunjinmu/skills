# Feishu / 知识库常见坑

## 1. 表建对了名字，但建错了位置

常见误区：
- 先创建了独立 Base app
- 再在 wiki 里又建了一个同名节点
- 最终数据写进了独立 app，而不是知识库内正式表

规避方法：
1. 先确认知识库 space_id 和 parent_node_token
2. 创建后立即核对正式 app_token / table_id
3. 用最终知识库链接验证，而不是只看标题

## 2. 新建多维表默认带空白行和占位列

默认通常会带：
- 10 条空白记录
- 默认字段：`Text` / `Single option` / `Date` / `Attachment`

收尾前必须：
- 删除空白行
- 删除无用默认列
- 主键列改为语义化名称

## 3. 规则和定位信息写错地方

正确分层：
- 长期规则 / 结论 → `MEMORY.md`
- app_token / table_id / URL / 路径 → `TOOLS.md`
- 当日过程 → `memory/YYYY-MM-DD.md`
- 可复用流程 → `docs/workflows/`

## 4. 独立表与知识库表混用

如果正式目标是知识库内表：
- 旧独立表立即标记为废弃
- 后续默认语义只指向正式知识库表
- 不要在两个地方并行更新

## 5. 双向关联自动化比删记录更难

当前验证结论：
- 删记录自动化已打通
- DuplexLink 自动创建仍需继续攻关
- 已知错误：`DuplexLinkFieldPropertyError`

因此现阶段：
- 业务先以表结构正确、定位正确为第一优先级
- 双向关联自动化作为后续专项优化
