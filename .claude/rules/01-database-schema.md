# Database Schema & Data Models

## SQLite Database Overview

**Location**: `../data/sessions.db` (shared across all services)

**Purpose**: Central data store for all Claude Code session data, interactions, errors, and metrics.

**Initialization**: Created automatically on first run by monitor service using `shared/db_schema.sql`

## Tables

### 1. sessions

Represents a complete Claude Code session (from start to end).

```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,              -- UUID
  start_time DATETIME NOT NULL,     -- When user started coding with Claude
  end_time DATETIME,                -- When user finished (NULL if still ongoing)
  duration_seconds INTEGER,          -- Calculated: end_time - start_time
  language TEXT NOT NULL,            -- python, javascript, typescript, java, go, rust, etc
  project_name TEXT,                 -- Inferred from directory or manually set
  file_path TEXT,                    -- Primary file being edited
  total_tokens_used INTEGER,         -- Sum of all token usage in session (nullable)
  acceptance_rate FLOAT,             -- 0-1, calculated: accepted / total interactions
  status TEXT NOT NULL,              -- completed, abandoned, in_progress
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_start_time ON sessions(start_time);
CREATE INDEX idx_sessions_language ON sessions(language);
CREATE INDEX idx_sessions_status ON sessions(status);
```

**Fields Explanation**:
- `id`: UUID (e.g., `550e8400-e29b-41d4-a716-446655440000`)
- `start_time`: ISO format timestamp when monitor detected first interaction
- `end_time`: ISO format timestamp when session ended (NULL if in progress)
- `duration_seconds`: Seconds between start_time and end_time
- `language`: One of: python, javascript, typescript, java, go, rust, csharp, cpp, etc
- `project_name`: Directory name or user-specified project name
- `file_path`: Absolute path to the primary file being edited
- `total_tokens_used`: Sum of tokens_used from all interactions in this session
- `acceptance_rate`: Percentage of interactions where user accepted the suggestion
- `status`: "completed" (session ended normally), "abandoned" (timeout), "in_progress" (still active)

---

### 2. interactions

Individual code suggestions within a session. Each interaction is a prompt → response pair.

```sql
CREATE TABLE interactions (
  id TEXT PRIMARY KEY,              -- UUID
  session_id TEXT NOT NULL,         -- Foreign key → sessions.id
  sequence_number INTEGER NOT NULL, -- Order within session (1, 2, 3...)
  timestamp DATETIME NOT NULL,      -- When this interaction happened
  human_prompt TEXT NOT NULL,       -- What user asked Claude
  claude_response TEXT NOT NULL,    -- Code Claude suggested
  response_length INTEGER,          -- Length of claude_response in chars
  was_accepted BOOLEAN NOT NULL,    -- User accepted without modification
  was_modified BOOLEAN NOT NULL,    -- User modified after accepting
  modification_count INTEGER,       -- How many times user edited before accepting
  tokens_used INTEGER,              -- Tokens for this interaction (nullable)
  interaction_type TEXT NOT NULL,   -- new_code, refactor, bugfix, explanation
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sessions(id),
  PRIMARY KEY (id)
);

CREATE INDEX idx_interactions_session_id ON interactions(session_id);
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp);
CREATE INDEX idx_interactions_type ON interactions(interaction_type);
```

**Fields Explanation**:
- `id`: UUID for this interaction
- `session_id`: Links to sessions table
- `sequence_number`: 1st, 2nd, 3rd interaction in this session
- `timestamp`: When this prompt-response occurred
- `human_prompt`: Full text of what user asked (e.g., "Write a function that validates email")
- `claude_response`: Full code Claude suggested
- `response_length`: Character count of response (for metrics)
- `was_accepted`: TRUE if user accepted without changes
- `was_modified`: TRUE if user made edits after accepting
- `modification_count`: If user edited 3 times before accepting = 3
- `tokens_used`: Approximate token count (nullable if not tracked)
- `interaction_type`: Categorizes the interaction
  - "new_code": Writing new functions/classes
  - "refactor": Improving existing code
  - "bugfix": Fixing errors
  - "explanation": Claude explaining code
- `created_at`: When this record was inserted

---

### 3. errors

Track errors that occurred during or after Claude's suggestions.

