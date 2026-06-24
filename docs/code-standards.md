# Code Standards and Conventions

**Project:** World Cup 2026 Intelligence  
**Scope:** Python backend, TypeScript/React frontend, SQL, testing practices  
**Last Updated:** 2026-06-21

---

## 1. Python (Backend, >=3.12)

### 1.1 Style

- **Framework:** Black (implicit; use `black --line-length=100` if enforcing)
- **Linting:** Follow PEP 8; use `pylint` or `flake8` as needed
- **Type hints:** Mandatory for function signatures and return types
- **Imports:** Group stdlib, third-party, then local (isort style)

**Example:**
```python
from typing import Optional, TypedDict
import logging
from datetime import datetime

from sqlalchemy import select, Table
from pydantic import BaseModel, Field

from app.config import settings
from app.data.standings_math import compute_group_table

logger = logging.getLogger(__name__)
```

### 1.2 Naming Conventions

| Category | Convention | Example |
|----------|-----------|---------|
| Variables | `snake_case` | `computed_facts`, `brief_date` |
| Functions | `snake_case` | `compute_group_table()` |
| Classes | `PascalCase` | `BriefState`, `APIFootballClient` |
| Constants | `UPPER_SNAKE_CASE` | `API_FOOTBALL_BASE_URL`, `LIVE_POLL_SECONDS` |
| Modules | `snake_case.py` | `standings_math.py`, `api_football.py` |
| TypedDict keys | `snake_case` | `brief_date`, `tokens_in`, `node_timings` |

### 1.3 Comments

- Minimal comments; code should be self-explanatory
- Comment the **why**, not the **what**
- Single-line (`#`) for brief notes; avoid multi-line blocks

**Good:**
```python
# DST guard: only fire if hour matches and last run was >20h ago
if current_hour == target_hour and (now - last_run) > timedelta(hours=20):
    schedule_brief()
```

**Avoid:**
```python
# Check if the current hour equals the target hour
if current_hour == target_hour:  # This is obvious from the code
```

### 1.4 Pure Functions and Side Effects

**Preferred:** Pure functions in `data/` modules (testable, deterministic)

**Example (standings_math.py):**
```python
def compute_group_table(matches: list[Match]) -> list[TeamRow]:
    """Compute group table deterministically: 3/1/0 pts, tiebreak GD→GF."""
    # No DB access, no logging, no side effects
    # Unit-testable; safe to call multiple times
    ...
```

**I/O separation:** I/O (DB, HTTP) isolated to `repository.py`, `api_football.py`, and FastAPI routes.

### 1.5 Error Handling

**Graceful degradation (Collector pattern):**
```python
try:
    standings = api_football.fetch_standings()
except APIError as e:
    logger.warning("API fetch failed; using cached standings", exc_info=e)
    standings = db.load_last_standings()  # Keep last-good
```

**Retries with exponential backoff:**
```python
@retry(max_attempts=3, backoff_factor=2)
def call_deepseek(prompt: str) -> str:
    """Retry LLM calls; fail after 3 attempts."""
    ...
```

**Upserts are non-fatal:**
```python
# In repository.py:
stmt = insert(matches).values(...).on_conflict_do_update(...)
db.execute(stmt)  # Never raises; silently upserts
```

### 1.6 Testing

**Pytest framework:**
- Test file: `tests/test_<module>.py`
- Fixture: use `conftest.py` for shared setup
- Naming: `test_<function>_<scenario>()` (e.g., `test_compute_group_table_with_ties()`)

**Example:**
```python
def test_compute_group_table_with_ties():
    """Group table tiebreak: same points → GD → GF."""
    matches = [
        Match(home_team_id=1, away_team_id=2, home_goals=1, away_goals=1),
        Match(home_team_id=1, away_team_id=3, home_goals=2, away_goals=0),
    ]
    table = compute_group_table(matches)
    assert table[0].position == 1  # Higher GD
    assert table[1].position == 2
```

