# Architecture & Folder Structure

## System Overview

```
claude-code-analyzer/
├── README.md                      # Main project documentation
├── CLAUDE.md                      # Developer context (this file references rules/)
├── .gitignore
├── docker-compose.yml             # Optional: run all services together
│
├── monitor/                       # Python service: detects & logs Claude Code
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── README.md
│   └── src/
│       ├── __init__.py
│       ├── main.py               # Entry point, orchestration
│       ├── detector.py            # Watch for .claude files, emit events
│       ├── logger.py              # Log interactions, compute basic metrics
│       ├── db.py                  # SQLAlchemy models, CRUD operations
│       └── utils.py               # Helper functions (complexity analysis, etc)
│
├── backend/                       # Python FastAPI service: analytics APIs
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── README.md
│   ├── .env.example
│   └── src/
│       ├── __init__.py
│       ├── main.py               # FastAPI app, CORS, health check
│       ├── api/
│       │   ├── __init__.py
│       │   ├── sessions.py       # GET /api/sessions, /api/sessions/{id}
│       │   ├── metrics.py         # GET /api/metrics/quality, /metrics/errors
│       │   └── timeline.py        # GET /api/timeline/session, /timeline/historical
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py          # SQLAlchemy ORM models (shared with monitor)
│       │   └── queries.py         # Database query functions
│       └── utils/
│           ├── __init__.py
│           └── aggregations.py    # Statistical calculations, quality scoring
│
├── frontend/                      # React service: dashboard & visualizations
│   ├── package.json
│   ├── vite.config.js
│   ├── README.md
│   └── src/
│       ├── main.jsx              # Entry point
│       ├── App.jsx                # Router, layout
│       ├── pages/
│       │   ├── Dashboard.jsx      # Main dashboard with charts & filters
│       │   ├── Sessions.jsx       # List of all sessions
│       │   └── SessionDetail.jsx  # Single session details (optional)
│       ├── components/
│       │   ├── Charts/
│       │   │   ├── Timeline.jsx   # Line chart wrapper
│       │   │   ├── Heatmap.jsx    # 2D heatmap
│       │   │   └── ScatterPlot.jsx# Scatter plot
│       │   ├── Filters/
│       │   │   ├── DateRange.jsx  # Date picker
│       │   │   └── LanguageFilter.jsx # Language multi-select
│       │   └── InsightsPanel.jsx  # Auto-generated insights
│       ├── hooks/
│       │   ├── useSessions.js     # Fetch sessions from API
│       │   └── useMetrics.js      # Fetch metrics from API
│       ├── api/
│       │   └── client.js          # Axios instance, API helper functions
│       └── styles/
│           └── globals.css        # Global styles, Tailwind setup
│
├── shared/                        # Shared utilities between services
│   ├── db_schema.sql             # SQLite DDL (CREATE TABLE statements)
│   └── constants.py              # Shared constants (languages, error types, etc)
│
└── data/                          # Auto-created on first run
    └── sessions.db                # SQLite database (shared between monitor & backend)
```

## Service Separation

### Monitor Service
- **Responsibility**: Detect Claude Code sessions, log interactions, write to SQLite
- **Independent**: Doesn't depend on backend or frontend
- **Runs**: Continuously in background on user's machine
- **Output**: Populated SQLite database

### Backend Service
- **Responsibility**: Expose APIs for analytics, compute aggregated metrics
- **Input**: Reads from SQLite database
- **Output**: JSON responses to frontend
- **Runs**: On localhost:8000
- **Independent**: Doesn't depend on monitor or frontend (but needs database from monitor)

### Frontend Service
- **Responsibility**: Display interactive charts, filters, insights
- **Input**: Fetches from backend APIs
- **Output**: HTML/CSS/JS rendered in browser
- **Runs**: On localhost:5173
- **Independent**: Doesn't depend on monitor or backend (but needs backend running)

## Data Flow

