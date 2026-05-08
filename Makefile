.PHONY: dev dev-backend dev-frontend install build clean

dev:
	@trap 'kill 0' EXIT; \
	$(MAKE) dev-backend & \
	$(MAKE) dev-frontend & \
	wait

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
