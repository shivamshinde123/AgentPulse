# Subagent Workflow

## Overview

This file defines when and how to create specialized Claude Code subagents for complex tasks. A subagent is a dedicated Claude Code session focused on a specific component.

## When to Create a Subagent

Create a subagent when:

1. **A component becomes complex** (>500 lines of code)
2. **Specialized expertise needed** (3D visualization, advanced DB optimization)
3. **Task is self-contained** (can be done independently)
4. **Main agent is overloaded** (hard to keep context)

## Subagent Categories

### 1. Database Optimization Subagent

**When to create:**
- Queries are slow (>100ms for typical operations)
- Need to optimize N+1 problems
- Need to add indexes or refactor queries
- Need connection pooling configuration

**Scope:**
- Files: `monitor/src/db.py`, `backend/src/db/queries.py`, `shared/db_schema.sql`
- Task: Profile queries, add indexes, optimize slow queries
- Success: All queries execute in <50ms average

**Request template:**
```
@Claude Code: Create subagent for Database Optimization

Task: Profile and optimize database queries for the analytics system.

Current issues:
- Session list query takes >200ms for 1000 sessions
- Filtering by date range is slow
- Metrics aggregation queries are inefficient

Files involved:
- monitor/src/db.py (database operations)
- backend/src/db/queries.py (query functions)
- shared/db_schema.sql (schema and indexes)

Success criteria:
- All queries execute in <50ms
- Explain N+1 problems found and fixed
- Provide index recommendations
- Document query optimization strategies
```

### 2. Advanced Plotly Charts Subagent

**When to create:**
- Need 3D scatter plots or visualizations
- Need custom interactivity (linked charts, click events)
- Need animations or transitions
- Need custom color scales or themes

**Scope:**
- Files: `frontend/src/components/Charts/`
- Task: Build advanced chart components with Plotly
- Success: 3D charts render smoothly, interactions work

**Request template:**
```
@Claude Code: Create subagent for Advanced Plotly Charts

Task: Implement 3D visualization for session trajectories.

Requirements:
- 3D scatter plot showing sessions in quality/complexity/error space
- Color code by language
- Size by duration
- Interactive: hover shows session metadata
- Zoom and rotate support

Files involved:
- frontend/src/components/Charts/

Success criteria:
- 3D chart renders without performance issues
- Hover tooltips work
- Zoom/rotate responsive
- Mobile-friendly fallback (2D chart)
```

### 3. Error Handling & Logging Subagent

**When to create:**
- Need structured logging across services
- Need error recovery mechanisms
- Need monitoring/alerting
- Need error dashboards

**Scope:**
- Files: All Python files (monitor, backend)
- Task: Implement comprehensive logging and error handling
- Success: All errors logged with context, recoverable errors handled

**Request template:**
```
@Claude Code: Create subagent for Error Handling & Logging

Task: Implement structured logging and error recovery.

Requirements:
- Structured JSON logging for all services
- Centralized error handling with context
- Automatic error recovery where possible
- Error logs stored for debugging

Files involved:
- monitor/src/
- backend/src/

Success criteria:
- All unhandled exceptions caught
- Error logs contain full context
- Database connection errors retry automatically
- API errors return proper HTTP status codes
```

### 4. Data Aggregation Subagent

**When to create:**
- Need complex statistical calculations
- Need anomaly detection
- Need predictive metrics
- Need advanced trend analysis

**Scope:**
- Files: `backend/src/utils/aggregations.py`
- Task: Implement advanced aggregation functions
- Success: All metrics calculated correctly

**Request template:**
```
@Claude Code: Create subagent for Data Aggregation

Task: Implement advanced statistical aggregations.

Requirements:
- Percentile calculations
- Anomaly detection in acceptance rates
- Trend forecasting (simple linear regression)
- Standard deviation and confidence intervals

Files involved:
- backend/src/utils/aggregations.py
- backend/src/db/queries.py (for data retrieval)

Success criteria:
- All statistical functions implemented
- Unit tests for each function
- Performance optimized (<100ms for typical calls)
- Documented mathematical approach
```

### 5. Frontend State Management Subagent

**When to create:**
- Frontend has complex state (many filters, cross-component state)
- Need Redux or Context API
- Need state persistence (localStorage)
- Need undo/redo functionality

**Scope:**
- Files: `frontend/src/hooks/`, `frontend/src/`
- Task: Refactor frontend to use global state management
- Success: Filters sync across pages, state persists

**Request template:**
```
@Claude Code: Create subagent for Frontend State Management

Task: Implement global state management for filters and user preferences.

Current issue:
- Filters in Dashboard don't persist when navigating to Sessions page
- Multiple filter components managing state separately
- No way to save user's filter preferences

Files involved:
- frontend/src/ (all frontend files)

Success criteria:
- Global filter state (Context API or simple store)
- Filters persist across navigation
- User preferences saved to localStorage
- Easy to add new filters without refactoring
```

### 6. Testing Subagent

**When to create:**
- Need comprehensive test coverage
- Need test infrastructure (CI/CD)
- Need E2E test automation
- Need performance/load testing

