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
2. Use remote JSON fallback (SQLite + snapshot remoto)
3. Migrate to PostgreSQL (recommended for production)
4. Accept data loss and re-import from conteudo.json

See "Data Persistence Limitations" section below for details.

## Remote JSON Fallback (S3/R2)

This app supports automatic remote snapshot backup/restore:

- On startup, if local SQLite is empty, the app tries restoring from remote JSON.
- After write operations, the app pushes a fresh JSON snapshot remotely.
- Backup sync is best effort (network failures do not block app usage).

### Streamlit Secrets

Configure secrets in Streamlit Cloud:

```toml
[backup]
json_get_url = "https://<URL-PRESIGNED-GET>"
json_put_url = "https://<URL-PRESIGNED-PUT>"
json_put_method = "PUT" # optional: PUT (default) or POST
```

### Recommended Setup

- Store a single object (e.g. `backup/study_tracker_snapshot.json`) in R2 or S3.
- Generate one pre-signed URL for reading and one for writing this object.
- For local setup, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.

## Supabase/PostgreSQL (Recommended for durable persistence)

This app supports PostgreSQL automatically. If a DB URL is configured, it is used instead of local SQLite.

### Streamlit Secrets (preferred)

```toml
[database]
url = "postgresql+psycopg://<user>:<password>@<host>:6543/postgres?sslmode=require&pgbouncer=true"
```

### Environment variable fallback

```toml
DATABASE_URL = "postgresql+psycopg://<user>:<password>@<host>:6543/postgres?sslmode=require&pgbouncer=true"
```

Notes:
- Keep `sslmode=require`.
- For Supabase pooler, port `6543` with `pgbouncer=true` is recommended.
- Never commit credentials to Git.

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
