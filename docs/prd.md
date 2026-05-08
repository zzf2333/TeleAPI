# TeleAPI PRD v0.1

## 1. 项目名称

**TeleAPI**

全称定位：

> A lightweight Telegram channel API gateway.

中文定位：

> 一个轻量级 Telegram 频道 API 网关，用于将已订阅的 Telegram 频道内容同步为结构化数据，并通过 API、Webhook 和 WebSocket 对外提供访问能力。

---

## 2. 一句话说明

**TeleAPI 是一个将 Telegram 订阅频道内容转换为可查询、可推送、可实时订阅数据接口的开源工具。**

它解决的问题是：

> 用户已经订阅了某些 Telegram 频道，但频道内容只能在 Telegram 客户端中浏览，无法稳定地被外部系统拉取、过滤、存储、推送和消费。

TeleAPI 通过 Telethon 登录 Telegram 用户账号，监听指定频道，将频道消息同步到本地数据库，并对外提供标准化的数据访问能力。

---

## 3. 项目背景

Telegram 上存在大量有价值的频道内容，例如：

- 加密货币资讯频道
- 美股 / 宏观 / 投研频道
- 行业情报频道
- 项目公告频道
- 新闻聚合频道
- 社区动态频道
- 交易信号频道

但 Telegram 原生使用方式存在明显限制：

1. **内容难以结构化使用**
   频道内容通常只能在客户端中查看，无法直接作为数据源接入外部系统。

2. **历史内容不方便批量同步**
   如果想拉取某个频道的历史消息，需要自己调用 Telegram API 并处理分页、限流、去重、存储等问题。

3. **新消息无法统一推送到业务系统**
   Telegram 有新消息时，外部系统通常无法通过标准 Webhook 方式接收。

4. **过滤规则分散且难维护**
   不同频道可能需要不同关键词、正则、消息类型过滤规则。

5. **第三方系统不应该直接依赖 Telegram 客户端逻辑**
   投研系统、新闻系统、AI Agent、自动化工作流等，只需要标准化 API，而不应该关心 Telethon、session、频道权限、Telegram 消息格式等底层细节。

因此，需要一个轻量级中间层：

```txt
Telegram Channels
      ↓
TeleAPI
      ↓
REST API / Webhook / WebSocket
      ↓
External Systems
```

---

## 4. 产品目标

### 4.1 核心目标

TeleAPI 的核心目标是：

> 将用户已订阅的 Telegram 频道转换为一个稳定、可查询、可推送、可实时消费的数据源。

### 4.2 具体目标

1. 支持配置多个 Telegram 频道。
2. 支持同步频道历史消息。
3. 支持监听频道新消息。
4. 支持将消息结构化存储到数据库。
5. 支持通过 REST API 查询频道和消息。
6. 支持通过 Webhook 主动推送新消息。
7. 支持通过 WebSocket 实时订阅新消息。
8. 支持基于配置文件的过滤规则。
9. 支持失败重试、推送日志和同步状态记录。
10. 支持 Docker 一键部署。

---

## 5. 非目标

v0.1 阶段不做以下事情：

1. 不做通用订阅源平台。
2. 不接入 RSS、Twitter/X、Discord、Email Newsletter 等非 Telegram 数据源。
3. 不做复杂的多租户 SaaS 权限系统。
4. 不做 Telegram Bot 群管理工具。
5. 不做 Telegram 消息发送、群发、营销工具。
6. 不做 AI 摘要、翻译、情绪分析等高级处理能力。
7. 不做复杂前端管理后台，但需要提供轻量后台管理界面，用于登录授权、查看频道、查看消息、查看同步状态、查看 Webhook 状态和基础配置检查。
8. 不保证绕过 Telegram 官方限制或权限边界。

当前阶段只聚焦：

> Telegram Channel → Structured Data → API / Webhook / WebSocket

---

## 6. 目标用户

### 6.1 开发者

