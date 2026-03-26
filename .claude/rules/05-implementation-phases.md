# Implementation Phases

## Phase 1: Setup (1-2 hours)

### Goals
- Create folder structure
- Initialize all configuration files
- Set up git repository
- Create README files for each service

### Tasks

1. **Root folder structure**
   ```bash
   mkdir -p claude-code-analyzer
   cd claude-code-analyzer
   mkdir -p monitor/src backend/src frontend/src frontend/public shared data
   ```

2. **Git initialization**
   ```bash
   git init
   git config user.name "Your Name"
   git config user.email "your@email.com"
   ```

3. **Create root files**
   - `README.md` - Project overview, quick start, features
   - `CLAUDE.md` - Developer context (points to rules/)
   - `.gitignore` - Python, Node, data, IDE files
   - `docker-compose.yml` - Optional service orchestration

4. **Create monitor service files**
   - `monitor/pyproject.toml`
   - `monitor/README.md`
   - `monitor/src/__init__.py`

5. **Create backend service files**
   - `backend/pyproject.toml`
   - `backend/.env.example`
   - `backend/README.md`
   - `backend/src/__init__.py`

6. **Create frontend service files**
   - `frontend/package.json`
   - `frontend/vite.config.js`
   - `frontend/index.html`
   - `frontend/README.md`
   - `frontend/src/main.jsx`
   - `frontend/public/`

7. **Create shared files**
   - `shared/db_schema.sql`
   - `shared/constants.py`

8. **First commit**
   ```bash
   git add .
   git commit -m "feat: initial project setup"
   ```

### Verification
- All directories exist
- All config files present
- Git repository initialized
- Can run `uv sync` in monitor/ and backend/ without errors

---

## Phase 2: Database & Monitor Service (2-3 hours)

### Goals
- Create SQLite database schema
- Implement database layer (SQLAlchemy models)
- Implement file system monitoring
- Implement interaction logging
- Manually test with CLI fallback

### Tasks

1. **Create database schema** (`shared/db_schema.sql`)
   - sessions table
   - interactions table
   - errors table
   - code_metrics table
   - Indexes
   - (Reference: `rules/01-database-schema.md`)

2. **Implement monitor/src/db.py**
   - SQLAlchemy models (SessionModel, InteractionModel, ErrorModel, CodeMetricsModel)
   - Pydantic schemas
   - DatabaseManager class with CRUD operations
   - Connection pooling, error handling
   - (Reference: `rules/02-monitor-service.md`)

3. **Implement monitor/src/detector.py**
   - SessionDetector class
   - File system watching with Watchdog
   - Event emission (session_started, interaction_detected, session_ended)
   - (Reference: `rules/02-monitor-service.md`)

4. **Implement monitor/src/logger.py**
   - SessionLogger class
   - Subscribe to detector events
   - Compute interaction type classification
   - Detect code modifications
   - Compute code metrics (Python: ast parsing)
   - Calculate acceptance rate
   - (Reference: `rules/02-monitor-service.md`)

5. **Implement monitor/src/utils.py**
   - `extract_language(file_path)` - Determine language from extension
   - `calculate_nesting_depth(code, language)` - AST analysis
   - `parse_error_message(error_text)` - Error classification
   - `estimate_tokens(text)` - Rough token count

6. **Implement monitor/src/main.py**
   - Database initialization
   - Detector startup
   - Logger startup
   - Signal handling (Ctrl+C graceful shutdown)
   - CLI argument parsing for `--log-interaction` fallback
   - (Reference: `rules/02-monitor-service.md`)

7. **Test monitor with CLI**
   ```bash
   cd monitor
   uv sync
   uv run python src/main.py --log-interaction "Write a hello world function" "def hello():\n    print('hello')"
   ```

8. **Verify database**
   ```bash
   sqlite3 ../data/sessions.db "SELECT COUNT(*) FROM sessions;"
   ```

9. **Commit**
   ```bash
   git add .
   git commit -m "feat: monitor service with database integration"
   ```

### Verification
- Database tables created and accessible
- Monitor starts without errors
- CLI `--log-interaction` works
- Data persists to SQLite
- Can query `data/sessions.db` directly

---

## Phase 3: Backend Service (2-3 hours)

### Goals
- Implement FastAPI app
- Create API endpoints (sessions, metrics, timeline)
- Implement database queries
- Implement aggregation functions
- Test endpoints with curl/Postman

### Tasks