**Scope:**
- Files: All services (test directories)
- Task: Write and automate tests
- Success: 80%+ coverage, CI/CD passing

**Request template:**
```
@Claude Code: Create subagent for Testing

Task: Implement comprehensive test suite and CI/CD pipeline.

Requirements:
- Unit tests for all Python modules (80%+ coverage)
- Integration tests for API endpoints
- React component tests
- E2E tests for critical workflows
- GitHub Actions CI/CD pipeline

Files involved:
- monitor/tests/
- backend/tests/
- frontend/src/__tests__/
- .github/workflows/

Success criteria:
- 80%+ code coverage across all services
- All tests passing
- CI/CD pipeline working
- Tests run on every push
- Test execution time <5 minutes
```

### 7. DevOps & Deployment Subagent

**When to create:**
- Need Docker containerization
- Need cloud deployment (Heroku, AWS, GCP)
- Need environment management
- Need monitoring and alerting

**Scope:**
- Files: Root level (docker, deployment configs)
- Task: Set up containerization and deployment
- Success: One-command deployment to cloud

**Request template:**
```
@Claude Code: Create subagent for DevOps & Deployment

Task: Containerize project and set up deployment pipeline.

Requirements:
- Dockerfile for each service
- docker-compose for local development
- Environment variable management
- Deployment to Heroku or similar
- Health checks and monitoring

Files involved:
- Dockerfile (root)
- docker-compose.yml
- .env files
- GitHub Actions for deployment

Success criteria:
- docker-compose up starts all services
- Deployment to cloud with single command
- Health checks working
- Environment variables properly managed
```

## How to Request a Subagent

### Step 1: Recognize the need
You realize during implementation that a component is becoming complex or specialized.

### Step 2: Prepare context
Gather information about the task:
- Which files are involved?
- What's the specific problem?
- What are the success criteria?
- How does this relate to the rest of the project?

### Step 3: Create the subagent
In Claude Code, use this format:

```
@Claude Code: Create a subagent for [Component Name]

Context: [Brief explanation of why this needs a subagent]

Task: [Clear description of what to accomplish]

Files involved:
- path/to/file1.py
- path/to/file2.py
- path/to/file3.jsx

Constraints:
- Use [technology/pattern]
- Don't modify [file] (external API/dependency)
- Must maintain backward compatibility with [component]

Success criteria:
- [Specific, measurable outcome 1]
- [Specific, measurable outcome 2]
- [Specific, measurable outcome 3]

Documentation:
- Comment your code
- Explain any non-obvious decisions
- Update README if adding new files
```

### Step 4: Integrate results
The subagent returns completed code that you:
1. Review for quality and correctness
2. Copy into the main project
3. Test to ensure integration works
4. Commit with clear message

## Subagent Integration Checklist

- [ ] Review code for style consistency
- [ ] Verify it works with existing code
- [ ] Run tests
- [ ] Update documentation
- [ ] Commit with clear message
- [ ] Link back to main branch if diverged

## Commit Message Format After Subagent

```
feat: [component] - subagent: [specific achievement]

Subagent: [ComponentName Subagent]
Files modified: [list of files]
Changes: [summary of changes]
Testing: [how tested]

Closes: [reference to original issue if any]
```

Example:
```
feat: database - subagent: query optimization and indexing

Subagent: Database Optimization Subagent
Files modified:
- monitor/src/db.py
- backend/src/db/queries.py
- shared/db_schema.sql

Changes:
- Added 5 strategic indexes for common queries
- Refactored session list query to avoid N+1
- Connection pooling optimized

Testing: All queries now execute <50ms average

Related: Slow dashboard load times resolved
```

## Subagent Communication Protocol

**Main Agent → Subagent:**
```
@Claude Code: [request with full context and requirements]
```

**Subagent → Main Agent:**
```
Subagent completed: [ComponentName]

Summary: [What was accomplished]

Files created/modified: [list]

Key changes: [summary]

Validation: [how it was tested]

Ready for integration: [yes/no]

Notes: [any constraints or follow-up needed]
```

## Managing Multiple Subagents

If running multiple subagents in parallel:

1. Ensure they don't modify the same files
2. Use git branches if possible
3. Merge results sequentially
4. Test integration after each merge

Example workflow:
```bash
git checkout -b feat/db-optimization
# Subagent 1 works here

git checkout main
git merge feat/db-optimization

git checkout -b feat/advanced-charts
# Subagent 2 works here

git checkout main
git merge feat/advanced-charts
```

## When Not to Create a Subagent

Subagents are overkill for:
- Simple bug fixes
- Small features (<100 lines)
- Configuration changes
- Documentation updates
- Refactoring that fits in one session

Just use main Claude Code for these.

## Portfolio Value

Subagent usage demonstrates:
- **Planning**: Knowing when to specialize
- **Architecture**: Clear task separation
- **Communication**: Structured handoffs
- **Quality**: Focused expertise on complex tasks

Document this workflow in your portfolio as a sign of professional development practices.