```sql
CREATE TABLE errors (
  id TEXT PRIMARY KEY,              -- UUID
  interaction_id TEXT NOT NULL,     -- Foreign key → interactions.id
  session_id TEXT NOT NULL,         -- Foreign key → sessions.id (for easy filtering)
  error_type TEXT NOT NULL,         -- syntax, runtime, type, logic
  error_message TEXT NOT NULL,      -- Full error text from IDE/compiler/runtime
  language TEXT NOT NULL,           -- Programming language context
  severity TEXT NOT NULL,           -- low, medium, high
  was_resolved_in_next_interaction BOOLEAN,  -- Did next suggestion fix it?
  recovery_interactions_count INTEGER,       -- How many tries to fix?
  timestamp DATETIME NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (interaction_id) REFERENCES interactions(id),
  FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_errors_session_id ON errors(session_id);
CREATE INDEX idx_errors_interaction_id ON errors(interaction_id);
CREATE INDEX idx_errors_type ON errors(error_type);
```

**Fields Explanation**:
- `error_type`: 
  - "syntax": Code doesn't parse (missing semicolon, bad indentation, etc)
  - "runtime": Code runs but crashes (NameError, TypeError, etc)
  - "type": Type checking fails (mypy, TypeScript errors)
  - "logic": Code runs without errors but produces wrong result
- `severity`:
  - "low": Minor issue, easily fixed
  - "medium": Blocks compilation/interpretation but relatively straightforward fix
  - "high": Critical logic error or security issue
- `was_resolved_in_next_interaction`: Did the very next interaction fix this error?
- `recovery_interactions_count`: If next interaction didn't fix it, how many total attempts?
- `timestamp`: When the error was detected

---

### 4. code_metrics

Static analysis metrics computed from Claude's code suggestions.

```sql
CREATE TABLE code_metrics (
  id TEXT PRIMARY KEY,              -- UUID
  interaction_id TEXT NOT NULL,     -- Foreign key → interactions.id
  cyclomatic_complexity FLOAT,      -- 1-50+ (1 is simple, 10+ is complex)
  lines_of_code INTEGER,            -- Number of lines in suggestion
  function_count INTEGER,           -- Number of functions defined
  class_count INTEGER,              -- Number of classes defined
  max_nesting_depth INTEGER,        -- Max nesting level (loops, ifs, etc)
  has_type_hints BOOLEAN,           -- For Python: type hints present?
  code_quality_score FLOAT,         -- 0-1 (computed from above metrics)
  language TEXT NOT NULL,           -- python, javascript, etc
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (interaction_id) REFERENCES interactions(id),
  PRIMARY KEY (id)
);

CREATE INDEX idx_code_metrics_interaction_id ON code_metrics(interaction_id);
```

**Fields Explanation**:
- `cyclomatic_complexity`: Computed from Python `ast` module or JavaScript equivalent
  - 1-5: Simple
  - 6-10: Moderate
  - 11+: Complex (harder to test/understand)
- `lines_of_code`: Actual code lines (excluding comments/blanks)
- `function_count`, `class_count`: Structural breakdown
- `max_nesting_depth`: How deep are if/for/while nesting? (0-3 is good, 5+ is problematic)
- `has_type_hints`: Python-specific, TRUE if `def func(x: int) -> str:` format used
- `code_quality_score`: Aggregate 0-1 score computed as:
  ```
  score = (
    (1 - min(complexity, 10)/10) * 0.4 +      -- Lower complexity is better
    (type_hints ? 0.3 : 0) +                  -- Type hints increase quality
    (max_nesting <= 3 ? 0.3 : 0.1) +          -- Shallow nesting is better
    (loc <= 50 ? 0.0 : -0.1)                  -- Too long is worse
  )
  clamped to [0, 1]
  ```

---

## Relationships

```
sessions (1) ──→ (∞) interactions
            ──→ (∞) errors
            ──→ (∞) code_metrics (via interactions)

interactions (1) ──→ (∞) errors
              ──→ (∞) code_metrics
```

**Key Points**:
- One session has many interactions
- One interaction may have multiple errors
- One interaction has one code_metrics record
- Errors link to both interaction AND session (for easy filtering)

---

## Data Types & Constraints

| Type | Example | Notes |
|------|---------|-------|
| TEXT | 'python', 'Write a function' | Variable length strings |
| INTEGER | 42, 1000, -1 | Whole numbers |
| FLOAT | 0.85, 3.14 | Decimal numbers |
| BOOLEAN | 1 (TRUE), 0 (FALSE) | SQLite uses 0/1 |
| DATETIME | '2025-01-15T14:30:00' | ISO 8601 format |
| PRIMARY KEY | AUTO | Unique identifier for each row |
| FOREIGN KEY | Links between tables | Maintains referential integrity |
| DEFAULT CURRENT_TIMESTAMP | Auto-set on insert | Current time |

