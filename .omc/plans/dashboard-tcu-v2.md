# Dashboard de Estudos TCU V2 - Implementation Plan

**Project:** GayATCU - TCU Exam Study Dashboard
**Date:** 2026-03-09
**Scope:** Complete Feature Set (MVP + Advanced Features)
**Complexity:** MEDIUM

---

## Context

This project is a Streamlit-based study tracking dashboard for TCU (Tribunal de Contas da União) exam preparation. The dashboard will help students track their progress through 345 study topics organized across 17 subsections.

**Existing Assets:**

- `/Users/gabrielramos/gayatcu/conteudo.json` - Complete study content with 345 topics
- Python 3.13 virtual environment already configured
- Git repository initialized

**Data Structure (conteudo.json):**

```json
[
  {
    "titulo": "CONHECIMENTOS GERAIS",
    "subsecoes": [
      {
        "titulo": "LÍNGUA PORTUGUESA",
        "topicos": [
          {
            "codigo": "1",
            "titulo": "Interpretação de texto...",
            "aulas_direcao": "",
            "questoes": "",
            "revisao": ""
          }
        ]
      }
    ]
  }
]
```

**Important:** `conteudo.json` is an ARRAY of section objects, not a single object. Each array element represents a main section (e.g., "CONHECIMENTOS GERAIS", "CONHECIMENTOS ESPECÍFICOS", etc.).

---

## Work Objectives

### Primary Goals

1. Build a complete Streamlit dashboard with 4 main pages
2. Implement SQLite database for progress tracking
3. Create spaced repetition review system (24h/7d/15d/30d intervals)
4. Generate statistics and progress visualizations

### Success Criteria

- [ ] Dashboard loads and displays all 345 topics from conteudo.json
- [ ] Users can mark topics as complete with timestamps
- [ ] Review page shows topics due for spaced repetition
- [ ] Statistics page shows progress by section and overall completion
- [ ] Data persists across sessions in SQLite database
- [ ] Application can be deployed locally or to a platform supporting SQLite (e.g. Heroku/GCP)

---

## Architecture

### Technology Stack

- **Framework:** Streamlit 1.28+
- **Database:** SQLite3 (built-in Python)
- **Language:** Python 3.13
- **UI Components:** Streamlit native widgets, Plotly for charts

### Project Structure

```
gayatcu/
├── app.py                  # Main Streamlit application
├── db.py                   # SQLite database layer
├── utils.py                # Helper functions (data loading, calculations)
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml         # Streamlit configuration
├── pages/
│   ├── 1_📋_Checklist.py   # Checklist page
│   ├── 2_📅_Revisões.py    # Reviews/SRS page
│   └── 3_📊_Estatísticas.py # Statistics page
├── data/
│   └── study_tracker.db    # SQLite database (auto-created)
├── conteudo.json           # Study content (existing)
└── README.md               # Documentation
```

### Database Schema

```sql
-- Topics table
CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    secao TEXT NOT NULL,
    subsecao TEXT NOT NULL,
    titulo TEXT NOT NULL,
    UNIQUE(codigo, secao, subsecao)
);

-- Progress tracking
CREATE TABLE progress (
    topic_id INTEGER PRIMARY KEY,
    completed_at TIMESTAMP,
    last_reviewed_at TIMESTAMP,
    review_count INTEGER DEFAULT 0,
    next_review_date DATE,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);

-- Performance indexes (CRITICAL for query performance)
CREATE INDEX idx_next_review ON progress(next_review_date);
CREATE INDEX idx_codigo ON topics(codigo);
CREATE INDEX idx_secao_subsecao ON topics(secao, subsecao);
CREATE INDEX idx_topic_id_progress ON progress(topic_id);

-- (Tabela progress já foi definida antes dos índices)

-- Review log
CREATE TABLE review_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interval_days INTEGER,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);
```

---

## Security Requirements

### SQL Injection Prevention (MANDATORY)

**CRITICAL:** ALL database operations MUST use parameterized queries with `?` placeholders. NEVER interpolate user input directly into SQL strings.

**Correct (Parameterized):**

```python
cursor.execute(
    "SELECT * FROM topics WHERE codigo = ? AND secao = ?",
    (codigo, secao)
)
```

