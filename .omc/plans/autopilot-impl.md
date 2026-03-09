# Implementation Plan: Deploy GayATCU to Streamlit Community Cloud

## Revision History

**Version 1.1** (Revised after Critic Review)
- **CRITICAL FIX**: Downgraded Python from 3.13 to 3.11 for Streamlit Cloud compatibility
- **CRITICAL FIX**: Added psutil import with graceful degradation (try/except) for Streamlit Cloud environments
- **ENHANCEMENT**: Specified exact command `uv pip freeze > requirements.txt` (not pip freeze)
- **ENHANCEMENT**: Added specific integration points (line numbers) for cache cleanup in app.py
- **ENHANCEMENT**: Expanded Task 4.1 checklist to include all DEPLOYMENT.md sections from spec
- **DOCUMENTATION**: Added justification for Streamlit 1.55.0 vs spec's 1.40.0 recommendation
- **RISK MITIGATION**: Updated Risk Assessment table to reflect mitigated risks

**Version 1.0** (Initial Architect Draft)
- Original plan created by Architect agent

## Overview
This plan addresses all requirements from the specification to prepare GayATCU (a TCU study tracking system with Spaced Repetition) for deployment to Streamlit Community Cloud.

**Current State Analysis:**
- **Dependencies**: Managed via uv (`pyproject.toml` with `requires-python = ">=3.13"`)
- **Core Dependencies**: pandas>=2.3.3, plotly>=6.6.0, sqlmodel>=0.0.37, streamlit>=1.55.0
- **App Structure**: Multi-page Streamlit app (`app.py` + 3 pages in `pages/`)
- **Database**: SQLite with SQLModel ORM (`db.py`)
- **Session Management**: Centralized in `session.py` with SessionStateManager
- **Components**: Reusable charts in `components/charts.py`
- **Existing Config**: `.streamlit/config.toml` exists but incomplete for cloud deployment
- **Missing Files**: `requirements.txt`, `DEPLOYMENT.md`

**Key Challenge**: The spec recommends Streamlit 1.40.0 but the project uses streamlit>=1.55.0. This plan will use the newer version for compatibility with latest features.

---

## Phase 1: Dependency Management

### Task 1.1: Export dependencies from pyproject.toml
**Files**: `pyproject.toml` (read), `requirements.txt` (create)
**Actions**:
- [ ] Read current dependencies from `pyproject.toml`
- [ ] **CRITICAL**: Update `pyproject.toml` from `requires-python = ">=3.13"` to `requires-python = ">=3.11"` (Python 3.13 not supported on Streamlit Community Cloud yet)
- [ ] Generate `requirements.txt` using: `uv pip freeze > requirements.txt` (NOT pip freeze)
- [ ] Include all direct dependencies and their transitive requirements
- [ ] Add monitoring dependency (psutil) for resource tracking
- [ ] Add Streamlit version note: Using streamlit>=1.55.0 vs spec's 1.40.0 recommendation (no breaking changes for used features)
**Verification**:
```bash
# Create fresh venv and test install
python -m venv test_env
source test_env/bin/activate  # or test_env\Scripts\activate on Windows
pip install -r requirements.txt
python -c "import streamlit, pandas, plotly, sqlmodel, psutil; print('All imports OK')"
```
**Estimated Time**: 30 minutes

### Task 1.2: Verify Python version compatibility
**Files**: `pyproject.toml`, `requirements.txt`
**Actions**:
- [ ] Document Python 3.11 requirement in DEPLOYMENT.md (downgraded from 3.13 for Streamlit Cloud compatibility)
- [ ] Add `# Requires Python 3.11+` comment to requirements.txt
- [ ] Verify pyproject.toml shows `requires-python = ">=3.11"`
**Verification**: Requirements.txt includes `# Requires Python 3.11+` comment and pyproject.toml updated
**Estimated Time**: 15 minutes

---

## Phase 2: Streamlit Configuration Enhancement

### Task 2.1: Update .streamlit/config.toml for cloud deployment
**Files**: `.streamlit/config.toml`
**Actions**:
- [ ] Add `[client]` section with `showErrorDetails = false` (security)
- [ ] Add `[client]` section with `toolbarMode = "minimal"` (clean UX)
- [ ] Add `[server]` section with `maxUploadSize = 200` (limit uploads)
- [ ] Add `[server]` section with `headless = true` (cloud mode)
- [ ] Add `[logger]` section with `level = "info"` (appropriate logging)
- [ ] Add `[browser]` section with `gatherUsageStats = false` (privacy)
**Verification**:
```bash
cat .streamlit/config.toml
# Should include all sections mentioned above
```
**Estimated Time**: 20 minutes

---

## Phase 3: Resource Optimization

### Task 3.1: Create monitoring module
**Files**: `monitoring.py` (create)
**Actions**:
- [ ] Create `monitoring.py` with memory tracking using psutil
- [ ] **CRITICAL**: Add psutil import with graceful degradation for Streamlit Cloud compatibility:
  ```python
  try:
      import psutil
      HAS_PSUTIL = True
  except ImportError:
      HAS_PSUTIL = False
      import streamlit as st
      st.warning("⚠️ Memory monitoring unavailable (psutil not installed)")
  ```