1. **Implement backend/src/main.py**
   - FastAPI app initialization
   - CORS middleware setup
   - Health check endpoint
   - API router includes
   - Startup with Uvicorn
   - (Reference: `rules/03-backend-service.md`)

2. **Implement backend/src/db/models.py**
   - SQLAlchemy ORM models (same as monitor)
   - Ensure schema consistency with monitor
   - (Reference: `rules/01-database-schema.md`)

3. **Implement backend/src/db/queries.py**
   - QueryManager class
   - `get_all_sessions()` with filtering
   - `get_session_with_interactions()`
   - `get_session_stats()`
   - `get_quality_metrics()`
   - `get_error_analysis()`
   - `get_acceptance_metrics()`
   - `get_session_timeline()`
   - `get_historical_timeline()`
   - All with proper error handling
   - (Reference: `rules/03-backend-service.md`)

4. **Implement backend/src/api/sessions.py**
   - Pydantic response schemas
   - `GET /api/sessions` with filtering & pagination
   - `GET /api/sessions/{session_id}`
   - `GET /api/sessions/stats/summary`
   - (Reference: `rules/03-backend-service.md`)

5. **Implement backend/src/api/metrics.py**
   - `GET /api/metrics/quality`
   - `GET /api/metrics/errors`
   - `GET /api/metrics/acceptance`
   - Pydantic response schemas
   - (Reference: `rules/03-backend-service.md`)

6. **Implement backend/src/api/timeline.py**
   - `GET /api/timeline/session/{session_id}`
   - `GET /api/timeline/historical`
   - Pydantic response schemas
   - (Reference: `rules/03-backend-service.md`)

7. **Implement backend/src/utils/aggregations.py**
   - `calculate_quality_score()` - 0-1 score from metrics
   - `detect_error_patterns()` - Error analysis
   - `compute_rolling_average()` - Smooth trends
   - (Reference: `rules/03-backend-service.md`)

8. **Create backend/.env.example**
   - DATABASE_PATH
   - API_PORT
   - API_HOST
   - FRONTEND_ORIGIN

9. **Test backend endpoints**
   ```bash
   cd backend
   uv sync
   uv run python src/main.py
   
   # In another terminal:
   curl http://localhost:8000/health
   curl http://localhost:8000/api/sessions
   curl http://localhost:8000/api/sessions/stats/summary
   ```

10. **Commit**
    ```bash
    git add .
    git commit -m "feat: FastAPI backend with endpoints"
    ```

### Verification
- Backend starts without errors
- `/health` endpoint responds
- `/api/sessions` returns list (or empty if no data)
- All endpoints return proper JSON
- Swagger UI available at `/docs`

---

## Phase 4: Frontend Service (3-4 hours)

### Goals
- Create React project structure
- Build chart components
- Build filter components
- Build pages (Dashboard, Sessions)
- Integrate with backend APIs
- Verify data flows end-to-end

### Tasks

1. **Initialize React project**
   ```bash
   cd frontend
   npm install
   ```

2. **Implement frontend/src/api/client.js**
   - Axios instance with base URL
   - Error interceptors
   - API helper functions
   - (Reference: `rules/04-frontend-service.md`)

3. **Implement frontend/src/hooks/useSessions.js**
   - Fetch sessions with filters
   - Handle loading, error states
   - (Reference: `rules/04-frontend-service.md`)

4. **Implement frontend/src/hooks/useMetrics.js**
   - Fetch metrics from all endpoints
   - Aggregate data for charts
   - (Reference: `rules/04-frontend-service.md`)

5. **Implement chart components**
   - `frontend/src/components/Charts/Timeline.jsx` - Line chart
   - `frontend/src/components/Charts/Heatmap.jsx` - 2D heatmap
   - `frontend/src/components/Charts/ScatterPlot.jsx` - Scatter plot
   - (Reference: `rules/04-frontend-service.md`)

6. **Implement filter components**
   - `frontend/src/components/Filters/DateRange.jsx` - Date picker
   - `frontend/src/components/Filters/LanguageFilter.jsx` - Language select
   - (Reference: `rules/04-frontend-service.md`)

7. **Implement insights component**
   - `frontend/src/components/InsightsPanel.jsx` - Auto insights
   - (Reference: `rules/04-frontend-service.md`)

8. **Implement pages**
   - `frontend/src/pages/Dashboard.jsx` - Main dashboard
   - `frontend/src/pages/Sessions.jsx` - Sessions list
   - (Reference: `rules/04-frontend-service.md`)

