# Code Style & Standards

## Philosophy

- **Readability first**: Code is read more often than written
- **Consistency**: Uniform style across all services
- **Self-documenting**: Clear names, comments where non-obvious
- **Professional**: Portfolio quality, production-ready code

## Python (Monitor & Backend)

### Naming Conventions

```python
# Classes: PascalCase
class SessionLogger:
    pass

class DatabaseManager:
    pass

# Functions/methods: snake_case
def create_session(language, project_name):
    pass

def get_all_sessions(filters, limit, offset):
    pass

# Constants: SCREAMING_SNAKE_CASE
SESSION_TIMEOUT_SECONDS = 300
SUPPORTED_LANGUAGES = ["python", "javascript", "typescript"]

# Private methods: _leading_underscore
def _compute_quality_score(metrics):
    pass

# Global variables: snake_case (avoid when possible)
database_path = "../data/sessions.db"
```

### Code Organization

```python
# 1. Imports at top (organized)
import os
from datetime import datetime
from typing import List, Optional, Dict

from sqlalchemy import Column, String
from pydantic import BaseModel

# 2. Constants
SESSION_TIMEOUT = 300
SUPPORTED_LANGUAGES = ["python", "javascript"]

# 3. Classes
class SessionModel:
    """SQLAlchemy model for sessions."""
    pass

class SessionLogger:
    """Logs Claude Code interactions."""
    pass

# 4. Functions
def create_session():
    pass

def log_interaction():
    pass
```

### Type Hints

Always use type hints:

```python
# Good
def create_session(
    language: str,
    project_name: str,
    file_path: str
) -> str:
    """Create a new session.
    
    Args:
        language: Programming language (python, javascript, etc)
        project_name: Name of the project
        file_path: Path to the primary file
    
    Returns:
        Session ID (UUID string)
    """
    pass

# Bad - no type hints
def create_session(language, project_name, file_path):
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_quality_score(
    cyclomatic_complexity: Optional[float],
    lines_of_code: Optional[int],
    has_type_hints: bool
) -> float:
    """Calculate code quality score from metrics.
    
    Combines multiple metrics into a single 0-1 quality score:
    - Lower complexity = better (40% weight)
    - Type hints present = better (30% weight)
    - Shallow nesting = better (30% weight)
    
    Args:
        cyclomatic_complexity: 1-50+ (1 is simple)
        lines_of_code: Number of lines in code
        has_type_hints: Whether code has type annotations
    
    Returns:
        float: Quality score between 0 and 1
    
    Example:
        >>> calculate_quality_score(5.0, 50, True)
        0.7
    """
    score = 0.0
    
    if cyclomatic_complexity is not None:
        complexity_score = (1 - min(cyclomatic_complexity, 10) / 10) * 0.4
        score += complexity_score
    
    if has_type_hints:
        score += 0.3
    else:
        score += 0.1
    
    return max(0, min(1, score))
```

### Error Handling

```python
# Good - specific exceptions
try:
    session = db.get_session(session_id)
except SessionNotFoundError:
    logger.error(f"Session {session_id} not found")
    return None
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise

# Bad - bare except
try:
    session = db.get_session(session_id)
except:
    pass
```

### Comments

```python
# Good - explains WHY, not WHAT
# We use a default timeout of 300s to allow users to take coffee breaks
# without session being marked as abandoned
SESSION_TIMEOUT = 300

# Bad - obvious comment
# Set session timeout
SESSION_TIMEOUT = 300

# Good - explain non-obvious decisions
def calculate_acceptance_rate(interactions):
    # Only count interactions that were at least 50 chars (filter out accidents)
    valid_interactions = [i for i in interactions if len(i.response) > 50]
    accepted = sum(1 for i in valid_interactions if i.was_accepted)
    return accepted / len(valid_interactions) if valid_interactions else 0

# Bad - obvious what the code does
accepted = sum(1 for i in interactions if i.was_accepted)
```

## JavaScript/React (Frontend)

### Naming Conventions

