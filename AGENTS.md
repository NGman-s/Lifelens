# Repository Guidelines

## Project Structure & Module Organization
`frontend/` contains the Uni-app client built with Vue 3, Vite, and Pinia. Main code lives in `frontend/src/`: `pages/` for routes, `components/` for reusable UI, `store/` for state, `utils/` for API/image/permission helpers, and `static/` for assets. `backend/` contains the FastAPI service: `main.py` is the entrypoint, `services/vision_service.py` handles model calls, `utils/cleanup.py` manages file cleanup, and `test_api.py` is the current smoke test. Root deployment files include `docker-compose.yml`, `nginx.conf`, and the README docs. Runtime uploads go to `backend/uploads/` and are gitignored.

## Build, Test, and Development Commands
- `cd backend && pip install -r requirements.txt` installs Python dependencies.
- `cd backend && python main.py` starts the API on `http://localhost:8080`.
- `cd frontend && npm install` installs frontend dependencies.
- `cd frontend && npm run dev:h5 -- --host` runs the H5 development build locally.
- `cd frontend && npm run build:h5` creates the production H5 bundle.
- `docker compose up -d --build` builds and runs the full stack behind Nginx.

## Coding Style & Naming Conventions
Follow the style already present in each area: 4-space indentation for Python and 2 spaces for Vue, JavaScript, and JSON. Keep Python modules in `snake_case`; use `PascalCase` for Vue components such as `ResultOverlay.vue`; keep page folders lowercase, for example `src/pages/history/`. Centralize network changes in `frontend/src/utils/request.js`. No ESLint, Prettier, Black, or Ruff config is committed, so match surrounding code and keep diffs small.

## Testing Guidelines
Backend testing is currently a smoke test: run `python backend/test_api.py` while the API is running, with `backend/sample_food.jpg` available. When changing backend logic, add narrow tests or reproducible manual steps alongside the change. Frontend changes should be verified in H5 and, for camera/upload/permission flows, on the intended device target. There is no enforced coverage threshold yet.

## Commit & Pull Request Guidelines
Recent history mostly follows Conventional Commit prefixes such as `feat:`, `fix:`, and `docs:`. Prefer `type: short imperative summary` for new commits. Pull requests should describe scope, list the commands or manual checks performed, call out any config changes, and include screenshots or recordings for UI updates.

## Configuration & Security
Store secrets in `.env`, especially `DASHSCOPE_API_KEY` and optional backend settings such as `DASHSCOPE_BASE_URL` or `CORS_ALLOW_ORIGINS`. Do not commit `.env`, generated uploads, or build artifacts. For local non-Docker runs, keep the backend host in `frontend/src/utils/request.js` aligned with the API you are testing.