9. **Implement App.jsx & routing**
   - React Router setup
   - Navigation bar
   - Routes to pages
   - (Reference: `rules/04-frontend-service.md`)

10. **Implement main.jsx & styles**
    - React DOM render
    - `frontend/src/styles/globals.css` - Global styles
    - (Reference: `rules/04-frontend-service.md`)

11. **Test frontend**
    ```bash
    cd frontend
    npm run dev
    # Opens http://localhost:5173
    ```

12. **Verify data flow**
    - Dashboard displays KPI cards
    - Filters work
    - Charts display data from backend
    - Session list is sortable
    - No console errors

13. **Commit**
    ```bash
    git add .
    git commit -m "feat: React dashboard with charts and filters"
    ```

### Verification
- Frontend starts without errors
- Dashboard loads
- KPI cards show correct values
- Charts render (Plotly)
- Filters work and update charts
- Session list displays all sessions
- Can click session row (if SessionDetail implemented)

---

## Phase 5: Integration & Polish (1-2 hours)

### Goals
- Test full end-to-end flow
- Fix any integration issues
- Polish documentation
- Create startup scripts
- Final cleanup

### Tasks

1. **End-to-end test**
   - Terminal 1: Start monitor
     ```bash
     cd monitor && uv run python src/main.py
     ```
   - Terminal 2: Start backend
     ```bash
     cd backend && uv run python src/main.py
     ```
   - Terminal 3: Start frontend
     ```bash
     cd frontend && npm run dev
     ```
   - Use monitor CLI to log test sessions
   - Verify data appears in dashboard

2. **Create startup script** (optional)
   - `run.sh` - Start all three services
   - Or use `docker-compose.yml`

3. **Update README files**
   - Root `README.md`: Overview, features, quick start
   - `monitor/README.md`: How to run, config options
   - `backend/README.md`: API documentation, how to run
   - `frontend/README.md`: Component structure, how to run

4. **Create CLAUDE.md** (already done in Phase 1)
   - Points to rules/ folder
   - Quick reference

5. **Final cleanup**
   - Remove debug logging
   - Add proper error messages
   - Ensure all code is documented
   - Check .gitignore completeness

6. **Final commits**
   ```bash
   git add .
   git commit -m "docs: update README and setup scripts"
   git commit -m "chore: final cleanup and polish"
   ```

7. **Create GitHub repository**
   - Push to GitHub
   - Add topics: full-stack, python, react, fastapi, analytics
   - Write compelling README for portfolio

### Verification
- All three services run together
- Monitor → Backend → Frontend data flow works
- No errors in console or terminal
- Dashboard shows real data
- Code is clean and documented
- README explains everything
- Can be cloned and run on another machine

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1 | 1-2 hrs | Project structure, configs |
| 2 | 2-3 hrs | Monitor service, database |
| 3 | 2-3 hrs | Backend API |
| 4 | 3-4 hrs | React dashboard |
| 5 | 1-2 hrs | Integration, polish, docs |
| **Total** | **9-14 hrs** | **Complete portfolio project** |

---

## When to Create Subagents

During any phase, if you encounter:

1. **Complex database optimization** → Database Optimization subagent
   - Slow queries, index tuning, query analysis
   - (See `rules/07-subagent-workflow.md`)

2. **Advanced charting** → Advanced Plotly Charts subagent
   - 3D charts, custom interactivity, animations
   - (See `rules/07-subagent-workflow.md`)

3. **Error handling & logging** → Error Handling subagent
   - Structured logging, error recovery, monitoring
   - (See `rules/07-subagent-workflow.md`)

4. **Testing** → Testing subagent
   - Unit tests, integration tests, E2E tests
   - (See `rules/07-subagent-workflow.md`)

---

## Commit Strategy

After each phase, make a commit:
```bash
git add .
git commit -m "feat: [phase name] - [what was accomplished]"
```

Example commits:
```
feat: phase-1 - project setup and configuration
feat: phase-2 - monitor service with database
feat: phase-3 - FastAPI backend with analytics endpoints
feat: phase-4 - React dashboard with charts and filters
docs: phase-5 - final polish and documentation
```

---

## Next: Phase 1 Instructions

To start Phase 1:

1. Open Claude Code
2. Say: "Let's start Phase 1: Setup. Create all folders and config files as specified in rules/05-implementation-phases.md"
3. Claude Code will create the structure
4. Review output and make first commit

Then proceed to Phase 2 when Phase 1 is complete.
