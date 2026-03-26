# Testing Strategy

## Overview

Testing is critical for a portfolio project. It demonstrates code quality, reliability, and professional approach.

## Testing Pyramid

```
        Integration Tests (E2E)
       /                      \
    API Tests              Component Tests
   /          \            /          \
Unit Tests   Database    Charts     Hooks
```

## Unit Tests

### Python (pytest)

**Monitor service tests** (`monitor/tests/test_monitor.py`)
```python
# Test database operations
def test_create_session():
    db = DatabaseManager(":memory:")
    session = db.create_session(language="python", project_name="test")
    assert session is not None

def test_log_interaction():
    db = DatabaseManager(":memory:")
    session_id = db.create_session(language="python")
    interaction = db.add_interaction(session_id, prompt="test", response="code")
    assert interaction is not None

# Test metric calculations
def test_calculate_quality_score():
    score = calculate_quality_score(complexity=5, loc=50, type_hints=True)
    assert 0 <= score <= 1
    assert score > 0.5  # Should be decent quality
```

**Backend service tests** (`backend/tests/test_aggregations.py`)
```python
def test_detect_error_patterns():
    errors = [
        {"error_type": "syntax", "recovery_count": 1},
        {"error_type": "syntax", "recovery_count": 2},
        {"error_type": "runtime", "recovery_count": 3},
    ]
    patterns = detect_error_patterns(errors)
    assert patterns["most_common"] == "syntax"
    assert patterns["distribution"]["syntax"] == 2
```

### JavaScript (Jest)

**Frontend hooks tests** (`frontend/src/__tests__/hooks.test.js`)
```javascript
import { renderHook, waitFor } from '@testing-library/react'
import { useSessions } from '../hooks/useSessions'

test('useSessions fetches sessions', async () => {
  const { result } = renderHook(() => useSessions({}))
  
  await waitFor(() => {
    expect(result.current.loading).toBe(false)
  })
  
  expect(Array.isArray(result.current.sessions)).toBe(true)
})
```

## API Tests

### Backend Endpoints

```bash
# Test sessions endpoint
curl -X GET "http://localhost:8000/api/sessions" \
  -H "Content-Type: application/json"

# Test metrics endpoint
curl -X GET "http://localhost:8000/api/metrics/quality" \
  -H "Content-Type: application/json"

# Test with Postman or Insomnia
# Import collection and test all endpoints
```

## Integration Tests

### Monitor → Database

```python
# Test that monitor properly logs sessions
def test_monitor_session_flow():
    db = DatabaseManager(":memory:")
    detector = SessionDetector()
    logger = SessionLogger(detector, db)
    
    # Emit events
    detector.emit("session_started", {...})
    detector.emit("interaction_detected", {...})
    detector.emit("session_ended", {...})
    
    # Verify database
    sessions = db.get_all_sessions({}, 100, 0)
    assert len(sessions) == 1
    assert len(sessions[0].interactions) == 1
```

### Backend → Database

```python
# Test that backend reads from database correctly
def test_get_sessions_api(client):
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert "sessions" in response.json()
```

### Frontend → API

```javascript
// Test that frontend properly fetches and displays data
test('Dashboard displays sessions from API', async () => {
  // Mock API response
  mockApiClient.get.mockResolvedValue({
    data: { sessions: [{ id: "1", language: "python" }] }
  })
  
  render(<Dashboard />)
  
  await waitFor(() => {
    expect(screen.getByText("python")).toBeInTheDocument()
  })
})
```

## End-to-End Tests

### Full Flow Test

1. **Start all services**
   ```bash
   # Terminal 1
   cd monitor && uv run python src/main.py
   
   # Terminal 2
   cd backend && uv run python src/main.py
   
   # Terminal 3
   cd frontend && npm run dev
   ```

2. **Log a test session** (monitor CLI)
   ```bash
   # Terminal 1 (add to monitor)
   uv run python src/main.py --log-interaction "Write a function" "def f(): pass"
   ```

