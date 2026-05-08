# TeleAPI 技术架构

## 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | Python 3.12+ |
| 包管理 | uv |
| API 框架 | FastAPI (async) |
| Telegram | Telethon (用户账号) |
| ORM | SQLModel (Pydantic + SQLAlchemy) |
| 数据库 | SQLite + aiosqlite |
| 配置 | YAML + Pydantic 校验 |
| 前端 | React + Vite + Tailwind CSS |
| 部署 | Docker Compose |

## 模块结构

```
src/teleapi/
├── main.py              # FastAPI app + lifespan 生命周期管理
├── config.py            # YAML 配置加载 + Pydantic 校验 + 环境变量覆盖
├── database.py          # async SQLite engine + session factory
├── auth.py              # admin_api_key 鉴权中间件
├── models/              # SQLModel 数据模型
│   ├── channel.py       # 频道
│   ├── message.py       # 消息
│   ├── sync_job.py      # 同步任务
│   └── webhook_delivery.py  # Webhook 推送记录
├── telegram/            # Telegram 相关
│   ├── client.py        # TelegramClientManager (StringSession 持久化)
│   ├── login.py         # QR 扫码登录流程
│   ├── channel_manager.py   # 频道解析 + DB upsert
│   ├── normalizer.py    # 消息结构化 (Telethon → 统一格式)
│   ├── sync.py          # 历史消息同步 (断点续传/FloodWait)
│   └── listener.py      # 实时新消息监听
├── api/                 # REST API 端点
│   ├── auth_routes.py   # /api/auth/* (QR 登录/状态/登出)
│   ├── channels.py      # /api/channels
│   ├── messages.py      # /api/messages (游标分页)
│   ├── sync.py          # /api/sync-jobs
│   ├── webhooks.py      # /api/webhook-deliveries
│   └── system.py        # /api/system/status + config-check
└── services/            # 业务服务
    ├── event.py         # 进程内事件总线 (pub/sub)
    ├── filter.py        # 关键词/正则过滤引擎
    └── webhook.py       # Webhook 分发 (HMAC签名/重试)
```

## 数据流

### 历史同步

```
config.yaml → ChannelManager → Telegram API (iter_messages)
    → Normalizer → 去重 (unique 约束) → SQLite
    → SyncJob 状态更新
```

### 实时监听

```
Telegram Channel (新消息)
    → Telethon events.NewMessage
    → Normalizer → 去重 → SQLite
    → EventDispatcher.dispatch("message.created")
        → FilterEngine.apply_filters()
        → WebhookDispatcher (HMAC签名 + httpx POST + 重试)
        → WebhookDelivery 日志
```

### API 查询

```
Client Request
    → verify_api_key (Bearer / X-TeleAPI-Key)
    → FastAPI Router → SQLModel Query → JSON Response
```

## 鉴权

- 所有 `/api/*` 端点需要 `admin_api_key`
- `/health` 免鉴权
- 支持 `Authorization: Bearer xxx` 和 `X-TeleAPI-Key: xxx`
- 使用 `secrets.compare_digest()` 防时序攻击

## 数据库

- SQLite WAL 模式，支持并发读
- 4 张表：channels, messages, sync_jobs, webhook_deliveries
- messages 表 `(channel_id, telegram_message_id)` 唯一约束保证去重
- 游标分页：基于 `(date DESC, id DESC)` 的 keyset pagination

## Session 持久化

- 使用 Telethon StringSession，序列化为字符串
- 存储在 `data/session.key`，原子写入（先写 .tmp 再 rename）
- Docker 通过 volume 挂载 `data/` 目录持久化