**Incorrect (Vulnerable to SQL Injection):**

```python
# NEVER DO THIS
cursor.execute(f"SELECT * FROM topics WHERE codigo = '{codigo}' AND secao = '{secao}'")
```

**All CRUD operations in `db.py` must follow this pattern:**

- `mark_topic_complete()`: Use `?` for topic_id
- `get_topics_due_for_review()`: Use `?` for date parameter
- `mark_review_complete()`: Use `?` for topic_id and interval
- `import_topics_from_json()`: Use `?` for all INSERT values

### Connection Management (MANDATORY)

**CRITICAL:** Cache database connection in `st.session_state` to avoid re-initializing on every rerun.

**Implementation Pattern:**

```python
# In app.py and all page files
def get_db():
    """Get or create cached database connection"""
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = init_db()
    return st.session_state.db_conn

# Use throughout the app
conn = get_db()
```

---

## Guardrails

### Must Have (Non-Negotiable)

- SQLite database for data persistence
- Streamlit multi-page architecture
- Spaced repetition algorithm (24h → 7d → 15d → 30d)
- All 345 topics loaded from conteudo.json
- Portuguese language UI
- Mobile-responsive layout

### Must NOT Have

- No external authentication required (single-user local app)
- No cloud database dependencies (SQLite file-based only)
- No hardcoded content - everything from conteudo.json
- No ORM - use raw SQLite3 for simplicity
- No JavaScript custom widgets (Streamlit native only)

---

## Deployment Strategy

### LOCAL-ONLY DEPLOYMENT (Selected Approach)

**Decision:** This application is designed for LOCAL USE ONLY.

**Rationale:**

- Streamlit Cloud resets filesystem on each deployment, losing SQLite data
- Single-user use case doesn't justify cloud database complexity
- User data privacy is maintained locally
- Simpler architecture, faster development

**Deployment Model:**

```bash
# User runs locally
source .venv/bin/activate
streamlit run app.py
```

**Data Persistence:**

- SQLite database stored in `data/study_tracker.db`
- User responsible for backing up their data
- Export functionality provided (Phase 7) for manual backups

**NOT Supported:**

- Streamlit Cloud deployment (data loss on redeploy)
- Multi-user access
- Cloud database sync

**Future Enhancement Path** (if cloud deployment is needed later):

- Replace SQLite with PostgreSQL via `st.connection()`
- Add user authentication
- Implement session management

---

## Task Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Project Setup & Configuration                            │
│    - Create directory structure                             │
│    - Set up requirements.txt                                │
│    - Configure Streamlit                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ 2. Database Layer (db.py)                                   │
│    - Initialize SQLite database                             │
│    - Create schema                                          │
│    - Import topics from conteudo.json                       │
│    - CRUD operations for progress                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ 3. Utilities & Helpers (utils.py)                           │
│    - Load conteudo.json                                     │
│    - Calculate next review dates                            │
│    - Progress calculations                                  │
│    - Date formatting helpers                                │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ 4. Main Application (app.py)                                │
│    - Session state initialization                           │
│    - Database initialization on first run                   │
│    - Main page (overview & quick stats)                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ 5. Checklist Page (pages/1_📋_Checklist.py)                 │
│    - Display topics grouped by section/subsection           │
│    - Checkbox for each topic                                │
│    - Save progress to database                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ 6. Reviews Page (pages/2_📅_Revisões.py)                    │
│    - Spaced repetition logic                                │
│    - Show topics due for review                             │
│    - Mark reviews as complete with interval update          │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ 7. Statistics Page (pages/3_📊_Estatísticas.py)             │
│    - Progress charts (completion rate)                      │
│    - Progress by section                                    │
│    - Review schedule visualization                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ 8. Testing & Deployment                                     │
│    - Local testing                                          │
│    - Create deployment documentation                        │
│    - Streamlit Cloud deployment guide                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed TODOs

### Phase 1: Project Setup (Est. 30 min)

**Task 1.1: Create Directory Structure**

- [ ] Create `pages/` directory
- [ ] Create `data/` directory
- [ ] Create `.streamlit/` directory
- [ ] Add `.gitignore` entry for `data/*.db` and `*.db-shm` and `*.db-wal`

**Acceptance Criteria:**