```
Claude Code Session
        ↓
  Monitor Service
        ↓
  SQLite Database (sessions.db)
        ↓
  Backend Service (reads DB)
        ↓
  API Responses (JSON)
        ↓
  Frontend Service (visualizes)
        ↓
  Interactive Dashboard
```

## Configuration Files

### Root Level
- **README.md**: Project overview, quick start, features
- **CLAUDE.md**: Developer context, quick reference
- **.gitignore**: Exclude Python, Node, data, IDE files
- **docker-compose.yml**: Optional service orchestration

### Monitor
- **pyproject.toml**: Dependencies (SQLAlchemy, Watchdog, Pydantic)
- **README.md**: How to run, what it monitors, configuration options

### Backend
- **pyproject.toml**: Dependencies (FastAPI, Uvicorn, SQLAlchemy)
- **.env.example**: Environment variables template (DATABASE_PATH, PORT)
- **README.md**: API documentation, how to run

### Frontend
- **package.json**: Dependencies (React, Vite, Plotly, Axios)
- **vite.config.js**: Dev server setup, proxy to backend
- **README.md**: Component structure, how to run

## Key Design Principles

1. **Separation of Concerns**: Each service has a single responsibility
2. **Loose Coupling**: Services interact only through database (monitor→backend) or API (backend→frontend)
3. **High Cohesion**: Related code is in the same module
4. **Testability**: Each service can be tested independently
5. **Scalability**: Easy to add new features (e.g., WebSocket real-time updates, multi-agent comparison)
6. **Portfolio Quality**: Clean code, good documentation, professional structure

## Environment Variables

### Monitor
- `DATABASE_PATH`: Path to SQLite database (default: `../data/sessions.db`)
- `WATCH_DIRECTORY`: Root directory to monitor (default: current working directory)

### Backend
- `DATABASE_PATH`: Path to SQLite database (default: `../data/sessions.db`)
- `API_PORT`: Port to run API server (default: 8000)
- `API_HOST`: Host to bind to (default: 127.0.0.1)
- `FRONTEND_ORIGIN`: CORS origin for frontend (default: http://localhost:5173)

### Frontend
- `VITE_API_URL`: Backend API base URL (default: http://localhost:8000)

## First-Time Setup Checklist

- [ ] Create root folder structure (monitor/, backend/, frontend/, shared/, data/)
- [ ] Create pyproject.toml in monitor/ and backend/
- [ ] Create package.json in frontend/
- [ ] Create shared/db_schema.sql
- [ ] Create README.md for each service
- [ ] Create .env files (using .env.example templates)
- [ ] Initialize git repository, create .gitignore
- [ ] Create docker-compose.yml for convenient multi-service startup

## Directory Naming & File Conventions

- **Folders**: lowercase with underscores (monitor, backend, frontend, api, db)
- **Python files**: lowercase with underscores (main.py, detector.py, db.py)
- **React components**: PascalCase (Dashboard.jsx, DateRange.jsx, Timeline.jsx)
- **React hooks**: camelCase with "use" prefix (useSessions.js, useMetrics.js)
- **API routes**: lowercase with hyphens (/api/sessions, /api/code-metrics)
- **Database tables**: snake_case lowercase (sessions, interactions, code_metrics)
- **Database columns**: snake_case lowercase (session_id, created_at, interaction_type)

## Dependencies Management

**Python**: Use `uv` instead of `pip`
- Each service has its own `pyproject.toml`
- Run `uv sync` in service directory to install dependencies
- Commit `uv.lock` to version control

**Node**: Use `npm` for frontend
- Single `package.json` in frontend/ directory
- Run `npm install` to install dependencies
- Commit `package-lock.json` to version control

## Shared Database Location

All three services access the same SQLite database at `../data/sessions.db`:
- **Monitor**: Writes to it
- **Backend**: Reads from it
- **Frontend**: Doesn't access directly (reads via backend API)

The `data/` folder is created automatically on first run. Don't commit `sessions.db` to git (add to .gitignore).
