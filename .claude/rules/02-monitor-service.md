# Monitor Service (Python)

## Overview

The monitor service runs continuously on the user's local machine and watches for Claude Code sessions. It logs interactions (prompt → response pairs) to the SQLite database.

**Location**: `monitor/` directory  
**Language**: Python 3.9+  
**Package Manager**: uv  
**Key Dependency**: Watchdog (file system monitoring)

## Responsibilities

1. **Detect** Claude Code activity (watch .claude files or file system changes)
2. **Extract** metadata (timestamp, language, file path, tokens, etc.)
3. **Log** interactions (human prompt, Claude response, acceptance status)
4. **Compute** basic metrics (modification count, interaction type classification)
5. **Store** all data in SQLite database

## Architecture

```
main.py
  ├─ detector.py      (watches file system for Claude Code activity)
  ├─ logger.py        (logs interactions, computes basic metrics)
  └─ db.py            (database operations: SQLAlchemy models & CRUD)
```

## File Structure

```
monitor/
├── pyproject.toml
├── uv.lock
├── README.md
└── src/
    ├── __init__.py
    ├── main.py
    ├── detector.py
    ├── logger.py
    ├── db.py
    └── utils.py
```

## Dependencies (pyproject.toml)

```toml
[project]
name = "claude-code-analyzer-monitor"
version = "0.1.0"
description = "Monitor and log Claude Code sessions locally"
requires-python = ">=3.9"

dependencies = [
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "watchdog>=3.0.0",
]
```

## Module Details

### 1. main.py - Entry Point & Orchestration

```python
# Key responsibilities:
# - Initialize database (create tables if needed)
# - Start detector (file system watcher)
# - Start logger (subscriber to detector events)
# - Keep running indefinitely
# - Handle Ctrl+C gracefully

# Startup flow:
# 1. os.makedirs("../data", exist_ok=True)
# 2. init_database("../data/sessions.db")
# 3. detector = SessionDetector()
# 4. logger = SessionLogger(detector)
# 5. detector.start()
# 6. logger.start()
# 7. Keep running with signal.pause()
# 8. On KeyboardInterrupt, shutdown gracefully

# Example console output:
# > Monitor started. Watching for Claude Code sessions...
# > Detected session start: python, /Users/user/project/main.py
# > Logged interaction: sequence=1, type=new_code
# > Session ended: 3 interactions, 85% acceptance rate
```

**Key Functions**:
- `init_database(db_path)` - Create tables if not exist
- `main()` - Orchestration
- `signal_handler(signum, frame)` - Graceful shutdown
- `setup_logging()` - Configure logging to console

---

### 2. detector.py - File System Monitoring

**Purpose**: Watch for Claude Code activity, emit events that logger subscribes to.

**Detection Strategy**:

The monitor needs to detect when Claude Code creates/modifies `.claude` metadata files. However, `.claude` may not always be readable or even exist. Implement a **two-tier approach**:

#### Tier 1: .claude File Watching (Primary)
- Watch common `.claude` locations:
  - User's project root directory: `./.claude/`
  - Home directory: `~/.claude/`
  - MacOS: `~/Library/Application Support/Claude/`
  - Windows: `C:\Users\[User]\AppData\Local\Claude\`
  - Linux: `~/.config/claude/`
- Use Watchdog to detect file creation/modification events
- Parse metadata (timestamp, language, file being edited)
- Emit `SessionStarted` event with metadata

#### Tier 2: CLI Fallback (For Testing/Flexibility)
- Allow manual logging via command: `python src/main.py --log-interaction "prompt" "response"`
- Useful for testing without relying on actual Claude Code
- Makes system more flexible for portfolio demonstrations

```python
# Example class structure:

class SessionDetector:
    def __init__(self, watch_paths=None):
        # watch_paths: list of directories to monitor
        # If None, use default locations
        self.event_handlers = []  # Subscribers
        self.observer = Observer()  # Watchdog observer
    
    def subscribe(self, handler):
        # handler is a function or class with on_event(event_type, data)
        self.event_handlers.append(handler)
    
    def emit(self, event_type: str, data: dict):
        # Call all subscribers with event
        for handler in self.event_handlers:
            handler.on_event(event_type, data)
    
    def on_created(self, event):
        # Watchdog callback: file created
        if event.src_path.endswith('.claude'):
            self.emit("session_started", {...})
    
    def on_modified(self, event):
        # Watchdog callback: file modified
        if event.src_path.endswith('.claude'):
            self.emit("interaction_detected", {...})
    
    def start(self):
        # Start watching directories
        pass
    
    def stop(self):
        # Stop watching
        pass