```bash
# Verify structure exists
ls -la pages/ .streamlit/ data/
```

**Task 1.2: Create requirements.txt**

- [ ] Add `streamlit>=1.28.0`
- [ ] Add `plotly>=5.18.0`
- [ ] Add `pandas>=2.0.0`

**Acceptance Criteria:**

```bash
# File exists with correct dependencies
cat requirements.txt
```

**Task 1.3: Configure Streamlit**

- [ ] Create `.streamlit/config.toml`
- [ ] Set app title to "GayATCU - Dashboard de Estudos TCU"
- [ ] Configure theme colors
- [ ] Enable wide mode

**Acceptance Criteria:**

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
[client]
showErrorDetails = false
[logger]
level = "info"
```

---

### Phase 2: Database Layer (Est. 1 hour)

**Task 2.1: Create db.py Module**

- [ ] Implement `init_db()` function
- [ ] Create tables (topics, progress, review_log)
- [ ] Add `import_topics_from_json()` function
- [ ] Implement CRUD operations

**Acceptance Criteria:**

```python
# Functions to implement:
def init_db(db_path="data/study_tracker.db") -> sqlite3.Connection
def import_topics_from_json(conn, json_path="conteudo.json") -> int
def mark_topic_complete(conn, topic_id: int) -> bool
def get_topic_progress(conn, topic_id: int) -> dict
def get_all_progress(conn) -> list
def get_topics_due_for_review(conn, date: str) -> list
def mark_review_complete(conn, topic_id: int, interval: int) -> bool
def get_statistics(conn) -> dict
```

**Parameterized Query Requirements:**

```python
# ALL database operations MUST use parameterized queries
def mark_topic_complete(conn, topic_id: int) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO progress (topic_id, completed_at, next_review_date) VALUES (?, datetime('now'), date('now', '+1 day'))",
        (topic_id,)  # Parameterized with ?
    )
    conn.commit()
    return True

def get_topics_due_for_review(conn, date: str) -> list:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT t.*, p.review_count FROM topics t JOIN progress p ON t.id = p.topic_id WHERE p.next_review_date <= ?",
        (date,)  # Parameterized with ?
    )
    return cursor.fetchall()
```

**Task 2.2: Data Import Logic**

- [ ] Parse conteudo.json structure (ARRAY of section objects)
- [ ] Map sections → "secao" field (iterate over array)
- [ ] Map subsections → "subsecao" field
- [ ] Map topics with codigo and titulo
- [ ] Handle duplicates gracefully (INSERT OR IGNORE)

**Array Iteration Pattern:**

```python
def import_topics_from_json(conn, json_path="conteudo.json") -> int:
    with open(json_path, 'r', encoding='utf-8') as f:
        sections = json.load(f)  # This is an ARRAY

    cursor = conn.cursor()
    count = 0

    for section in sections:  # Iterate over array
        secao = section['titulo']
        for subsection in section['subsecoes']:
            subsecao = subsection['titulo']
            for topic in subsection['topicos']:
                cursor.execute(
                    "INSERT OR IGNORE INTO topics (codigo, secao, subsecao, titulo) VALUES (?, ?, ?, ?)",
                    (topic['codigo'], secao, subsecao, topic['titulo'])
                )
                count += 1

    conn.commit()
    return count
```

**Acceptance Criteria:**

```python
# Test import
conn = init_db()
count = import_topics_from_json(conn)
assert count == 345  # All topics imported
```

---

### Phase 3: Utilities (Est. 30 min)

**Task 3.1: Create utils.py Module**

- [ ] `load_content()` - Load and validate conteudo.json
- [ ] `calculate_next_review(current_interval, success)` - SRS algorithm
- [ ] `format_date(date_str)` - Portuguese date formatting
- [ ] `get_completion_percentage(conn)` - Calculate overall progress
- [ ] `get_section_progress(conn)` - Progress by section

**Spaced Repetition Algorithm:**

```python
INTERVALS = [1, 7, 15, 30]  # days
def calculate_next_review(current_level: int, success: bool) -> int:
    if success and current_level < len(INTERVALS) - 1:
        return INTERVALS[current_level + 1]
    elif success:
        return INTERVALS[-1]  # Stay at 30 days
    else:
        return INTERVALS[0]  # Reset to 1 day
