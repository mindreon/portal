# 常用命令入口。在 Git Bash / 终端里执行：make up
# 每一行前面的 @ 表示不把命令本身打印出来，只看结果。

.PHONY: up down logs dev-api dev-web test-api install-api install-web

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

# 本地开发后端：需要先 make install-api
dev-api:
	cd apps/api && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 本地开发前端：需要先 make install-web
dev-web:
	cd apps/web && npm run dev

install-api:
	cd apps/api && uv sync --all-extras

install-web:
	cd apps/web && npm install

test-api:
	cd apps/api && uv run pytest -q