需要把 Telegram 频道内容接入自己系统的开发者。

典型需求：

- 把频道消息同步到自己的数据库。
- 通过 API 查询某个频道的历史消息。
- 将新消息推送到自己的后端服务。
- 对频道内容做二次处理。

### 6.2 投研 / 情报系统构建者

需要将 Telegram 作为信息源之一接入内部投研系统的人。

典型需求：

- 监听加密货币、宏观、美股、项目公告类频道。
- 按关键词过滤重要消息。
- 将消息推送到研究系统、告警系统或 AI 分析系统。

### 6.3 自动化工作流用户

使用 n8n、Zapier、Make、自研脚本等自动化工具的人。

典型需求：

- Telegram 新消息触发工作流。
- 过滤后推送到飞书、Slack、Discord、企业微信。
- 将特定消息保存到 Notion、数据库或知识库。

---

## 7. 核心使用场景

### 7.1 同步指定频道历史消息

用户在配置文件中声明频道：

```yaml
telegram:
    channels:
        - username: "example_channel"
          enabled: true
          sync_history: true
          history_limit: 1000
```

启动服务后，TeleAPI 自动拉取该频道历史消息并写入数据库。

用户可以通过 API 查询：

```http
GET /api/channels/example_channel/messages?limit=100
```

---

### 7.2 监听频道新消息

当 Telegram 频道有新消息时：

```txt
Telegram Channel
      ↓
Telethon Listener
      ↓
Message Normalizer
      ↓
Database
```

消息会被转换为统一结构并存储。

---

### 7.3 Webhook 推送新消息

当新消息通过过滤规则后，TeleAPI 主动向配置的 Webhook 地址发送 POST 请求：

```yaml
outputs:
    webhooks:
        - name: "research-system"
          url: "https://example.com/webhooks/telegram"
          enabled: true
          events:
              - "message.created"
```

推送示例：

```json
{
	"event": "message.created",
	"channel": {
		"id": "123456",
		"username": "example_channel",
		"title": "Example Channel"
	},
	"message": {
		"id": "98765",
		"text": "This is a new message",
		"date": "2026-05-08T10:30:00+09:00",
		"url": "https://t.me/example_channel/98765"
	}
}
```

---

### 7.4 WebSocket 实时订阅

前端或客户端可以连接 WebSocket：

```txt
ws://localhost:8080/ws/messages
```

当频道有新消息时，服务端实时推送消息。

适合场景：

- 实时消息面板
- 控制台日志
- 投研信息流
- 频道监听状态展示

---

### 7.5 按规则过滤消息

用户可以通过配置文件定义过滤规则：

```yaml
filters:
    - name: "crypto-important"
      channels:
          - "example_channel"
      include_keywords:
          - "BTC"
          - "ETH"
          - "ETF"
      exclude_keywords:
          - "广告"
          - "推广"
      message_types:
          - "text"
          - "photo"
```

只有通过过滤规则的消息才会进入指定输出通道。

---

## 8. 功能需求

## 8.1 Telegram 账号登录

### 需求说明

TeleAPI 使用 Telegram 用户账号登录，而不是 Bot Token。

原因：

- Bot 无法读取用户已订阅但 Bot 未加入的频道。
- 用户账号可以访问自己已经订阅的频道内容。
- 更符合“将我订阅的频道转换为 API”的需求。

### 功能点

1. 支持配置 `api_id` 和 `api_hash`。
2. 首次启动时支持手机号登录。
3. 支持验证码输入。
4. 支持 2FA 密码输入。
5. 登录成功后保存 session。
6. 后续启动自动复用 session。

### 配置示例

```yaml
telegram:
    api_id: 123456
    api_hash: "your_api_hash"
    session_name: "teleapi"
```

---

## 8.2 频道配置

### 需求说明

用户可以在配置文件中声明需要监听和同步的频道。

### 功能点