```

---

### Phase 4: Main Application (Est. 1 hour)

**Task 4.1: Create app.py**

- [ ] Initialize Streamlit page config
- [ ] Set up session state for database connection (cached)
- [ ] Create main page layout
- [ ] Display summary statistics
- [ ] Add quick actions

**Session State Caching Pattern (MANDATORY):**

```python
# At top of app.py
def get_db():
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = init_db()
    return st.session_state.db_conn

# Initialize on first run
conn = get_db()
```

**Main Page Layout:**

```
┌────────────────────────────────────────┐
│  GayATCU - Dashboard de Estudos TCU    │
├────────────────────────────────────────┤
│  📊 Resumo                              │
│  ┌──────────┬──────────┬──────────┐    │
│  │ Completos│ Revisões │  Total   │    │
│  │   45/345 │   12     │  345     │    │
│  └──────────┴──────────┴──────────┘    │
│                                         │
│  📈 Progresso por Seção                │
│  [Bar Chart]                            │
│                                         │
│  📅 Próximas Revisões (Hoje)           │
│  • Tópico X (Língua Portuguesa)        │
│  • Tópico Y (Matemática)               │
└────────────────────────────────────────┘
```

---

### Phase 5: Checklist Page (Est. 1 hour)

**Task 5.1: Create pages/1_📋_Checklist.py**

- [ ] Load content from conteudo.json
- [ ] Display sections and subsections in expandable sections
- [ ] Show checkboxes for each topic
- [ ] Sync checkbox state with database
- [ ] Save changes on checkbox toggle
- [ ] Show completion percentage per subsection

**UI Structure:**

```python
for secao in content:
    with st.expander(f"{secao['titulo']}"):
        for subsecao in secao['subsecoes']:
            st.subheader(subsecao['titulo'])
            for topico in subsecao['topicos']:
                # Checkbox with database sync
                checked = is_topic_complete(topic_id)
                if st.checkbox(topico['titulo'], value=checked):
                    mark_topic_complete(topic_id)
```

---

### Phase 6: Reviews Page (Est. 1.5 hours)

**Task 6.1: Create pages/2_📅_Revisões.py**

- [ ] Load topics due for review today
- [ ] Show review queue grouped by interval type
- [ ] Implement "Mark Review Complete" button
- [ ] Update next_review_date based on SRS algorithm
- [ ] Show upcoming reviews calendar view

**Review Queue Logic:**

```python
# Get topics due today
due_topics = get_topics_due_for_review(conn, datetime.now().date())

# Display with action buttons
for topic in due_topics:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"{topic['titulo']} ({topic['subsecao']})")
    with col2:
        if st.button("Revisar", key=topic['id']):
            mark_review_complete(conn, topic['id'])
            st.rerun()
```

---

### Phase 7: Statistics Page (Est. 1.5 hours)

**Task 7.1: Create pages/3_📊_Estatísticas.py**

- [ ] Overall completion rate donut chart
- [ ] Progress by section bar chart
- [ ] Review schedule timeline
- [ ] Study streak tracker
- [ ] Export data to CSV button

**Charts Required:**

1. Overall Progress (donut chart)
2. Completion by Section (grouped bar chart)
3. Reviews per Week (line chart)
4. Topic Distribution (pie chart)

---

### Phase 8: Testing & Documentation (Est. 1 hour)

**Task 8.1: Local Testing**

- [ ] Test database initialization
- [ ] Test all 345 topics load correctly
- [ ] Test checkbox functionality
- [ ] Test review system with all intervals
- [ ] Test statistics calculations
- [ ] Test mobile responsiveness

**Task 8.2: Create README.md**

- [ ] Project description
- [ ] Installation instructions
- [ ] Usage guide
- [ ] Deployment instructions

**Task 8.3: Deployment Preparation**

- [ ] Create `deploy.sh` script for Streamlit Cloud
- [ ] Add `.streamlit/credentials.toml` template
- [ ] Document environment variables

---

## Integration with Existing conteudo.json

### Data Loading Process

```python
def load_and_import_content():
    """Load conteudo.json and import into database"""
    with open('conteudo.json', 'r', encoding='utf-8') as f:
        content = json.load(f)

    conn = init_db()
    imported = import_topics_from_json(conn, content)
    return imported
