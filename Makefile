# PEERLESS.AI — local development helpers
# Usage: make <target>

PYTHON   := C:/Users/ahmed/AppData/Local/Programs/Python/Python314/python.exe
BACKEND  := apps/backend
FRONTEND := apps/frontend

.PHONY: up down logs ps psql redis-cli backend frontend migrate seed-standards

## ── Infrastructure ────────────────────────────────────────────────────────────

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

psql:
	docker compose exec postgres psql -U peerless -d peerless

redis-cli:
	docker compose exec redis redis-cli

## ── Backend ───────────────────────────────────────────────────────────────────

backend:
	cd $(BACKEND) && PYTHONPATH=src $(PYTHON) -m uvicorn peerless.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	cd $(BACKEND) && PYTHONPATH=src $(PYTHON) -m alembic upgrade head

seed-standards:
	cd $(BACKEND) && PYTHONPATH=src $(PYTHON) -m peerless.verification.standards seed

## ── Frontend ──────────────────────────────────────────────────────────────────

frontend:
	cd $(FRONTEND) && npm run dev

## ── Tests ─────────────────────────────────────────────────────────────────────

test-backend:
	cd $(BACKEND) && PYTHONPATH=src $(PYTHON) -m pytest tests/ -q

## ── Checkpoints ───────────────────────────────────────────────────────────────

checkpoint-1:
	bash scripts/checkpoint_1.sh

checkpoint-2:
	bash scripts/checkpoint_2.sh
