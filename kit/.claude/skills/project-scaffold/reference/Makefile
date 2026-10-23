# Mọi lệnh đều chạy trong Docker — máy chỉ cần Docker Desktop.
-include .env
export
COMPOSE := docker compose
PM := python3 .claude/tools/pm.py
.DEFAULT_GOAL := help

.PHONY: help up down restart logs ps build deps lint lint-be lint-fe test test-unit test-unit-be \
        test-unit-fe test-integration test-api test-e2e migrate migration share share-ngrok share-stop \
        board prod-tunnel-up prod-tunnel-down

help: ## Liệt kê các lệnh
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

up: ## Bật ứng dụng (http://localhost:8080)
	$(COMPOSE) up -d --build --wait
	@echo "✅ Ứng dụng: http://localhost:$${APP_PORT:-8080}  |  API docs: http://localhost:$${APP_PORT:-8080}/api/docs"

down: ## Tắt ứng dụng (GIỮ NGUYÊN dữ liệu)
	$(COMPOSE) down

restart: down up ## Khởi động lại

logs: ## Xem log (Ctrl+C để thoát)
	$(COMPOSE) logs -f --tail=100

ps: ## Trạng thái các container
	$(COMPOSE) ps

build: ## Build lại image (sau khi sửa requirements*.txt hoặc Dockerfile)
	$(COMPOSE) build

deps: ## Cài lại thư viện frontend theo bun.lock
	$(COMPOSE) run --rm --no-deps frontend bun install --frozen-lockfile

lint: lint-be lint-fe ## Kiểm tra code + luật kiến trúc

lint-be:
	$(COMPOSE) run --rm --no-deps backend sh -c "ruff check . && lint-imports"

lint-fe:
	$(COMPOSE) run --rm --no-deps frontend bun run typecheck

test: lint test-unit test-api test-e2e ## Chạy TOÀN BỘ kiểm tra

test-unit: test-unit-be test-unit-fe ## Unit test backend + frontend (bắt buộc, có ngưỡng coverage)

test-unit-be:
	$(COMPOSE) run --rm --no-deps backend pytest tests/unit --cov=app --cov-report=term-missing

test-unit-fe:
	$(COMPOSE) run --rm --no-deps frontend bun test --coverage

test-integration: ## Test repository với Postgres thật
	$(COMPOSE) up -d --wait db redis
	$(COMPOSE) run --rm backend pytest tests/integration -m integration

test-api: test-integration ## Integration test + Hurl test API qua Traefik
	$(COMPOSE) up -d --build --wait
	$(COMPOSE) --profile test run --rm hurl

test-e2e: ## Playwright test giao diện (desktop + mobile)
	$(COMPOSE) up -d --build --wait
	$(COMPOSE) --profile test run --rm --build e2e

migrate: ## Chạy migration database
	$(COMPOSE) run --rm backend alembic upgrade head

migration: ## Tạo migration mới: make migration name=add_orders
	@test -n "$(name)" || (echo "Thiếu name=..." && exit 1)
	$(COMPOSE) run --rm backend alembic revision --autogenerate -m "$(name)"

share: ## Tạo link xem online bản dev (Cloudflare Quick Tunnel, miễn phí, không cần tài khoản)
	@$(COMPOSE) --profile share up -d tunnel
	@echo "Đang tạo link chia sẻ..."
	@for i in $$(seq 1 30); do \
	  url=$$($(COMPOSE) --profile share logs tunnel 2>/dev/null | grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1); \
	  if [ -n "$$url" ]; then echo "🌐 $$url"; $(PM) link share "$$url" >/dev/null 2>&1 || true; exit 0; fi; \
	  sleep 2; \
	done; echo "Không lấy được link — xem: docker compose --profile share logs tunnel"; exit 1

share-ngrok: ## Link chia sẻ bằng ngrok (cần NGROK_AUTHTOKEN, tuỳ chọn NGROK_DOMAIN trong .env)
	@test -n "$$NGROK_AUTHTOKEN" || grep -q '^NGROK_AUTHTOKEN=.\+' .env 2>/dev/null || (echo "Thiếu NGROK_AUTHTOKEN trong .env" && exit 1)
	$(COMPOSE) --profile share-ngrok up -d ngrok
	@sleep 4; $(COMPOSE) --profile share-ngrok logs ngrok | grep -Eo 'url=https://[^ ]+' | tail -1

share-stop: ## Tắt link chia sẻ
	-$(COMPOSE) --profile share --profile share-ngrok stop tunnel ngrok
	-$(PM) link share --remove >/dev/null 2>&1

board: ## Mở bảng điều hành dự án (http://localhost:4000)
	$(PM) serve --open

# ---------- Production chạy trên chính máy này + Cloudflare Tunnel (cơ chế A) ----------
PROD := $(COMPOSE) -f docker-compose.prod.yml --env-file .deploy/.env.prod

prod-tunnel-up: ## Chạy bản production + Cloudflare Tunnel trên máy này
	@test -f .deploy/.env.prod || (echo "Chưa có .deploy/.env.prod — chạy /deploy-setup" && exit 1)
	$(PROD) --profile tunnel up -d --build --wait

prod-tunnel-down: ## Tắt bản production trên máy này (GIỮ dữ liệu)
	$(PROD) --profile tunnel down