```javascript
// Components: PascalCase
function Dashboard() { }
function SessionList() { }
function DateRangeFilter() { }

// Functions/hooks: camelCase
function useSessions(filters) { }
function useMetrics(filters) { }
function handleDateChange(date) { }

// Constants: SCREAMING_SNAKE_CASE
const API_BASE_URL = 'http://localhost:8000'
const DEFAULT_PAGE_SIZE = 50

// Private functions/utils: _leading_underscore
function _formatDate(date) { }
function _calculateStats(data) { }
```

### Code Organization

```javascript
// 1. Imports
import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Plot from 'react-plotly.js'
import { apiClient } from '../api/client'

// 2. Constants
const DEFAULT_PAGE_SIZE = 50
const API_TIMEOUT = 10000

// 3. Component
function Dashboard() {
  // State
  const [filters, setFilters] = useState({ /* ... */ })
  
  // Effects
  useEffect(() => { /* ... */ }, [filters])
  
  // Handlers
  const handleFilterChange = (newFilters) => { /* ... */ }
  
  // Computed values
  const kpis = useMemo(() => ({ /* ... */ }), [sessions])
  
  // Render
  return (
    <div className="dashboard">
      {/* JSX */}
    </div>
  )
}

export default Dashboard
```

### JSX Style

```javascript
// Good - clear structure
return (
  <div className="dashboard">
    <section className="kpi-cards">
      <KPICard title="Total Sessions" value={totalSessions} />
      <KPICard title="Avg Acceptance" value={avgAcceptance} />
    </section>
    
    <section className="charts">
      <Timeline data={timelineData} />
      <ScatterPlot data={scatterData} />
    </section>
  </div>
)

// Avoid - hard to read
return <div className="dashboard"><section className="kpi"><KPICard title="Total Sessions" value={totalSessions} /><KPICard title="Avg Acceptance" value={avgAcceptance} /></section></div>
```

### Props & Destructuring

```javascript
// Good - destructure in function signature
function SessionRow({ session, onSelect }) {
  return (
    <tr onClick={() => onSelect(session.id)}>
      <td>{session.language}</td>
      <td>{session.duration_seconds}s</td>
    </tr>
  )
}

// Also good - clear prop validation
function Timeline({ data = [], title = "Timeline", height = 400 }) {
  return <Plot data={data} layout={{ title }} style={{ height }} />
}
```

### Error Handling

```javascript
// Good - specific error handling with user feedback
async function fetchSessions(filters) {
  try {
    const response = await apiClient.get('/sessions', { params: filters })
    return response.data.sessions
  } catch (error) {
    if (error.response?.status === 404) {
      console.error('Sessions not found')
      return []
    } else if (error.response?.status === 500) {
      showErrorToast('Server error. Try again later.')
      return []
    }
    throw error
  }
}

// Use in component
const { sessions, loading, error } = useSessions(filters)
if (error) return <ErrorMessage message={error} />
```

## SQL (Database)

### Style

```sql
-- Good - clear, uppercase keywords, proper formatting
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  start_time DATETIME NOT NULL,
  language TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_language ON sessions(language);

SELECT s.id, s.language, COUNT(i.id) as interaction_count
FROM sessions s
LEFT JOIN interactions i ON s.id = i.session_id
WHERE s.status = 'completed'
GROUP BY s.id
ORDER BY s.created_at DESC;

-- Bad - hard to read
SELECT s.id,s.language,count(i.id) from sessions s left join interactions i on s.id=i.session_id where s.status='completed' group by s.id;
```

### Naming

```sql
-- Tables: plural snake_case
sessions
interactions
code_metrics

-- Columns: singular snake_case
session_id
interaction_type
created_at

-- Indexes: idx_[table]_[column]
idx_sessions_language
idx_interactions_session_id
idx_code_metrics_interaction_id
```

## CSS/Styling

### Class Naming

```css
/* BEM (Block Element Modifier) */
.dashboard { }
.dashboard__header { }
.dashboard__header--active { }

.filter-panel { }
.filter-panel__item { }
.filter-panel__item--disabled { }

/* Avoid */
.red-box { }  /* What's it for? */
.big-font { } /* How big? */
.button2 { }  /* What's the difference? */
```

### Organization