1. 支持通过 username 配置频道。
2. 支持通过 channel id 配置频道。
3. 支持启用 / 禁用单个频道。
4. 支持为每个频道设置历史同步数量。
5. 支持为每个频道设置独立过滤规则。
6. 支持记录频道元信息。

### 配置示例

```yaml
telegram:
    channels:
        - username: "example_channel"
          enabled: true
          sync_history: true
          history_limit: 1000
          filters:
              - "crypto-important"

        - username: "another_channel"
          enabled: true
          sync_history: false
```

---

## 8.3 历史消息同步

### 需求说明

用户可以主动同步某个频道的历史消息。

### 功能点

1. 支持启动时自动同步历史消息。
2. 支持通过 API 触发同步。
3. 支持设置同步数量。
4. 支持断点续传。
5. 支持消息去重。
6. 支持记录同步状态。
7. 支持 Telegram 限流处理。

### API 示例

```http
POST /api/channels/:channelId/sync
```

请求体：

```json
{
	"limit": 1000,
	"force": false
}
```

---

## 8.4 新消息监听

### 需求说明

TeleAPI 持续监听指定频道的新消息。

### 功能点

1. 支持监听多个频道。
2. 支持接收文本消息。
3. 支持接收图片消息元信息。
4. 支持接收链接消息。
5. 支持接收转发消息基础信息。
6. 支持记录原始 Telegram message id。
7. 支持生成消息永久链接。
8. 支持去重，避免重复写入。

---

## 8.5 消息结构化

### 需求说明

Telegram 原始消息需要转换为统一 Message 数据模型。

### 标准消息结构

```json
{
	"id": "internal_message_id",
	"telegram_message_id": 98765,
	"channel_id": "internal_channel_id",
	"channel_username": "example_channel",
	"channel_title": "Example Channel",
	"type": "text",
	"text": "message content",
	"date": "2026-05-08T10:30:00+09:00",
	"edit_date": null,
	"views": 1234,
	"forwards": 12,
	"replies": 3,
	"url": "https://t.me/example_channel/98765",
	"media": [],
	"entities": [],
	"raw": {}
}
```

---

## 8.6 REST API

### 需求说明

TeleAPI 对外提供 REST API，用于查询频道、消息、同步状态和推送日志。

### 访问鉴权

除 `/health` 外，所有 REST API 默认必须通过配置密钥访问。

推荐使用请求头：

```http
Authorization: Bearer your_admin_api_key
```

也可以兼容：

```http
X-TeleAPI-Key: your_admin_api_key
```

鉴权规则：

```txt
如果未配置 api_key：服务启动失败
如果请求未携带 api_key：返回 401 Unauthorized
如果请求 api_key 错误：返回 403 Forbidden
如果请求 api_key 正确：允许访问
```

### API 列表

#### Health

```http
GET /health
```

说明：

`/health` 用于容器健康检查，可以不要求鉴权，但不得返回敏感信息。

#### 频道列表

```http
GET /api/channels
```

#### 频道详情

```http
GET /api/channels/:channelId
```

#### 频道消息列表

```http
GET /api/channels/:channelId/messages
```

支持参数：

```txt
limit       每页数量
cursor      游标
before      查询某时间之前的消息
after       查询某时间之后的消息
keyword     关键词搜索
type        消息类型
```

#### 消息详情

```http
GET /api/messages/:messageId
```

#### 触发频道同步

```http
POST /api/channels/:channelId/sync
```

#### 同步任务状态

```http
GET /api/sync-jobs/:jobId
```

#### Webhook 推送日志

```http
GET /api/webhook-deliveries
```

---

## 8.7 轻量后台管理界面

### 需求说明

TeleAPI v0.1 需要提供轻量后台管理界面，但不做复杂 SaaS 后台。

后台管理界面的目标是降低自托管用户的使用门槛，让用户可以完成授权登录、运行状态查看、频道数据查看和基础调试。

### 页面范围

v0.1 后台只包含以下页面：

