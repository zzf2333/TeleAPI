# TeleAPI

A lightweight Telegram channel API gateway.

TeleAPI 将你已订阅的 Telegram 频道内容同步为结构化数据，并通过 REST API 和 Webhook 对外提供访问能力。

## Features

- Telegram 用户账号 QR 扫码登录
- 多频道配置与历史消息同步
- 新消息实时监听
- REST API 查询频道和消息
- Webhook 推送（HMAC-SHA256 签名 + 失败重试）
- 关键词 / 正则过滤引擎
- 轻量后台管理界面
- Docker 一键部署

## Quick Start

### 1. 获取 Telegram API 凭证

前往 [https://my.telegram.org](https://my.telegram.org) 创建应用，获取 `api_id` 和 `api_hash`。

### 2. 配置

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，填入：

- `telegram.api_id` 和 `telegram.api_hash`
- `security.admin_api_key`（至少 16 位，不可使用默认值）
- 需要监听的频道列表

### 3. Docker 启动

```bash
docker compose up -d
```

### 4. 登录

打开 `http://localhost:8080`，输入 Admin API Key，扫码登录 Telegram。

## 本地开发

```bash
# 后端
uv sync
cp config.example.yaml config.yaml  # 编辑配置
uv run uvicorn teleapi.main:app --host 0.0.0.0 --port 8080 --reload

# 前端
cd frontend
npm install
npm run dev
```

## API

启动后访问 `http://localhost:8080/docs` 查看 OpenAPI 文档。

### 主要端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查（无需鉴权） |
| GET | `/api/channels` | 频道列表 |
| GET | `/api/channels/{id}/messages` | 频道消息（支持分页、搜索） |
| POST | `/api/channels/{id}/sync` | 触发历史同步 |
| GET | `/api/sync-jobs` | 同步任务列表 |
| GET | `/api/webhook-deliveries` | Webhook 推送日志 |
| GET | `/api/system/status` | 系统状态 |
| GET | `/api/system/config-check` | 配置检查 |

### 鉴权

除 `/health` 外，所有 API 需要携带密钥：

```
Authorization: Bearer your_admin_api_key
```

或：

```
X-TeleAPI-Key: your_admin_api_key
```

## 技术栈

- Python / FastAPI / Telethon / SQLModel / SQLite
- React / Vite / Tailwind CSS
- Docker Compose

## License

MIT
