# Deploy GayATCU to Streamlit Community Cloud

## Overview

This guide covers deploying the GayATCU (TCU study tracker with Spaced Repetition System) to Streamlit Community Cloud, including configuration, monitoring, and troubleshooting.

## Prerequisites

- **GitHub repository** with your code
- **Streamlit Community Cloud account** (free at share.streamlit.io)
- **Python 3.11+** (Community Cloud usa 3.12 por padrão)
- **pyproject.toml + uv.lock** no root do repositório (estratégia única de dependências)

## Deploy Steps

### 1. Prepare Repository

```bash
# Verify dependency manager files (uv)
ls pyproject.toml uv.lock

# Verify lockfile is in sync
uv lock --check

# Verify Python version
grep "requires-python" pyproject.toml
# Should show: requires-python = ">=3.11" (or higher)

# Verify config file
cat .streamlit/config.toml
```

### 2. Push to GitHub

```bash
git add pyproject.toml uv.lock .streamlit/config.toml monitoring.py DEPLOYMENT.md README.md
git commit -m "chore: prepare for Streamlit Cloud deploy"
git push origin main
```

### 3. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select your GitHub repository
4. Configure deployment:
   - **Main file path**: `app.py`
   - **Python version**: 3.12 (default) ou outra versão suportada em **Advanced settings**
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
uv sync
uv run python -c "import streamlit, pandas, plotly, sqlmodel; print('OK')"
```

## Success Criteria

- [x] pyproject.toml and uv.lock present and synchronized
- [x] .streamlit/config.toml configured for cloud
- [x] monitoring.py module created with psutil fallback
- [x] DEPLOYMENT.md documentation complete
- [ ] App deployed successfully on Streamlit Cloud