1. 登录授权页
2. 系统状态页
3. 频道列表页
4. 消息列表页
5. 同步任务状态页
6. Webhook 推送日志页
7. 配置检查页

### 8.7.1 登录授权页

功能：

- 展示 Telegram QR Login 二维码。
- 展示扫码登录状态。
- 展示当前已授权 Telegram 账号。
- 支持退出登录。

### 8.7.2 系统状态页

展示：

- Telegram client 是否在线。
- 当前登录账号。
- 已启用频道数量。
- 最近一次消息接收时间。
- 数据库状态。
- 最近一次数据清理时间。
- Webhook 成功 / 失败数量。

### 8.7.3 频道列表页

展示：

- 频道名称。
- 频道 username。
- 是否启用。
- 最近消息时间。
- 最近同步状态。
- 最近 7 天消息数量。

v0.1 可以只读展示，不要求在后台动态新增频道。

### 8.7.4 消息列表页

展示：

- 消息时间。
- 所属频道。
- 消息类型。
- 消息正文摘要。
- Telegram 原文链接。

支持基础筛选：

- 按频道筛选。
- 按关键词搜索。
- 按消息类型筛选。

### 8.7.5 同步任务状态页

展示：

- 同步任务 ID。
- 频道。
- 状态。
- 已同步数量。
- 错误信息。
- 开始时间。
- 结束时间。

### 8.7.6 Webhook 推送日志页

展示：

- Webhook 名称。
- 事件类型。
- 推送状态。
- HTTP 状态码。
- 重试次数。
- 错误信息。
- 创建时间。

### 8.7.7 配置检查页

展示：

- `api_id` 是否配置。
- `api_hash` 是否配置。
- `admin_api_key` 是否配置。
- session 文件是否存在。
- SQLite 数据库是否可写。
- 配置的频道数量。
- 配置的 Webhook 数量。

### 后台访问鉴权

后台管理界面必须使用同一个 `admin_api_key` 进行访问控制。

推荐方式：

```txt
首次访问后台时输入 Admin API Key
前端保存到 localStorage 或 sessionStorage
后续请求统一附带 Authorization Header
```

v0.1 不做用户名密码系统，不做多用户 RBAC。

---

## 8.8 Webhook 推送

### 需求说明

当消息创建后，TeleAPI 可以主动向外部系统推送事件。

### 支持事件

v0.1 支持：

```txt
message.created
```

后续可扩展：

```txt
message.updated
message.deleted
channel.synced
webhook.failed
```

### 功能点

1. 支持配置多个 Webhook。
2. 支持按事件类型推送。
3. 支持按频道推送。
4. 支持按过滤规则推送。
5. 支持签名校验。
6. 支持失败重试。
7. 支持推送日志。
8. 支持禁用单个 Webhook。

### 签名机制

请求头：

```http
X-TeleAPI-Signature: sha256=xxxx
X-TeleAPI-Timestamp: 1710000000
```

签名内容：

```txt
timestamp + "." + raw_body
```

使用 HMAC-SHA256 计算。

### 配置示例

```yaml
outputs:
    webhooks:
        - name: "research-system"
          url: "https://example.com/webhook/telegram"
          secret: "your_webhook_secret"
          enabled: true
          events:
              - "message.created"
          channels:
              - "example_channel"
          filters:
              - "crypto-important"
          retry:
              max_attempts: 3
              backoff_seconds: [5, 30, 120]
```

---

## 8.9 WebSocket 实时推送

### 需求说明

WebSocket 用于前端页面或客户端实时接收新消息。

### 功能点

1. 支持客户端连接。
2. 支持按频道订阅。
3. 支持推送新消息事件。
4. 支持心跳检测。
5. 支持断线重连由客户端处理。
6. 支持简单 token 鉴权。

### 连接示例

```txt
ws://localhost:8080/ws/messages?token=xxx
```

### 订阅消息示例

```json
{
	"action": "subscribe",
	"channels": ["example_channel"]
}
```

