# Claude Code Analyzer

A full-stack analytics system that monitors Claude Code sessions locally, computes metrics, and displays interactive dashboards.

## Architecture

Three independent services communicating through a shared SQLite database:

```
monitor/    →  SQLite DB  →  backend/  →  frontend/
(collect)      (shared)      (API)        (dashboard)
```

- **Monitor** — Python service that watches `.claude` files and logs session data
- **Backend** — FastAPI server exposing analytics REST APIs
- **Frontend** — React dashboard with interactive charts

## Tech Stack

| Service | Stack |
|---------|-------|
| Monitor | Python 3.9+, SQLAlchemy, Watchdog, Pydantic, uv |
| Backend | Python 3.9+, FastAPI, Uvicorn, SQLAlchemy, uv |
| Frontend | React 18, Vite, Plotly.js, Axios, Tailwind CSS |

## Getting Started

### Monitor (data collection)
```bash
cd monitor && uv sync && uv run python src/main.py
```

### Backend (API server)
```bash
cd backend && uv sync && uv run python src/main.py
```

### Frontend (dashboard)
```bash
cd frontend && npm install && npm run dev
```

Dashboard available at `http://localhost:5173`

## License

MIT