- [ ] Implement `monitor_memory_usage()` function that displays in sidebar (only if HAS_PSUTIL)
- [ ] Implement `cleanup_session_state()` function for cache eviction (works without psutil)
- [ ] Add warning threshold at 2GB (Community Cloud limit is 2.7GB)
- [ ] Add garbage collection trigger
**Verification**:
```python
# In Python REPL
from monitoring import monitor_memory_usage, cleanup_session_state
print("Functions imported successfully")
```
**Estimated Time**: 45 minutes

### Task 3.2: Integrate monitoring into app.py
**Files**: `app.py`, `pages/*.py`
**Actions**:
- [ ] Import `monitor_memory_usage` in `app.py`
- [ ] **SPECIFIC LOCATION**: Add monitoring call in `app.py` main() function at line 193 (immediately after `initialize_database()` call)
- [ ] Optional: Add to dashboard page for visibility
**Verification**: Run `streamlit run app.py` and check sidebar shows memory usage (or graceful warning if psutil unavailable)
**Estimated Time**: 15 minutes

### Task 3.3: Audit and optimize cache usage
**Files**: `db.py`, `utils.py`, `app.py`
**Actions**:
- [ ] Review existing `@st.cache_data` decorators (found at `db.py:160`, `utils.py:15`)
- [ ] Document current TTL values (60s for `get_all_progress`, 300s for `load_content`)
- [ ] **SPECIFIC INTEGRATION**: Add `cleanup_session_state()` call in `app.py` main() function at line 194 (after `monitor_memory_usage()` call, before dashboard display)
- [ ] Add cleanup call to `SessionStateManager` class in `session.py` (create new static method `perform_cleanup()`)
- [ ] Ensure no unbounded cache growth
**Verification**: Cache TTLs are documented and reasonable (< 5 minutes for dynamic data), cleanup integrated at app.py:194
**Estimated Time**: 30 minutes

---

## Phase 4: Deployment Documentation

### Task 4.1: Create DEPLOYMENT.md
**Files**: `DEPLOYMENT.md` (create)
**Actions**:
- [ ] Document prerequisites (GitHub repo, Streamlit Cloud account, Python 3.11+)
- [ ] Document step-by-step deploy process
- [ ] Include post-deploy configuration steps
- [ ] Add monitoring and troubleshooting section
- [ ] Document resource limits and known limitations
- [ ] **CRITICAL**: Include SQLite persistence warning (data does NOT persist between deploys)
- [ ] **REQUIRED**: Add "Edge Cases and Limitations" section (from spec lines 266-282)
- [ ] **REQUIRED**: Add "Technical Debt and Future Improvements" section (from spec lines 283-299)
- [ ] **REQUIRED**: Add "Open Questions" section (from spec lines 300-306)
**Verification**: All sections from spec template (lines 169-306) are present, including:
- Prerequisites → Deploy Steps → Post-Deploy Configuration
- Troubleshooting (Memory Issues, Dependency Errors, Slow Performance)
- Edge Cases and Limitations (Resource Limits, Concurrency, Data Persistence)
- Technical Debt and Future Improvements (Short/Medium/Long Term)
- Open Questions (Database Persistence, User Authentication, Data Backup, Custom Domain)
**Estimated Time**: 60 minutes