---

## 8.10 过滤规则

### 需求说明

过滤规则用于控制哪些消息进入输出通道。

### v0.1 支持规则

1. 包含关键词。
2. 排除关键词。
3. 正则匹配。
4. 消息类型过滤。
5. 频道过滤。

### 配置示例

```yaml
filters:
    - name: "macro-news"
      include_keywords:
          - "CPI"
          - "FOMC"
          - "Fed"
      exclude_keywords:
          - "广告"
          - "推广"
      regex:
          - "(?i)rate cut"
      message_types:
          - "text"
```

### 规则逻辑

默认逻辑：

```txt
频道匹配
AND 消息类型匹配
AND 命中 include_keywords 或 regex
AND 不命中 exclude_keywords
```

如果未配置 include 或 regex，则默认不过滤关键词，只过滤排除项。

---

## 8.11 存储

### 需求说明

TeleAPI 需要持久化频道、消息、同步状态和 Webhook 推送记录。

### v0.1 推荐数据库

默认使用 SQLite，方便开源部署。

后续支持 PostgreSQL。

### 数据表

#### channels

| 字段            | 说明             |
| --------------- | ---------------- |
| id              | 内部频道 ID      |
| telegram_id     | Telegram 频道 ID |
| username        | 频道 username    |
| title           | 频道名称         |
| enabled         | 是否启用         |
| last_message_id | 最近同步消息 ID  |
| created_at      | 创建时间         |
| updated_at      | 更新时间         |

#### messages

| 字段                | 说明              |
| ------------------- | ----------------- |
| id                  | 内部消息 ID       |
| telegram_message_id | Telegram 消息 ID  |
| channel_id          | 内部频道 ID       |
| type                | 消息类型          |
| text                | 消息文本          |
| date                | 消息时间          |
| edit_date           | 编辑时间          |
| views               | 浏览数            |
| forwards            | 转发数            |
| replies             | 回复数            |
| url                 | Telegram 消息链接 |
| raw                 | 原始消息 JSON     |
| created_at          | 写入时间          |

#### sync_jobs

| 字段        | 说明                           |
| ----------- | ------------------------------ |
| id          | 同步任务 ID                    |
| channel_id  | 频道 ID                        |
| status      | pending/running/success/failed |
| total       | 计划同步数量                   |
| synced      | 已同步数量                     |
| error       | 错误信息                       |
| started_at  | 开始时间                       |
| finished_at | 结束时间                       |

#### webhook_deliveries

| 字段            | 说明           |
| --------------- | -------------- |
| id              | 推送记录 ID    |
| webhook_name    | Webhook 名称   |
| event           | 事件类型       |
| message_id      | 消息 ID        |
| status          | success/failed |
| attempts        | 重试次数       |
| response_status | HTTP 状态码    |
| response_body   | 响应内容       |
| error           | 错误信息       |
| created_at      | 创建时间       |

---

## 9. 系统架构

## 9.1 核心模块

```txt
TeleAPI
├── Telegram Client
├── Channel Manager
├── History Sync Service
├── Realtime Listener
├── Message Normalizer
├── Filter Engine
├── Storage Layer
├── REST API Server
├── Webhook Dispatcher
├── WebSocket Server
└── Config Loader
```

---

## 9.2 数据流

### 历史同步链路

```txt
User Config
    ↓
Channel Manager
    ↓
History Sync Service
    ↓
Telegram API
    ↓
Message Normalizer
    ↓
Filter Engine
    ↓
Storage Layer
```

### 新消息链路

```txt
Telegram Channel
    ↓
Realtime Listener
    ↓
Message Normalizer
    ↓
Storage Layer
    ↓
Event Dispatcher
    ├── Webhook Dispatcher
    └── WebSocket Server
```

---

## 10. 技术方案建议

## 10.1 技术栈

### 推荐方案