```

### Content Mapping

| JSON Field                                        | Database Field | Notes                             |
| ------------------------------------------------- | -------------- | --------------------------------- |
| sections[i].titulo                                | secao          | Main section (iterate over array) |
| sections[i].subsecoes[j].titulo                   | subsecao       | Subsection/Discipline             |
| sections[i].subsecoes[j].topicos[k].codigo        | codigo         | Topic ID                          |
| sections[i].subsecoes[j].topicos[k].titulo        | titulo         | Topic title                       |
| sections[i].subsecoes[j].topicos[k].aulas_direcao | -              | Not used currently                |
| sections[i].subsecoes[j].topicos[k].questoes      | -              | Not used currently                |
| sections[i].subsecoes[j].topicos[k].revisao       | -              | Not used currently                |

**Key Point:** `conteudo.json` is an array `[{...}, {...}]`, not a single object. Code must iterate over the array.

---

## Testing Strategy

### Unit Tests (Manual)

1. **Database Tests**
   - [ ] Verify all 345 topics import correctly
   - [ ] Test duplicate handling
   - [ ] Test progress CRUD operations

2. **SRS Algorithm Tests**
   - [ ] Verify interval progression (1→7→15→30)
   - [ ] Verify reset on failed review
   - [ ] Verify next_review_date calculation

3. **UI Tests**
   - [ ] Verify all checkboxes render
   - [ ] Verify state persistence
   - [ ] Verify statistics calculations

### Integration Tests

1. **End-to-End Workflow**
   - [ ] Complete first topic → Verify shows in reviews tomorrow
   - [ ] Complete review → Verify interval increases
   - [ ] Mark 100% of section → Verify statistics update

---

## Deployment Guide

### Local Development (Recommended)

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run app.py
```

**Why Local-Only:**

- SQLite database persists on local filesystem
- No data loss on application restart
- Privacy - study data stays on your machine
- No cloud database costs or complexity

### Streamlit Cloud Deployment (NOT SUPPORTED)

**DO NOT deploy to Streamlit Cloud** with this architecture:

- Cloud deployment loses SQLite data on each redeploy
- Single SQLite file is not suitable for cloud hosting
- Would require migration to PostgreSQL/MySQL

**If cloud deployment is needed in the future:**

1. Replace SQLite with `st.connection()` to PostgreSQL
2. Add user authentication
3. Implement multi-user session management
4. Redesign database schema for multiple users

### Environment Variables (Optional)

```
DB_PATH=data/study_tracker.db
CONTENT_PATH=conteudo.json
```

### Backup Strategy

Users should regularly backup:

1. `data/study_tracker.db` - Main database
2. Use export button in Statistics page (Phase 7) for CSV backup

---

## Success Criteria Validation

| Criterion            | How to Verify                                      |
| -------------------- | -------------------------------------------------- |
| All 345 topics load  | Check statistics page shows 345 total              |
| Mark topics complete | Use checklist page, verify checkbox persists       |
| Review system works  | Complete topic, verify appears in reviews next day |
| Statistics accurate  | Cross-check manual count with dashboard stats      |
| Data persists        | Close app, reopen, verify progress saved           |
| Deployment ready     | Can run `streamlit run app.py` without errors      |

---

## Open Questions

_All critical architectural decisions have been resolved. The following are optional enhancements for future consideration:_

1. **Cloud Migration** — If cloud deployment becomes a requirement, redesign with PostgreSQL and multi-user support
2. **Enhanced Authentication** — Currently single-user local app; add auth if sharing is needed
3. **Advanced Backup** — Current plan includes basic CSV export; consider automated backups if needed

---

## Next Steps

Once this plan is approved:

1. Create the directory structure
2. Implement Phase 2 (Database Layer) first as it's the foundation
3. Build out each phase sequentially
4. Test after each phase completion
5. Deploy to Streamlit Cloud for final validation

---

**Plan Created:** 2026-03-08
**Last Revised:** 2026-03-08 (Architect Feedback Incorporated)
**Estimated Total Time:** 8 hours
**Status:** Revised - Ready for Implementation