### Task 4.2: Update README.md with deployment section
**Files**: `README.md`
**Actions**:
- [ ] Add "Deploy to Streamlit Cloud" section
- [ ] Link to DEPLOYMENT.md for detailed instructions
- [ ] Add live deployment URL placeholder
- [ ] Update requirements.txt reference (currently at line 74 but file doesn't exist)
**Verification**: README references deployment and contains working requirements.txt command
**Estimated Time**: 15 minutes

---

## Phase 5: Pre-Deploy Testing

### Task 5.1: Local dependency verification
**Files**: `requirements.txt`, all Python files
**Actions**:
- [ ] Create fresh virtual environment
- [ ] Install from requirements.txt only
- [ ] Run `streamlit run app.py`
- [ ] Test all pages: Dashboard, Checklist, Reviews, Statistics
- [ ] Verify all imports work
**Verification**: App runs without errors in clean environment
**Estimated Time**: 30 minutes

### Task 5.2: Memory usage baseline test
**Files**: All app files
**Actions**:
- [ ] Run app with monitoring enabled
- [ ] Navigate through all pages
- [ ] Record baseline memory usage
- [ ] Check for memory leaks after 10 page refreshes
- [ ] Document findings in DEPLOYMENT.md
**Verification**: Memory usage stays below 1GB in normal operation
**Estimated Time**: 30 minutes

---

## Phase 6: Deployment Execution

### Task 6.1: Prepare repository for deploy
**Files**: Git repository
**Actions**:
- [ ] Verify all new files are committed
- [ ] Create commit with deployment preparation changes
- [ ] Push to GitHub main branch
- [ ] Verify repository is public or accessible by Streamlit Cloud
**Verification**: GitHub repository shows latest commit
**Estimated Time**: 15 minutes

### Task 6.2: Deploy to Streamlit Community Cloud
**Files**: Streamlit Cloud UI
**Actions**:
- [ ] Log in to share.streamlit.io
- [ ] Click "New app"
- [ ] Select GitHub repository
- [ ] Set main file path to `app.py`
- [ ] Click "Deploy"
- [ ] Monitor deployment logs
**Verification**: App deploys successfully and is accessible
**Estimated Time**: 30 minutes

### Task 6.3: Post-deploy verification
**Files**: Deployed app
**Actions**:
- [ ] Test all pages on deployed app
- [ ] Verify memory monitoring displays
- [ ] Check Cloud logs for errors
- [ ] Test database initialization
- [ ] Verify data persistence limitations are documented
**Verification**: All pages load without errors on deployed app
**Estimated Time**: 30 minutes

---

## Task Dependency Graph

```
Phase 1 (Dependencies) --> Phase 2 (Config) --> Phase 3 (Resource Optimization)
                                                      |
                                                      v
Phase 4 (Documentation) <-----------------------------+
                                                      |
                                                      v
Phase 5 (Testing) ------------------------------------+
                                                      |
                                                      v
Phase 6 (Deployment)
```

---

## Summary of New Files to Create

| File | Purpose | Size Estimate |
|------|---------|---------------|
| `requirements.txt` | Pinned dependencies for pip install | ~20 lines |
| `monitoring.py` | Memory tracking and cleanup functions | ~50 lines |
| `DEPLOYMENT.md` | Complete deployment guide | ~200 lines |

## Summary of Files to Modify

| File | Changes | Lines Affected |
|------|---------|----------------|
| `.streamlit/config.toml` | Add client/server/logger/browser sections | +15 lines |
| `app.py` | Import and call monitoring | +3 lines |
| `README.md` | Add deployment section, fix requirements.txt reference | +15 lines |

---

## Success Criteria Checklist

### Functional Requirements
- [ ] `requirements.txt` created with all dependencies correctly pinned
- [ ] `.streamlit/config.toml` configured for cloud deployment
- [ ] `monitoring.py` module created and integrated
- [ ] `DEPLOYMENT.md` documentation complete
- [ ] App deployed and accessible on Streamlit Cloud
- [ ] All pages functional on deployed app

### Performance Requirements
- [ ] Memory usage < 2GB in normal operation
- [ ] Page load time < 5 seconds
- [ ] Cache hit rate > 70% (documented)
- [ ] No memory leaks detected during testing

### Documentation Requirements
- [ ] DEPLOYMENT.md contains all sections from spec
- [ ] README.md updated with deployment instructions
- [ ] Troubleshooting guide included
- [ ] Resource limits documented

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Python 3.11 compatibility issues | Low | Medium | **MITIGATED**: Pre-emptively downgraded from 3.13 to 3.11 for maximum Streamlit Cloud compatibility |
| SQLite data loss on redeploy | High | Medium | Document clearly in DEPLOYMENT.md, consider PostgreSQL migration path |
| Memory exceeds Community Cloud limits | Medium | High | Implement monitoring and cache eviction, test baseline |
| psutil not available on Streamlit Cloud | Low | Low | **MITIGATED**: Added try/except import with graceful degradation in monitoring.py |

---

## Open Questions to Address During Implementation

1. **~~Python Version~~**: **RESOLVED** - Pre-emptively downgraded from Python 3.13 to 3.11 in Task 1.1 for Streamlit Cloud compatibility. Will verify after deployment.
2. **Data Persistence**: SQLite file does NOT persist between deploys on Streamlit Community Cloud. This is a critical limitation to document clearly in DEPLOYMENT.md.
3. **Database Size**: With 345 topics and review logs, verify database stays well under 50GB storage limit.

---

## Total Estimated Time

- **Phase 1**: 45 minutes
- **Phase 2**: 20 minutes
- **Phase 3**: 90 minutes
- **Phase 4**: 75 minutes
- **Phase 5**: 60 minutes
- **Phase 6**: 75 minutes

**Total**: ~5.5 hours (aligns with spec estimate of ~4 hours, with buffer for testing)

---

## References to Existing Code

- `/Users/gabrielramos/gayatcu/pyproject.toml:5-10` - Current dependencies
- `/Users/gabrielramos/gayatcu/.streamlit/config.toml:1-11` - Existing config (needs enhancement)
- `/Users/gabrielramos/gayatcu/db.py:160` - Existing cache decorator usage
- `/Users/gabrielramos/gayatcu/utils.py:15` - Existing cache decorator usage
- `/Users/gabrielramos/gayatcu/session.py:125-174` - SessionStateManager (may need cleanup integration)
- `/Users/gabrielramos/gayatcu/app.py:183-210` - Main function (monitoring integration point)