```txt
Language: Python
Telegram Client: Telethon
API Framework: FastAPI
Database: SQLite first, PostgreSQL later
ORM: SQLAlchemy or SQLModel
Config: YAML
Task Queue: asyncio first, Redis Queue later
Deploy: Docker / Docker Compose
Docs: OpenAPI / Swagger
```

### 选择理由

1. Telethon 是 Python 生态里成熟的 Telegram 客户端库。
2. FastAPI 适合快速构建 REST API 和 WebSocket。
3. SQLite 适合开源项目零依赖部署。
4. YAML 配置适合开发者手动维护频道和过滤规则。
5. Docker Compose 方便用户快速启动。

---

## 11. 配置文件设计

### 完整配置示例

```yaml
app:
    name: "TeleAPI"
    host: "0.0.0.0"
    port: 8080
    log_level: "info"

telegram:
    api_id: 123456
    api_hash: "your_api_hash"
    session_name: "teleapi"
    channels:
        - username: "example_channel"
          enabled: true
          sync_history: true
          history_limit: 1000
          filters:
              - "crypto-important"

filters:
    - name: "crypto-important"
      include_keywords:
          - "BTC"
          - "ETH"
          - "ETF"
      exclude_keywords:
          - "广告"
          - "推广"
      regex: []
      message_types:
          - "text"
          - "photo"

security:
    admin_api_key: "your_admin_api_key"
    allow_health_without_auth: true

outputs:
    api:
        enabled: true

    websocket:
        enabled: true

    webhooks:
        - name: "research-system"
          url: "https://example.com/webhook/telegram"
          secret: "your_webhook_secret"
          enabled: true
          events:
              - "message.created"
          channels:
              - "example_channel"
          filters:
              - "crypto-important"
          retry:
              max_attempts: 3
              backoff_seconds:
                  - 5
                  - 30
                  - 120

database:
    url: "sqlite:///./data/teleapi.db"
```

---

## 12. MVP 范围

## 12.1 v0.1 必须实现

1. Telethon 用户账号登录。
2. YAML 配置加载。
3. 配置级 `admin_api_key` 鉴权。
4. 多频道配置。
5. 单频道 / 多频道历史消息同步。
6. 新消息实时监听。
7. 消息写入 SQLite。
8. REST API 查询频道列表。
9. REST API 查询频道消息。
10. Webhook 推送 `message.created`。
11. Webhook 失败重试。
12. 基础关键词过滤。
13. 轻量后台管理界面。
14. Docker Compose 部署。
15. README 快速开始文档。

---

## 12.2 v0.1 可以暂缓

1. WebSocket 实时推送。
2. 复杂前端管理后台，例如多用户、角色权限、可视化拖拽配置、团队协作后台。
3. PostgreSQL 支持。
4. 消息全文搜索。
5. 媒体文件下载。
6. 多用户权限系统。
7. AI 摘要和分类。
8. 可视化过滤规则配置。

---

## 13. 版本规划

### v0.1：核心可用版

目标：完成 Telegram Channel → API / Webhook 的基础闭环。

包含：

- 登录
- 配置频道
- 同步历史消息
- 监听新消息
- 存储
- API 查询
- Webhook 推送
- 基础过滤

---

### v0.2：实时和稳定性增强

目标：提升实时消费和运行稳定性。

包含：

- WebSocket 支持
- 更完善的失败重试
- 同步任务状态 API
- Webhook 推送日志查询
- 更完善的错误处理
- 更好的日志系统

---

### v0.3：存储和查询增强

目标：提升数据查询能力。

包含：

- PostgreSQL 支持
- 消息全文搜索
- 更多消息类型支持
- 媒体元信息增强
- 分页游标优化

---

### v0.4：轻量管理界面

目标：降低使用门槛。

包含：

- 频道列表页面
- 消息列表页面
- 同步状态页面
- Webhook 状态页面
- 配置检查页面

---

## 14. 成功指标

### v0.1 成功标准

