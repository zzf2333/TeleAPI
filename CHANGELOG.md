# Changelog

## v0.1.0 (2025-05-08)

首个公开版本。

### Features

- Telegram 用户账号登录（QR 扫码 / 手机号验证码 / 2FA）
- 多频道配置与历史消息同步（支持增量 / 全量）
- 新消息实时监听，自动入库
- REST API：频道列表、消息查询（游标分页、关键词/类型/时间过滤）
- Webhook 推送（HMAC-SHA256 签名、失败指数退避重试）
- 关键词 / 正则过滤引擎，支持频道级和消息类型过滤
- 后台管理界面（React + Tailwind，全中文）
- Docker 一键部署（多阶段构建，前后端打包）
- YAML 配置 + 环境变量覆盖 + 弱密钥校验

### Bug Fixes

- 修复 `_async_session_factory` 导入时为 None 导致启动崩溃
- 修复用户无 username 时界面显示空的 `(@)`
- 修复 `GET /api/channels/{id}` 找不到频道时返回 200 而非 404
- 修复 auth 端点鉴权遗漏 + Swagger 文档路径

### Tests

- 222 个测试用例覆盖单元 / 数据库 / 服务层 / API / E2E 五层