# Events emitted:
# - "session_started": New Claude Code session detected
#   data: {timestamp, language, file_path, project_name}
# - "interaction_detected": New prompt-response detected
#   data: {timestamp, human_prompt, claude_response, tokens}
# - "session_ended": Session finished or timed out
#   data: {session_id, duration, interaction_count}
```

**Detector Behavior**:
- Runs continuously in background
- Watches file system for changes
- When `.claude` file is created: emit `session_started`
- When `.claude` file is modified: emit `interaction_detected`
- If no activity for N seconds (timeout=300): emit `session_ended`
- All events go to subscribers (logger listens)

---

### 3. logger.py - Interaction Logging

**Purpose**: Subscribe to detector events, compute basic metrics, store in database.

```python
class SessionLogger:
    def __init__(self, detector, db_path):
        self.detector = detector
        self.db = DatabaseManager(db_path)
        self.current_session = None
        self.previous_response = None  # Track last response for modification detection
        
        # Subscribe to detector
        detector.subscribe(self)
    
    def on_event(self, event_type: str, data: dict):
        if event_type == "session_started":
            self._handle_session_started(data)
        elif event_type == "interaction_detected":
            self._handle_interaction_detected(data)
        elif event_type == "session_ended":
            self._handle_session_ended(data)
    
    def _handle_session_started(self, data):
        # Create new session in database
        session = Session(
            language=data["language"],
            project_name=data["project_name"],
            file_path=data["file_path"],
            start_time=data["timestamp"],
            status="in_progress"
        )
        session_id = self.db.create_session(session)
        self.current_session = session_id
        print(f"Session started: {session_id}")
    
    def _handle_interaction_detected(self, data):
        # Extract from data:
        # - human_prompt: what user asked
        # - claude_response: code Claude suggested
        # - tokens: approximate tokens used
        
        # Classify interaction type
        interaction_type = self._classify_interaction(data["claude_response"])
        
        # Detect if response was modified from previous
        was_modified = self._detect_modification(data["claude_response"])
        
        # Create interaction record
        interaction = Interaction(
            session_id=self.current_session,
            sequence_number=next_sequence,
            timestamp=data["timestamp"],
            human_prompt=data["human_prompt"],
            claude_response=data["claude_response"],
            was_accepted=True,  # Assume accepted unless marked otherwise
            was_modified=was_modified,
            interaction_type=interaction_type,
            tokens_used=data.get("tokens")
        )
        
        interaction_id = self.db.add_interaction(interaction)
        
        # Compute code metrics (if language supported)
        if data["language"] in ["python", "javascript", "typescript"]:
            metrics = self._compute_code_metrics(
                data["claude_response"],
                data["language"]
            )
            self.db.add_code_metrics(interaction_id, metrics)
        
        self.previous_response = data["claude_response"]
        print(f"Interaction logged: {interaction_id}")
    
    def _handle_session_ended(self, data):
        # Calculate acceptance rate
        acceptance_rate = self._calculate_acceptance_rate(
            self.current_session
        )
        
        # Update session
        self.db.end_session(
            self.current_session,
            end_time=data["timestamp"],
            acceptance_rate=acceptance_rate,
            status="completed"
        )
        
        print(f"Session ended: {self.current_session}")
        self.current_session = None
    
    def _classify_interaction(self, code_response: str) -> str:
        # Heuristics to classify interaction type:
        # - "new_code": Few existing functions, mostly new definitions
        # - "refactor": Existing functions being modified/reorganized
        # - "bugfix": Small changes, error fixes (uses ast diff)
        # - "explanation": Response is mostly comments, no new code
        
        # Simple heuristic for now:
        if len(code_response) < 100:
            return "bugfix"
        elif code_response.count("def ") + code_response.count("class ") > 2:
            return "new_code"
        else:
            return "refactor"
    
    def _detect_modification(self, code_response: str) -> bool:
        # Compare with previous response
        if self.previous_response is None:
            return False
        return code_response != self.previous_response
    
    def _compute_code_metrics(self, code: str, language: str) -> dict:
        # Use ast module for Python
        # Use regex/simple parsing for JavaScript/TypeScript
        
        metrics = {
            "cyclomatic_complexity": None,
            "lines_of_code": None,
            "function_count": None,
            "class_count": None,
            "max_nesting_depth": None,
            "has_type_hints": None,
            "code_quality_score": None
        }
        
        if language == "python":
            import ast
            try:
                tree = ast.parse(code)
                metrics["lines_of_code"] = len(code.split("\n"))
                metrics["function_count"] = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
                metrics["class_count"] = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
                # More metrics as needed
            except SyntaxError:
                pass  # Code may be incomplete/invalid
        
        return metrics
    
    def _calculate_acceptance_rate(self, session_id: str) -> float:
        # Query interactions for this session
        interactions = self.db.get_session_interactions(session_id)
        if not interactions:
            return 0.0
        
        accepted = sum(1 for i in interactions if i.was_accepted)
        return accepted / len(interactions)