3. **Verify data flow**
   ```bash
   # Check database
   sqlite3 data/sessions.db "SELECT COUNT(*) FROM sessions;"
   
   # Check API
   curl http://localhost:8000/api/sessions
   
   # Check dashboard
   # Open http://localhost:5173, verify data displayed
   ```

4. **Test all filters**
   - Date range filter
   - Language filter
   - Status filter
   - Verify charts update

## Performance Tests

### Database Query Performance

```python
# Measure query speed
import time

start = time.time()
sessions = get_all_sessions({}, 1000, 0)  # Large pagination
elapsed = time.time() - start

assert elapsed < 1.0  # Should be fast
```

### API Response Time

```bash
# Measure API response time
time curl http://localhost:8000/api/sessions

# Real: 0.05s user
# Should be < 0.5s for good UX
```

## Error Handling Tests

### Monitor Error Handling

```python
def test_monitor_handles_invalid_code():
    # Invalid Python code
    code = "def func(:\n    pass"
    
    # Should not crash, should handle gracefully
    metrics = compute_code_metrics(code, "python")
    assert metrics["cyclomatic_complexity"] is None
```

### Backend Error Handling

```python
def test_backend_handles_missing_session():
    response = client.get("/api/sessions/nonexistent")
    assert response.status_code == 404
    assert "error" in response.json()
```

### Frontend Error Handling

```javascript
test('Dashboard handles API error gracefully', async () => {
  mockApiClient.get.mockRejectedValue(new Error('API Error'))
  
  render(<Dashboard />)
  
  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument()
  })
})
```

## Test Coverage Goals

| Component | Target |
|-----------|--------|
| Monitor service | 80% |
| Backend service | 85% |
| Frontend components | 75% |
| API endpoints | 90% |
| Utils/aggregations | 90% |

## Test Execution

### Run All Tests

```bash
# Python tests
cd monitor && pytest
cd ../backend && pytest

# JavaScript tests
cd ../frontend && npm test
```

### Continuous Testing

Add GitHub Actions workflow (`.github/workflows/test.yml`):
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Monitor
        run: cd monitor && uv sync && pytest
      - name: Test Backend
        run: cd backend && uv sync && pytest
      - name: Test Frontend
        run: cd frontend && npm ci && npm test
```

## Test Data

Use fixtures for consistent test data:

```python
# monitor/tests/conftest.py
@pytest.fixture
def sample_session():
    return {
        "language": "python",
        "project_name": "test_project",
        "file_path": "/tmp/test.py",
        "start_time": datetime.utcnow(),
        "status": "in_progress"
    }

@pytest.fixture
def sample_interaction():
    return {
        "human_prompt": "Write a hello function",
        "claude_response": "def hello():\n    print('hello')",
        "was_accepted": True,
        "interaction_type": "new_code"
    }
```

## Manual Testing Checklist

- [ ] Monitor detects Claude Code activity (or CLI fallback works)
- [ ] Monitor logs interactions to database
- [ ] Monitor calculates acceptance rate
- [ ] Backend API returns all session data
- [ ] Backend API filters work (language, date range, status)
- [ ] Backend aggregations are correct
- [ ] Frontend loads without errors
- [ ] Dashboard displays all KPI cards
- [ ] Charts render with sample data
- [ ] Filters update charts on change
- [ ] Sessions list is sortable
- [ ] Error messages display gracefully
- [ ] No console errors or warnings

## Testing Tools

**Python**
- pytest - Unit testing framework
- pytest-cov - Coverage reporting
- pytest-asyncio - Async test support

**JavaScript**
- Jest - Testing framework
- React Testing Library - Component testing
- Cypress (optional) - E2E testing

## When to Create Testing Subagent

Create a testing subagent when:
- Comprehensive test suite needed
- Coverage requirements (>80%)
- CI/CD pipeline setup
- Complex mocking/fixtures required

Reference: `rules/07-subagent-workflow.md`