---

## Indexes

Indexes speed up common queries. Include these:

```sql
-- sessions
CREATE INDEX idx_sessions_start_time ON sessions(start_time);
CREATE INDEX idx_sessions_language ON sessions(language);
CREATE INDEX idx_sessions_status ON sessions(status);

-- interactions
CREATE INDEX idx_interactions_session_id ON interactions(session_id);
CREATE INDEX idx_interactions_type ON interactions(interaction_type);

-- errors
CREATE INDEX idx_errors_session_id ON errors(session_id);
CREATE INDEX idx_errors_type ON errors(error_type);

-- code_metrics
CREATE INDEX idx_code_metrics_interaction_id ON code_metrics(interaction_id);
```

---

## Sqlalchemy ORM Models (Python)

These models are defined in `monitor/src/db.py` and `backend/src/db/models.py`:

```python
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class SessionModel(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    language = Column(String, nullable=False)
    project_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    total_tokens_used = Column(Integer, nullable=True)
    acceptance_rate = Column(Float, nullable=True)
    status = Column(String, nullable=False)  # completed, abandoned, in_progress
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interactions = relationship("InteractionModel", back_populates="session")
    errors = relationship("ErrorModel", back_populates="session")

class InteractionModel(Base):
    __tablename__ = "interactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    human_prompt = Column(Text, nullable=False)
    claude_response = Column(Text, nullable=False)
    response_length = Column(Integer, nullable=True)
    was_accepted = Column(Boolean, nullable=False)
    was_modified = Column(Boolean, nullable=False)
    modification_count = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    interaction_type = Column(String, nullable=False)  # new_code, refactor, bugfix, explanation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("SessionModel", back_populates="interactions")
    errors = relationship("ErrorModel", back_populates="interaction")
    metrics = relationship("CodeMetricsModel", back_populates="interaction")

class ErrorModel(Base):
    __tablename__ = "errors"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    interaction_id = Column(String, ForeignKey("interactions.id"), nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    error_type = Column(String, nullable=False)  # syntax, runtime, type, logic
    error_message = Column(Text, nullable=False)
    language = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # low, medium, high
    was_resolved_in_next_interaction = Column(Boolean, nullable=True)
    recovery_interactions_count = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interaction = relationship("InteractionModel", back_populates="errors")
    session = relationship("SessionModel", back_populates="errors")

class CodeMetricsModel(Base):
    __tablename__ = "code_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    interaction_id = Column(String, ForeignKey("interactions.id"), nullable=False)
    cyclomatic_complexity = Column(Float, nullable=True)
    lines_of_code = Column(Integer, nullable=True)
    function_count = Column(Integer, nullable=True)
    class_count = Column(Integer, nullable=True)
    max_nesting_depth = Column(Integer, nullable=True)
    has_type_hints = Column(Boolean, nullable=True)
    code_quality_score = Column(Float, nullable=True)
    language = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interaction = relationship("InteractionModel", back_populates="metrics")
```

---

## Pydantic Schemas (for API validation & responses)

Used in FastAPI endpoints:

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class InteractionSchema(BaseModel):
    id: str
    session_id: str
    sequence_number: int
    timestamp: datetime
    human_prompt: str
    claude_response: str
    was_accepted: bool
    was_modified: bool
    modification_count: Optional[int]
    interaction_type: str

class ErrorSchema(BaseModel):
    id: str
    error_type: str
    error_message: str
    severity: str
    recovery_interactions_count: Optional[int]

class CodeMetricsSchema(BaseModel):
    cyclomatic_complexity: Optional[float]
    lines_of_code: Optional[int]
    code_quality_score: Optional[float]

class SessionSchema(BaseModel):
    id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    language: str
    project_name: Optional[str]
    acceptance_rate: Optional[float]
    status: str
    interaction_count: int
    error_count: int

class SessionDetailSchema(SessionSchema):
    interactions: List[InteractionSchema]
    errors: List[ErrorSchema]
    metrics: List[CodeMetricsSchema]
```

---

## Migration & Initialization

When monitor starts, it:
1. Checks if `data/` directory exists, creates if not
2. Checks if `sessions.db` exists
3. If not, executes `shared/db_schema.sql` to create all tables
4. If yes, validates schema integrity
5. Begins logging sessions

**No manual migrations needed** - SQLAlchemy handles this automatically.
