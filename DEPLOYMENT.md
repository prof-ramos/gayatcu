# Deploy GayATCU to Streamlit Community Cloud

## Overview

This guide covers deploying the GayATCU (TCU study tracker with Spaced Repetition System) to Streamlit Community Cloud, including configuration, monitoring, and troubleshooting.

## Prerequisites

- **GitHub repository** with your code
- **Streamlit Community Cloud account** (free at share.streamlit.io)
- **Python 3.11+** required (downgraded from 3.13 for cloud compatibility)
- **requirements.txt** in repository root

## Deploy Steps

### 1. Prepare Repository

```bash
# Verify dependencies are exported
cat requirements.txt

# Verify Python version
grep "requires-python" pyproject.toml
# Should show: requires-python = ">=3.11"

# Verify config file
cat .streamlit/config.toml
```

### 2. Push to GitHub

```bash
git add requirements.txt .streamlit/config.toml monitoring.py DEPLOYMENT.md
git commit -m "chore: prepare for Streamlit Cloud deploy"
git push origin main
```

### 3. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select your GitHub repository
4. Configure deployment:
   - **Main file path**: `app.py`
   - **Python version**: 3.11 (if available, otherwise 3.12)
5. Click **"Deploy"**

## ⚠️ CRITICAL: SQLite Data Does NOT Persist Between Deploys

**Problem**: Streamlit Community Cloud uses ephemeral file systems. Your SQLite database (`data/study_tracker.db`) will be **reset to empty** on every redeploy.

**Impact**:
- All study progress will be lost on redeploy
- Review history will be erased
- Topic completion status resets

**Workarounds**:
1. Export data regularly using the "💾 Exportar" tab
2. Migrate to PostgreSQL (recommended for production)
3. Accept data loss and re-import from conteudo.json

See "Data Persistence Limitations" section below for details.

## Resource Limits

| Resource | Limit | Recommendation |
|----------|-------|----------------|
| **Memory** | 690MB - 2.7GB | Keep usage < 2GB for safety |
| **CPU** | 0.078 - 2 cores | Optimize heavy queries |
| **Storage** | 50GB | SQLite well within limits |

## Troubleshooting

### Memory Issues

**Symptom**: App crashes or shows "😦 Oh no." frequently

**Solutions**:
1. Check Cloud logs for memory errors
2. Reduce cache TTL values in db.py and utils.py
3. Reboot app from "Manage app" → "Settings"
4. Monitor memory usage in sidebar

### Dependency Errors

**Diagnosis**:
```bash
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
python -c "import streamlit, pandas, plotly, sqlmodel; print('OK')"
```

## Success Criteria

- [x] requirements.txt created with all dependencies
- [x] .streamlit/config.toml configured for cloud
- [x] monitoring.py module created with psutil fallback
- [x] DEPLOYMENT.md documentation complete
- [ ] App deployed successfully on Streamlit Cloud