**Coverage:** Aim for >=80% on `data/` and `pipeline/` modules; 100% on `standings_math.py`.

### 1.7 Logging

**Config:** `logging_config.py` — non-blocking QueueHandler, INFO+, DB persistent

**Usage:**
```python
log = logging.getLogger(__name__)

log.info("Brief generated", extra={"brief_date": date, "node": "editor"})
log.warning("API key missing; using cached data", exc_info=error)
log.error("Pipeline failed", exc_info=exc, extra={"run_id": run_id})
```

**Whitelisted context fields:**
- `node` (collector, analyst, editor)
- `attempt` (retry count)
- `fixture_id` (match ID)
- `brief_date` (YYYY-MM-DD)
- `run_id` (UUID)

---

## 2. TypeScript / React (Frontend)

### 2.1 Style

- **Language:** TypeScript in strict mode (`strict: true` in tsconfig.json)
- **Linting:** ESLint 9 (strict config)
- **Formatter:** Prettier (optional; Tailwind classnames may vary)
- **Line length:** 100 characters (soft limit)

### 2.2 Naming Conventions

| Category | Convention | Example |
|----------|-----------|---------|
| Variables | `camelCase` | `briefDate`, `matchScore` |
| Functions | `camelCase` | `fetchBriefs()`, `formatTime()` |
| Components | `PascalCase` | `BriefCard`, `LiveMatchCard` |
| Files | `kebab-case` | `brief-card.tsx`, `live-match-card.tsx` |
| Constants | `UPPER_SNAKE_CASE` or `camelCase` | `API_BASE` or `pollIntervalMs` |
| Type aliases | `PascalCase` | `Brief`, `Fixture`, `Standing` |
| Interfaces | `PascalCase` | `BriefProps`, `MatchData` |

### 2.3 File Organization

**Components:**
```
components/
├── brief-card.tsx          # Client component (if interactive)
├── brief-detail.tsx
└── index.ts                # Export barrel (optional)
```

**Utilities:**
```
lib/
├── api.ts                  # All fetch calls
├── time.ts                 # Timezone helpers
├── sparkline.ts            # SVG generation
└── types.ts                # Shared interfaces
```

**Server vs Client:**
```typescript
// Server component (default, in app/)
export default async function BriefPage({ params }) {
  const brief = await fetch(`/api/briefs/${params.date}`);
  return <BriefDetail brief={brief} />;
}

// Client component (in components/)
"use client";
export function LiveMatchCard({ match }) {
  const [score, setScore] = useState(match.homeGoals);
  return <div>{score}</div>;
}
```

### 2.4 Type Safety

**Props interfaces:**
```typescript
interface BriefCardProps {
  brief: Brief;
  onClick?: (date: string) => void;
}

export function BriefCard({ brief, onClick }: BriefCardProps) {
  return <div onClick={() => onClick?.(brief.date)}>{brief.title}</div>;
}
```

**Type imports:**
```typescript
import type { Brief, Fixture } from "@/lib/types";  // Type-only import
import { apiFetch } from "@/lib/api";               // Value import
```

**Avoid `any`:**
```typescript
// Good
const data: Brief | null = await apiFetch("/api/briefs/latest");

// Avoid
const data: any = ...;
```

### 2.5 Server Components

**Default:** Page components are server components (fetch at render time)

**Example:**
```typescript
// app/standings/page.tsx (server)
export default async function StandingsPage({
  searchParams,
}: {
  searchParams: { date?: string };
}) {
  const standings = await apiFetch(
    `/api/standings?date=${searchParams.date || new Date().toISOString().split("T")[0]}`
  );
  return <StandingsTable data={standings} />;
}
```

**Client islands:**
```typescript
// components/logs-view.tsx (client)
"use client";
export function LogsView() {
  const [logs, setLogs] = useState([]);
  useEffect(() => {
    const timer = setInterval(async () => {
      const fresh = await fetch("/api/logs").then((r) => r.json());
      setLogs(fresh);
    }, 10000);
    return () => clearInterval(timer);
  }, []);
  return <LogTable logs={logs} />;
}
```

