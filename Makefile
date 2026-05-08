.PHONY: dev dev-backend dev-frontend dev-stop install build clean

dev: dev-stop
	@trap 'kill 0' EXIT; \
	$(MAKE) dev-backend & \
	$(MAKE) dev-frontend & \
	wait

dev-stop:
	@-lsof -ti :8080 | xargs kill 2>/dev/null; true
	@-lsof -ti :5173 | xargs kill 2>/dev/null; true

dev-backend:
	uv run uvicorn teleapi.main:app --host 0.0.0.0 --port 8080 --reload

dev-frontend:
	cd frontend && npm run dev

install:
	uv sync
	cd frontend && npm install

build:
	cd frontend && npm run build

clean:
	rm -rf frontend/dist frontend/node_modules/__vite
