# Agentic QA

AI-powered testing platform with natural-language tests and self-healing execution.  
Epic Brief: `spec:f7074a65-1009-4074-80e5-6cfa35a2908f/5ab786c7-4a77-454f-8235-b825b7378111`

## Tech stack

- **Frontend:** Next.js 15.5, React 19, TypeScript 5.7+, Tailwind CSS 3.4+
- **Backend:** FastAPI 0.128+, Python 3.12, Pydantic 2.10+
- **Deployment:** Railway

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- Git

## Local development

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with your configuration
npm run dev
```

Runs at [http://localhost:3000](http://localhost:3000).

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python -m uvicorn app.main:app --reload
```

Use `python -m uvicorn` so the same Python that has the packages runs the server (avoids "uvicorn not recognized" when Scripts is not on PATH). If port 8000 is in use, stop the process or run with `--port 8001`.

Runs at [http://localhost:8000](http://localhost:8000). API docs at [http://localhost:8000/docs](http://localhost:8000/docs). Health check at [http://localhost:8000/health](http://localhost:8000/health).

## Project structure

```
agentic-qa/
├── frontend/     Next.js app (App Router, Tailwind)
├── backend/      FastAPI app (uvicorn)
└── README.md
```

Environment variables are documented in `frontend/.env.example` and `backend/.env.example`.

### Database (NeonDB)

1. Create a Neon project at [neon.tech](https://neon.tech) or use the Neon CLI.
2. Copy the connection string (format: `postgresql://user:pass@host/db?sslmode=require`).
3. Add to `backend/.env` and `frontend/.env.local`:
   ```
   DATABASE_URL=your_neon_connection_string
   ```
4. Run migrations:
   ```bash
   cd backend
   python scripts/run_migrations.py
   ```

### Redis

**Local development (recommended if Railway Redis times out from your network):**

1. Start Redis in Docker:
   ```bash
   docker run -d -p 6379:6379 --name agentic-qa-redis redis
   ```
2. In `backend/.env`:
   ```
   REDIS_URL=redis://localhost:6379
   ```

**Railway Redis (for production or when reachable):**

1. Add a Redis service in your Railway project.
2. Copy `REDIS_URL` to `backend/.env` for local dev, or it auto-injects in production.
3. If you get connection/SSL timeouts, use local Redis above instead.

**Worker (run execution + live streaming):**

```bash
cd backend
python scripts/run_worker.py
```

## Linting

- **Frontend:** From `frontend/`, run `npm run lint` (ESLint 8 with `eslint-config-next`).
- **Backend:** No lint config in MVP.

## Testing

**Backend (pytest):**

```bash
cd backend
# With venv activated:
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

Tests live in `backend/tests/` (e.g. `test_main.py` for the health endpoint).

## Deployment (Railway)

Railway auto-detects the frontend from `frontend/package.json` and the backend from `backend/Dockerfile`. Configure environment variables in the Railway dashboard for each service. No `railway.json` is required for MVP.

## Next steps

- **T2:** ✅ Database schema and NeonDB connections
- **T3:** ✅ Redis Streams setup, run queue, worker, SSE