### 2.6 API Integration

**All fetches in `lib/api.ts`:**
```typescript
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      cache: "no-store",
      ...options,
    });
    return res.ok ? res.json() : null;
  } catch (e) {
    console.error("Fetch error", e);
    return null;
  }
}
```

**Error fallback:**
```typescript
const briefs = (await apiFetch<Brief[]>("/api/briefs")) || [];
return briefs.length > 0 ? <BriefList briefs={briefs} /> : <EmptyState />;
```

### 2.7 Styling

**Tailwind CSS v4:**
```typescript
<div className="flex gap-4 p-4 bg-surface border border-border rounded-lg">
  <span className="text-text-primary">{title}</span>
</div>
```

**Design tokens (CSS custom properties):**
```css
/* app/globals.css */
:root {
  --bg: #060e22;
  --surface: #0a1b3d;
  --primary: #2d6bf6;
  --text-primary: #ffffff;
}

/* Usage */
.card {
  background-color: var(--surface);
  color: var(--text-primary);
}
```

**Avoid inline styles:**
```typescript
// Good
<div className="flex gap-2">

// Avoid
<div style={{ display: "flex", gap: "8px" }}>
```

### 2.8 Comments

**Minimal; explain non-obvious logic only:**
```typescript
// Good
// suppressHydrationWarning: time zone mismatch on SSR (server = UTC, client = AEST)
<div suppressHydrationWarning>
  {formatTimeAEST(new Date())}
</div>

// Avoid
// Format the date
const formatted = formatDate(date);  // This is obvious
```

### 2.9 Testing (Vitest)

**Lib functions only (not components):**
```typescript
// lib/sparkline.test.ts
import { generateSparkline } from "./sparkline";

describe("generateSparkline", () => {
  it("should generate SVG path for line chart", () => {
    const path = generateSparkline([1, 2, 3, 2, 1]);
    expect(path).toMatch(/^M\d+/);  // SVG path
  });
});
```

**Test file naming:** `<module>.test.ts`

---

## 3. SQL and Database

### 3.1 Alembic Migrations

**File naming:** `versions/000N_<descriptive_name>.py` (auto-generated)

**Structure:**
```python
"""Migration: Add team_id to standings."""

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('standings', sa.Column('team_id', sa.Integer(), nullable=False))

def downgrade():
    op.drop_column('standings', 'team_id')
```

**Best practices:**
- One change per migration (schema or seed)
- Downgrade must be reversible
- Test migrations on a copy DB before prod

### 3.2 SQLAlchemy Core

**Explicit over implicit:**
```python
# Good: Core
stmt = select(matches).where(matches.c.status == "completed")
result = db.execute(stmt).fetchall()

# Avoid: ORM (not used in this project)
# result = db.query(Match).filter(Match.status == "completed").all()
```

**Upserts:**
```python
from sqlalchemy import insert
stmt = insert(matches).values(fixture_id=123, score=2).on_conflict_do_update(
    index_elements=['fixture_id'],
    set_=dict(score=2)
)
db.execute(stmt)
```

**Indexes:**
```python
# In migration
op.create_index('ix_app_logs_ts_desc', 'app_logs', ['ts'], postgresql_desc=True)
op.create_index('ix_articles_brief_date', 'articles', ['brief_date'], unique=True)
```

### 3.3 Data Constraints

| Constraint | Pattern | Example |
|-----------|---------|---------|
| Unique | Primary key or index | `articles.brief_date UNIQUE` |
| Foreign key | One-to-many | `matches.team_id → teams.id` |
| NOT NULL | Mandatory field | `matches.status NOT NULL` |
| Default | Auto-fill | `created_at TIMESTAMP DEFAULT NOW()` |

---

## 4. Testing Practices

### 4.1 Coverage Goals

