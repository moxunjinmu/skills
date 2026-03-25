# Feishu Bitable References

## 当前状态

`feishu-bitable` 已独立成立，负责飞书多维表格自动化。

当前已覆盖：
- record CRUD（含 delete / batch delete）
- field CRUD（含 delete）
- create-duplex-link
- 表清理辅助

## 已知重点问题

### DuplexLink
- `type=21` 已确认是 DuplexLink
- 当前仍需继续稳定收敛 `DuplexLinkFieldPropertyError`
- 后续应重点沉淀：property schema、知识库内表创建方式、回链字段命名规范

## 外部能力吸收目标

### `feishu-bitable-field`
优先吸收：
- 字段创建参数组织方式
- 字段 property 说明
- 字段配置层面的边界

## 后续整理方向

### docs / workflow
- 新建表默认垃圾行列清理 SOP
- 知识库内正式表治理 SOP
- DuplexLink 调试记录

### scripts
- 增补 message/log 输出
- 增补更明确的 create-field property 模板