1. 用户可以在 10 分钟内通过 Docker Compose 启动项目。
2. 用户可以成功登录 Telegram 账号。
3. 用户可以配置至少 1 个频道并同步历史消息。
4. 用户可以通过 REST API 查询频道消息。
5. 新消息可以自动写入数据库。
6. 新消息可以通过 Webhook 推送到外部系统。
7. 基础关键词过滤可以正常工作。
8. Webhook 推送失败时可以自动重试。

---

## 15. 风险与约束

## 15.1 Telegram API 限制

Telegram 对 API 调用存在限流和风控机制。

应对策略：

- 控制历史同步速度。
- 捕获 FloodWait 异常。
- 支持断点续传。
- 避免频繁登录和重复同步。

---

## 15.2 用户账号安全

TeleAPI 使用用户 Telegram 账号登录，需要保护 session 文件。

应对策略：

- session 文件本地保存。
- 不上传云端。
- 文档中明确安全风险。
- Docker volume 持久化 session。

---

## 15.3 API 访问安全

TeleAPI 部署后如果暴露到公网，存在被他人盗用 API、拉取消息、触发同步任务、访问后台页面的风险。

v0.1 必须提供配置密钥保护机制。

安全策略：

- 配置文件中必须设置 `security.admin_api_key`。
- 除 `/health` 外，所有 API 都必须校验 `admin_api_key`。
- 后台管理界面也必须通过 `admin_api_key` 访问。
- WebSocket 连接必须携带有效 `admin_api_key`。
- 密钥错误时返回 `403 Forbidden`。
- 未携带密钥时返回 `401 Unauthorized`。
- `/health` 不返回频道、账号、session、Webhook 等敏感信息。
- Docker 示例中必须提示用户修改默认密钥。
- 如果检测到默认密钥或空密钥，服务应拒绝启动。

推荐请求方式：

```http
Authorization: Bearer your_admin_api_key
```

兼容请求方式：

```http
X-TeleAPI-Key: your_admin_api_key
```

不建议把 API Key 放在 URL query 中，避免被日志记录。

---

## 15.4 频道权限问题

用户只能同步自己有权限访问的频道。

应对策略：

- 频道不可访问时返回明确错误。
- 不尝试绕过权限限制。
- 不支持抓取用户未订阅或无权限频道。

---

## 15.5 Webhook 接收方不稳定

外部系统可能超时、返回错误或不可用。

应对策略：

- 设置请求超时。
- 记录推送日志。
- 支持重试。
- 超过最大重试次数后标记失败。

---

## 16. 开源项目 README 核心文案

### 项目标题

```md
# TeleAPI

A lightweight Telegram channel API gateway.
```

### 项目介绍

```md
TeleAPI turns your subscribed Telegram channels into queryable APIs, webhooks, and realtime streams.

It uses your Telegram account session to sync channel history, listen for new messages, normalize messages into structured data, and expose them through REST APIs and webhook events.
```

### 中文介绍

```md
TeleAPI 是一个轻量级 Telegram 频道 API 网关。

它可以将你已订阅的 Telegram 频道内容同步为结构化数据，并通过 REST API、Webhook 和 WebSocket 对外提供访问能力，适合用于投研系统、新闻系统、自动化工作流和数据采集场景。
```

---

## 17. 最终产品边界

TeleAPI 当前阶段不追求成为通用数据平台，而是聚焦一个清晰问题：

> 如何把我已经订阅的 Telegram 频道，稳定地转换成外部系统可调用、可推送、可实时消费的数据接口。

这也是 v0.1 的核心判断标准：

```txt
能不能稳定监听指定 Telegram 频道？
能不能同步历史消息？
能不能结构化存储？
能不能通过配置密钥保护 API 和后台？
能不能提供轻量后台查看运行状态？
能不能通过 API 查询？
能不能通过 Webhook 推送？
能不能用配置规则过滤？
```

只要这条链路打通，TeleAPI 就具备了作为开源工具的第一阶段价值。