| Layer | Target | Notes |
|-------|--------|-------|
| Pure functions (`data/`, `lib/`) | 100% | Deterministic; easy to test |
| API routes | 80%+ | Mock DB; test happy + error paths |
| LLM nodes | 50%+ | Hard to mock; stub outputs acceptable |
| Components | 50%+ | Vitest for `lib/` functions; manual QA for UI |

### 4.2 Test Isolation

**Avoid shared state:**
```python
# Good: Each test sets up its own data
def test_compute_group_table_empty():
    table = compute_group_table([])
    assert len(table) == 0

def test_compute_group_table_with_matches():
    matches = [...]
    table = compute_group_table(matches)
    assert len(table) > 0
```

**Use fixtures:**
```python
@pytest.fixture
def sample_matches():
    return [Match(...), Match(...)]

def test_scoring(sample_matches):
    table = compute_group_table(sample_matches)
    assert table[0].points == 3
```

### 4.3 Async Testing

**pytest-asyncio for async routes:**
```python
@pytest.mark.asyncio
async def test_briefs_endpoint():
    client = TestClient(app)
    response = await client.get("/api/briefs")
    assert response.status_code == 200
```

---

## 5. Git and Version Control

### 5.1 Commits

**Format:** Conventional commits
```
feat(backend): add H2H tiebreaker to standings math
fix(frontend): suppress hydration warning on time component
docs(deployment): update VM provisioning guide
test(standings): add edge case for tied points and GD
```

**No AI references:** Commits describe the change, not the process.

### 5.2 Branches

- **Feature:** `feat/<description>` (e.g., `feat/live-scores`)
- **Fix:** `fix/<description>` (e.g., `fix/tz-offset`)
- **Docs:** `docs/<description>` (e.g., `docs/api-endpoints`)

**Main is protected:** PR-required, tests must pass.

### 5.3 Secrets

**Never commit:**
- `.env` files
- API keys, tokens, credentials
- Private keys
- Database dumps with real data

**Use `.env.example`:**
```
API_FOOTBALL_KEY=<your-key-here>
DEEPSEEK_API_KEY=<your-key-here>
DATABASE_URL=postgresql+psycopg://...
```

---

## 6. File Size Guidance

- **Python files:** Aim for <500 LOC; split at domain boundaries
- **TypeScript files:** Aim for <300 LOC; components, utilities separate
- **SQL migrations:** One change per file
- **Test files:** Mirror the module being tested

---

## 7. Documentation in Code

**Docstrings (Python):**
```python
def compute_group_table(matches: list[Match]) -> list[TeamRow]:
    """Compute group table from matches.
    
    Tiebreak: points (descending) → GD (descending) → GF (descending).
    H2H not implemented (V1).
    
    Args:
        matches: List of match results in the group.
    
    Returns:
        List of TeamRow, sorted by final position.
    """
```

**JSDoc (TypeScript):**
```typescript
/**
 * Format time as AEST with fallback.
 * @param date - Date to format
 * @returns Formatted time string (e.g., "3:45 PM") or "TBD" if unavailable
 */
export function formatTimeAEST(date: Date): string {
```

---

## 8. Common Patterns

### 8.1 Graceful Degradation

```python
# Collector node
try:
    standings = api_football.fetch_standings()
except APIError:
    logger.warning("API fetch failed; falling back to cached")
    standings = db.load_last_standings()  # Keep brief moving
```

### 8.2 Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2)
)
def call_llm(prompt: str) -> str:
    # Retries 3x, exponential backoff
    ...
```

### 8.3 Type Guards

```typescript
// Ensure data is present before rendering
if (!standing || standing.length === 0) {
  return <EmptyState message="No standing data" />;
}
return <StandingsTable data={standing} />;
```

---

## 9. References

- **Python:** PEP 8, type hints (PEP 484)
- **TypeScript:** TypeScript Handbook (strict mode)
- **SQLAlchemy:** Core docs (not ORM)
- **React:** Server components, client islands
- **Testing:** pytest, Vitest documentation
- **Project README:** `README.md` (quick start, structure overview)
