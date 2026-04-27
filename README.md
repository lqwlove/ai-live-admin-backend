# tk-live Admin Backend

独立后台管理 API，负责管理员登录、用户管理、AI token 消耗日志、TTS 消耗日志和仪表盘统计。

## 本地启动

本机也使用 PostgreSQL。默认连接串：

```env
DATABASE_URL=postgresql+psycopg://postgresql:你的密码@localhost:55443/ai_db
```

先创建数据库和用户：

```bash
createdb tk_live_admin
psql -d tk_live_admin -c "CREATE USER tk_live_admin WITH PASSWORD 'tk_live_admin';"
psql -d tk_live_admin -c "GRANT ALL PRIVILEGES ON DATABASE tk_live_admin TO tk_live_admin;"
```

```bash
cd admin-system/backend
cp .env.example .env
uv run uvicorn app.main:app --reload --port 8100
```

首次启动会在 PostgreSQL 中自动创建表和默认管理员：

- 用户名：`admin`
- 密码：`admin123`

生产环境请修改 `.env` 中的 `SECRET_KEY`、`DATABASE_URL`、`INITIAL_ADMIN_PASSWORD` 和 `INTEGRATION_API_KEY`。

## 预留接入接口

直播工具后续可用 `X-Integration-Api-Key` 写入消耗日志：

- `POST /api/integration/ai-token-logs`
- `POST /api/integration/tts-logs`
# ai-live-admin-backend