```css
/* 1. Variables */
:root {
  --primary: #3B82F6;
  --secondary: #10B981;
  --spacing: 1rem;
}

/* 2. Global/Reset */
* { box-sizing: border-box; }
body { font-family: sans-serif; }

/* 3. Layout */
.container { max-width: 1200px; margin: 0 auto; }
.grid { display: grid; }

/* 4. Components */
.button { padding: var(--spacing); }
.card { box-shadow: 0 1px 3px rgba(0,0,0,0.1); }

/* 5. Utilities */
.mt-1 { margin-top: var(--spacing); }
.mb-2 { margin-bottom: calc(var(--spacing) * 2); }
```

## Git Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting, semicolons, etc)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding/updating tests
- `chore`: Build, dependencies, tooling

### Examples

```
feat(monitor): add session detection via .claude files

Implements file system watching using Watchdog to detect
Claude Code activity. Emits events for session_started,
interaction_detected, and session_ended.

Closes #123

feat(api): add metrics/quality endpoint

Implements GET /api/metrics/quality to return code quality
scores and complexity metrics over time.

Query params:
- session_id: filter to specific session
- granularity: "interaction" or "session"

fix(frontend): fix chart not updating on filter change

useMemo dependency list was missing 'filters'.
Now properly recomputes when filters change.

refactor(backend): extract aggregation logic to utils

Moved statistical functions from queries.py to new
aggregations.py file for better separation of concerns.
```

## Documentation

### README Structure

```markdown
# Project Name

Brief description (1-2 sentences)

## Features

- Feature 1
- Feature 2

## Quick Start

Installation and running instructions

## Architecture

High-level system overview

## API Documentation

Endpoint details if applicable

## Configuration

Environment variables, setup

## Development

How to contribute, code style, testing

## License

License info
```

### Code Comments

Write for **why**, not **what**:

```python
# Good - explains the reasoning
# Users often pause for coffee without properly ending sessions.
# 5-minute timeout balances between capturing long pauses and
# correctly ending truly abandoned sessions.
SESSION_TIMEOUT = 300

# Bad - restates the code
# Set timeout to 300 seconds
SESSION_TIMEOUT = 300
```

## Linting & Formatting

### Python

Use `black` for formatting:
```bash
pip install black
black monitor/src backend/src
```

Use `flake8` for linting:
```bash
pip install flake8
flake8 monitor/src backend/src --max-line-length=100
```

### JavaScript

Use `eslint` + `prettier`:
```bash
npm install --save-dev eslint prettier
npx eslint src --fix
npx prettier --write src
```

## Performance Guidelines

### Python

```python
# Prefer list comprehension
good = [x for x in items if x > 5]

# Avoid repeated calculations
bad = [item for item in items if calculate(item) > threshold]
good = [item for item in items if _get_cached(item) > threshold]

# Use generators for large data
bad = [expensive_operation(x) for x in million_items]
good = (expensive_operation(x) for x in million_items)
```

### JavaScript

```javascript
// Avoid unnecessary re-renders
const value = useMemo(() => computeExpensive(data), [data])

// Avoid inline object creation in JSX
const config = { color: 'blue', size: 10 }
return <Chart config={config} />

// Not:
return <Chart config={{ color: 'blue', size: 10 }} />
```

## Security

### Python - SQL Injection Prevention

```python
# Good - parameterized queries with SQLAlchemy
query = select(SessionModel).where(SessionModel.language == language)

# Bad - string concatenation
query = f"SELECT * FROM sessions WHERE language = '{language}'"
```

### JavaScript - XSS Prevention

```javascript
// Good - React automatically escapes
return <div>{userInput}</div>

// Bad - dangerously bypassing escaping
return <div dangerouslySetInnerHTML={{ __html: userInput }} />
```

## Final Checklist

Before committing:

- [ ] Code follows naming conventions
- [ ] Type hints present (Python)
- [ ] Docstrings for all public functions
- [ ] Comments explain WHY, not WHAT
- [ ] No console.log or debug prints left
- [ ] No hardcoded secrets
- [ ] Error handling in place
- [ ] Imports organized
- [ ] Code formatted (black, prettier)
- [ ] No linting errors
- [ ] Tests passing
