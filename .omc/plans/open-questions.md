# Open Questions

## Dashboard TCU V2 - 2026-03-08 (REVISED)

### RESOLVED - Architect Feedback Incorporated

- [x] **Deployment Target** — DECIDED: Local-only deployment. Streamlit Cloud not supported due to SQLite persistence issues.
- [x] **Authentication** — DECIDED: Single-user local app, no authentication required.
- [x] **Database Schema** — FIXED: Added indexes for performance (idx_next_review, idx_codigo, idx_secao_subsecao, idx_topic_id_progress).
- [x] **SQL Injection Prevention** — FIXED: Added security section requiring parameterized queries with `?` placeholders.
- [x] **Connection Management** — FIXED: Added session state caching pattern for database connections.
- [x] **JSON Structure** — FIXED: Documented that conteudo.json is an ARRAY, not a single object.
- [x] **Backup Strategy** — DECIDED: Basic CSV export included; user responsible for database file backup.

### Optional Future Enhancements

- [ ] **Cloud Migration** — If cloud deployment becomes a requirement, redesign with PostgreSQL and multi-user support
- [ ] **Enhanced Authentication** — Currently single-user local app; add auth if sharing is needed
- [ ] **Advanced Backup** — Current plan includes basic CSV export; consider automated backups if needed
- [ ] **Mobile Priority** — Is mobile optimization a priority for the UI layout? Streamlit is desktop-first but can be optimized for mobile.