```

**Key Features**:
- Listens to detector events
- Creates session on "session_started"
- Logs interactions on "interaction_detected"
- Computes interaction type (new_code, refactor, bugfix, explanation)
- Detects code modifications
- Computes code quality metrics (complexity, LOC, functions, etc.)
- Ends session on timeout or explicit "session_ended"
- Calculates overall acceptance rate

---

### 4. db.py - Database Operations

**Purpose**: SQLAlchemy models and CRUD operations.

```python
# Key classes:
# - SessionModel, InteractionModel, ErrorModel, CodeMetricsModel (ORM models)
# - DatabaseManager (CRUD operations)

class DatabaseManager:
    def __init__(self, db_path):
        # SQLAlchemy connection, connection pooling
        # Create tables if not exist
        pass
    
    def create_session(self, session: Session) -> str:
        # INSERT into sessions table
        # Return session_id
        pass
    
    def add_interaction(self, interaction: Interaction) -> str:
        # INSERT into interactions table
        # Return interaction_id
        pass
    
    def add_error(self, error: Error):
        # INSERT into errors table
        pass
    
    def add_code_metrics(self, interaction_id: str, metrics: dict):
        # INSERT into code_metrics table
        pass
    
    def end_session(self, session_id: str, end_time, acceptance_rate, status):
        # UPDATE sessions table
        pass
    
    def get_session_interactions(self, session_id: str) -> List[Interaction]:
        # SELECT interactions WHERE session_id = ?
        pass
```

**Implementation Notes**:
- Use SQLAlchemy ORM (not raw SQL)
- Connection pooling for efficiency
- Proper error handling (database errors, constraint violations)
- Transactions for multi-step operations
- See `rules/01-database-schema.md` for schema details

---

### 5. utils.py - Helper Functions

```python
# Functions:
# - extract_language(file_path: str) -> str
#   Returns language based on file extension
# - calculate_nesting_depth(code: str, language: str) -> int
#   AST parsing to compute max nesting level
# - parse_error_message(error_text: str) -> (error_type, severity)
#   Regex patterns to classify errors
# - estimate_tokens(text: str) -> int
#   Rough token count estimate (if actual tokens not available)
```

---

## Workflow

1. **Start**:
   - User runs: `cd monitor && uv sync && uv run python src/main.py`
   - main.py initializes database and starts detector + logger

2. **User codes with Claude Code**:
   - Claude Code creates/modifies `.claude` metadata file
   - Detector watches and detects this
   - Detector emits "session_started" event

3. **First interaction**:
   - Logger receives "session_started"
   - Logger creates session record in database
   - When Claude suggests code, detector emits "interaction_detected"
   - Logger logs interaction to database with metrics

4. **More interactions**:
   - Each Claude suggestion triggers "interaction_detected"
   - Logger logs each one
   - Computes metrics, detects modifications, classifies type

5. **Session ends**:
   - After N seconds of inactivity, detector emits "session_ended"
   - Logger updates session record with end_time, acceptance_rate, status
   - Ready for next session

6. **Data flow**:
   ```
   Claude Code session
         ↓ (.claude file created)
   Detector watches
         ↓ (event emitted)
   Logger listens
         ↓ (computes metrics)
   Database (SQLite)
         ↓
   Backend reads for APIs
   ```

---

## Configuration

**Environment Variables** (optional):
- `DATABASE_PATH`: Path to SQLite database (default: `../data/sessions.db`)
- `WATCH_DIRECTORY`: Root directory to monitor (default: current working directory)
- `SESSION_TIMEOUT_SECONDS`: Inactivity timeout (default: 300 seconds)
- `LOG_LEVEL`: Python logging level (default: INFO)

---

## Testing the Monitor

### Manual Testing (without actual Claude Code):

```bash
# Test 1: Verify database initialization
cd monitor && uv run python -c "from src.db import DatabaseManager; db = DatabaseManager('../data/sessions.db'); print('Database initialized')"

# Test 2: Log a test session manually
# Create a CLI command:
# uv run python src/main.py --test-session

# Inside main.py:
# if args.test_session:
#     detector.emit("session_started", {...})
#     detector.emit("interaction_detected", {prompt: "...", response: "..."})
#     detector.emit("session_ended", {...})

# Test 3: Verify data in database
sqlite3 ../data/sessions.db "SELECT * FROM sessions LIMIT 1;"
```

---

## Error Handling

- **Database connection errors**: Log and retry with backoff
- **Invalid file format**: Skip and continue watching
- **Timeout during session**: Gracefully mark as abandoned
- **Keyboard interrupt (Ctrl+C)**: Flush pending writes, close connections, exit cleanly

---

## Performance Considerations

- Watchdog is efficient (uses OS-level file system events, not polling)
- Database writes are batched where possible
- Keep only recent sessions in memory
- Archive old data if database grows large (future enhancement)

---

## Next Steps

1. Implement detector.py (file watching with Watchdog)
2. Implement logger.py (event handling, metrics computation)
3. Implement db.py (SQLAlchemy models, CRUD operations)
4. Implement main.py (orchestration, signal handling)
5. Test with CLI fallback (--log-interaction)
6. Once working, integrate with backend for API access
