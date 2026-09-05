# Portal 内部业务系统

公司内部用的业务管理系统。第一版覆盖 **飞书登录、合同、发票**，后面加模块时按同样的目录往下长。

这是一个 **monorepo**（单一仓库）：前端、后端、部署配置都在同一个 Git 仓库里。好处是一次克隆、一次 `docker compose up` 就能跑起来，前后端接口也不容易对不齐。

## 它怎么组成

```text
浏览器  →  Caddy(:80)
              ├─ /api/*  →  FastAPI (Python + uv)
              └─ 其它    →  Next.js
                              ↓
                         PostgreSQL
```

| 目录 | 作用 |
| --- | --- |
| `apps/api` | 后端。FastAPI 提供登录、合同、发票接口 |
| `apps/web` | 前端。Next.js 管理后台 |
| `deploy/Caddyfile` | 把前后端合成同一个网站，避免跨域 |
| `docker-compose.yml` | 一键拉起数据库、后端、前端、反向代理 |
| `DESIGN.md` | 前端视觉规范（单色工作台、黑底主按钮、合同/发票独立模块） |

登录只用飞书企业自建应用（OAuth）。本地还没配飞书时，可以打开「开发登录」先把业务页面跑通。视觉以 [DESIGN.md](./DESIGN.md) 为准，先改文档再改样式。

## 一键部署（推荐）

机器上需要 Docker 和 Docker Compose。

```bash
cp .env.example .env
# 至少改 SECRET_KEY；配飞书则填 FEISHU_APP_ID / FEISHU_APP_SECRET
docker compose up -d --build
```

浏览器打开 [http://localhost](http://localhost)。默认开启开发登录，方便第一次验收。

停止：

```bash
docker compose down
```

数据保存在项目目录下的 `data/postgres/` 和 `data/uploads/`，即使删除容器也不会丢失。清理数据前请先备份并删除对应目录。

合同上传后会一页一页交给通义千问理解（默认 `qwen3.7-plus`），抽取编号、甲乙方、金额、日期、付款比例等草稿要素；信息齐了就停止翻页，不会用正则去匹配正文。电子页只发该页文本，扫描页才发缩小后的图。在 `.env` 里同时填：

- `QWEN_API_KEY`：百炼 API Key
- `QWEN_BASE_URL`：`https://dashscope.aliyuncs.com/compatible-mode/v1`（北京；新加坡用 `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`）
- `QWEN_OCR_MODEL`：默认 `qwen3.7-plus`

失败不会回退到其它引擎，请手工填写。识别结果仍是草稿，必须在页面上核对。

Caddy、Postgres、Node、uv 都走公司 Harbor 镜像。当前没有旧库数据，直接 `docker compose up -d --build` 即可。Postgres 18 要把目录挂到 `/var/lib/postgresql`（不是 16 用的 `/var/lib/postgresql/data`）。

## GitHub Actions 自动部署

`.github/workflows/ci.yml` 会在 **Pull Request** 以及 **push 到 `main`** 时检查前后端代码。只有 `main` 上的 **push** 让 CI 成功之后，`.github/workflows/deploy.yml` 才会通过 SSH 部署到阿里云服务器的 `/srv/portal`，并重新构建和启动 Docker Compose。功能分支和 PR 的 CI 不会触发部署。

在仓库 Settings → Secrets and variables → Actions 中配置：

- `ALIYUN_HOST`：服务器公网 IP 或域名
- `ALIYUN_USER`：SSH 用户名
- `ALIYUN_SSH_KEY`：对应用户的私钥（完整内容）
- `ALIYUN_PORT`：SSH 端口，可选，默认 `22`

服务器需提前在 `/srv/portal` 克隆本仓库，并确保该目录下已有生产环境 `.env` 文件。

## 配置飞书登录

1. 打开 [飞书开放平台](https://open.feishu.cn/app)，创建 **企业自建应用**。
2. 在「凭证与基础信息」复制 App ID、App Secret，填进 `.env`。
3. 在「安全设置」添加重定向 URL，必须和 `.env` 里的 `FEISHU_REDIRECT_URI` **完全一致**。  
   本机 Docker 默认是：`http://localhost/api/v1/auth/feishu/callback`
4. 在「权限管理」申请登录需要的权限（默认 `auth:user.id:read`），然后发布应用，并给同事开通可用性。
5. 公司正式环境把 `AUTH_ALLOW_DEV_LOGIN` 改成 `false`，`COOKIE_SECURE` 在 HTTPS 下改成 `true`。

飞书授权流程可以记成三步：

1. 用户跳到飞书授权页，飞书带回一次性 `code`
2. 后端用 `code` 换 `user_access_token`
3. 后端拉取用户姓名 / `open_id`，在自己的 `users` 表落库，并写下登录 Cookie

官方文档：

- [获取授权码](https://open.feishu.cn/document/authentication-management/access-token/obtain-oauth-code)
- [获取 user_access_token](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/authentication-management/access-token/get-user-access-token)
- [获取用户信息](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/authen-v1/user_info/get)

## 本地开发（不用 Docker）

后端用 [uv](https://docs.astral.sh/uv/) 管理 Python 依赖，前端用 npm。Python 包默认从阿里云镜像安装（`https://mirrors.aliyun.com/pypi/simple`）。本机若还没装 uv，可以用同一镜像：

```bash
python3 -m pip install -U uv -i https://mirrors.aliyun.com/pypi/simple
```

```bash
# 后端
cd apps/api
uv sync --all-extras
# 本地可用 SQLite，免装 Postgres
export DATABASE_URL=sqlite:///./portal.db
export AUTH_ALLOW_DEV_LOGIN=true
uv run uvicorn app.main:app --reload --port 8000

# 另开一个终端跑前端
cd apps/web
npm install
npm run dev
```

打开 [http://localhost:3000](http://localhost:3000)。前端会把 `/api` 代理到 `http://localhost:8000`。

跑后端测试：

```bash
cd apps/api
uv run pytest -q
```

也可以在仓库根目录执行 `make test-api`、`make dev-api`、`make dev-web`。

## 以后怎么加新模块

以后加「付款」「客户档案」等，建议按这个顺序，不要先改前端：

1. 在 `apps/api/app/models/` 增加表
2. 用 Alembic 生成迁移：`cd apps/api && uv run alembic revision --autogenerate -m "add xxx"`
3. 在 `apps/api/app/schemas/` 写请求和响应
4. 在 `apps/api/app/modules/` 写路由，并在 `app/main.py` 里 `include_router`
5. 在 `apps/web/src/app/` 增加对应页面

这样每个业务都是「一张表 + 一组接口 + 一组页面」，互不踩脚。

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/v1/auth/config` | 登录页该显示哪些按钮 |
| GET | `/api/v1/auth/feishu/login` | 返回飞书授权地址 |
| GET | `/api/v1/auth/feishu/callback` | 飞书回调，写登录 Cookie |
| POST | `/api/v1/auth/dev-login` | 本地开发登录 |
| GET | `/api/v1/auth/me` | 当前用户 |
| POST | `/api/v1/auth/logout` | 退出 |
| * | `/api/v1/contracts` | 合同增删改查 |
| * | `/api/v1/invoices` | 发票增删改查 |

登录态放在名为 `portal_session` 的 **HttpOnly Cookie** 里，前端 JavaScript 读不到，可以减少 XSS 偷令牌的风险。
