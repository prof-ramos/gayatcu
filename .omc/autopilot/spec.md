# Spec: Deploy GayATCU para Streamlit Community Cloud

## Overview
Preparar o aplicativo GayATCU (sistema de acompanhamento de estudos TCU com Spaced Repetition) para deploy na Streamlit Community Cloud seguindo as melhores práticas da documentação oficial.

## Current State Analysis

### Arquitetura Atual
- **Backend**: SQLite + SQLModel ORM
- **Frontend**: Streamlit multi-page app
- **Dependencies**: Gerenciadas via uv (pyproject.toml)
- **Features**:
  - Dashboard com métricas de progresso
  - Checklist de tópicos com cache @st.cache_data
  - Sistema de revisões com SRS
  - Estatísticas com gráficos Plotly
  - SessionStateManager centralizado

### Estado Recentemente Atualizado (Fase 2A)
- Performance: 50-70% mais rápido com cache
- UX: Diálogos de confirmação @st.dialog
- Organização: st.tabs para navegação
- Código: SessionStateManager para state

## Requirements para Deploy

### 1. Gerenciamento de Dependências
**Problema**: Projeto usa uv (pyproject.toml) mas Streamlit Cloud requer requirements.txt

**Solução**:
- Criar requirements.txt exportado do pyproject.toml
- Pin versão do Streamlit (best practice)
- Incluir todas as dependências transitórias

### 2. Configuração de Recursos
**Problema**: Limites da Streamlit Community Cloud (Feb 2024)
- CPU: 0.078-2 cores
- Memory: 690MB-2.7GB
- Storage: 50GB max

**Solução**:
- Otimizar uso de memória
- Implementar cache eviction policy
- Adicionar resource monitoring
- Prevenir memory leaks

### 3. Configuração do App
**Problema**: Configurações não documentadas para cloud

**Solução**:
- Criar .streamlit/config.toml apropriado
- Configurar logging apropriado
- Definir timeouts e limits
- Setup theme consistente

### 4. Deploy Configuration
**Problema**: Setup inicial para deploy

**Solução**:
- Criar/verificar .streamlit/config.toml
- Documentar processo de deploy
- Adicionar README com instruções
- Configurar GitHub integration

## Technical Specification

### 1. Dependency Management

#### File: requirements.txt
```txt
# Core
streamlit==1.40.0
sqlmodel==0.0.22
sqlalchemy==2.0.36

# Visualization
plotly==5.24.1
pandas==2.2.3

# Data Validation
pydantic==2.10.4

# Utilities
python-dateutil==2.9.0

# Logging
python-json-logger==3.2.1
```

**Rationale**:
- Streamlit pinned para evitar breaking changes
- SQLModel + SQLAlchemy para ORM
- Plotly para gráficos interativos
- Pandas para manipulação de dados

### 2. Resource Optimization

#### Memory Management Strategy
- **Cache Limits**: TTL máximo de 5 minutos
- **Session State Cleanup**: Limpar estados não utilizados
- **Database Connection**: Pool de conexões limitado
- **Chart Caching**: Cache de 2 minutos para figuras

#### Implementation: monitoring.py
```python
import streamlit as st
import psutil
import gc

def monitor_memory_usage():
    """Monitor and display memory usage."""
    process = psutil.Process()
    mem_info = process.memory_info()

    st.sidebar.metric("Memory Usage", f"{mem_info.rss / 1024 / 1024:.1f} MB")

    # Warn if approaching limit
    if mem_info.rss > 2.0 * 1024 * 1024 * 1024:  # 2GB
        st.warning("⚠️ Approaching memory limit")

def cleanup_session_state():
    """Clean up unused session state entries."""
    if hasattr(st, 'session_state'):
        # Remove old cache entries
        keys_to_remove = []
        for key in st.session_state.keys():
            if key.startswith('_cache_data_'):
                keys_to_remove.append(key)

        for key in keys_to_remove[:10]:  # Limit cleanup
            del st.session_state[key]

        # Force garbage collection
        gc.collect()
```

### 3. Streamlit Configuration

#### File: .streamlit/config.toml
```toml
[theme]
base = "dark"
primaryColor = "#22c55e"
backgroundColor = "#0f172a"
secondaryBackgroundColor = "#1e293b"
textColor = "#f1f5f9"
font = "sans serif"

[client]
showErrorDetails = false
toolbarMode = "minimal"

[server]
runOnSave = true
maxUploadSize = 200
headless = true

[logger]
level = "info"

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = 8501
```

### 4. Deployment Documentation

#### File: DEPLOYMENT.md
```markdown
# Deploy GayATCU to Streamlit Community Cloud

## Prerequisites
- GitHub repository with code
- Streamlit Community Cloud account
- requirements.txt in repository root

## Deploy Steps

1. **Prepare Repository**
   ```bash
   # Export dependencies
   uv pip freeze > requirements.txt

   # Verify files
   ls -la requirements.txt .streamlit/config.toml
   ```

2. **Push to GitHub**
   ```bash
   git add requirements.txt .streamlit/config.toml
   git commit -m "chore: prepare for Streamlit Cloud deploy"
   git push origin main
   ```

3. **Deploy on Streamlit Cloud**
   - Go to share.streamlit.io
   - Click "New app"
   - Select repository
   - Main file path: `app.py`
   - Click "Deploy"

## Post-Deploy Configuration

### Monitoring
- Access "Manage app" from lower-right corner
- Check Cloud logs for errors
- Monitor resource usage

### Resource Management
- If "😦 Oh no." appears:
  1. Check Cloud logs
  2. Reboot app from "Manage app"
  3. Optimize memory usage

### Keeping App Awake
- Apps hibernate after 12h inactivity
- Visit app periodically to keep awake
- Or set up external pings

## Troubleshooting

### Memory Issues
```python
# In app.py, add memory monitoring
from monitoring import monitor_memory_usage

def main():
    monitor_memory_usage()
    # ... rest of app
```

### Dependency Errors
```bash
# Verify requirements.txt locally
uv pip install -r requirements.txt
streamlit run app.py
```

### Slow Performance
- Check cache hit rates
- Reduce TTL values
- Implement pagination for large datasets
```

## Success Criteria

### Functional Requirements
- [ ] requirements.txt criado com dependências corretas
- [ ] .streamlit/config.toml configurado
- [ ] App deployed com sucesso na Streamlit Cloud
- [ ] App responsivo sem erros de memória
- [ ] Logs acessíveis via "Manage app"

### Performance Requirements
- [ ] Memória < 2GB em uso normal
- [ ] Page load time < 5s
- [ ] Cache hit rate > 70%
- [ ] No memory leaks detectados

### Documentation Requirements
- [ ] DEPLOYMENT.md completo
- [ ] README.md atualizado com link para deploy
- [ ] Documentação de troubleshooting incluída

## Edge Cases and Limitations

### Resource Limits
- **Memory**: 2.7GB máximo → Implementar cache eviction
- **CPU**: 2 cores máximo → Otimizar queries pesadas
- **Storage**: 50GB → SQLite database dentro dos limites

### Concurrency
- **Multi-user**: SQLite suporta concorrência limitada
- **Session State**: Cada usuário tem estado isolado
- **Cache**: Compartilhado entre sessões (usar com cuidado)

### Data Persistence
- **Database**: SQLite file não persiste entre deploys
- **Solution**: Considerar migração para PostgreSQL se necessário
- **Workaround**: Exportar dados periodicamente

## Technical Debt and Future Improvements

### Short Term (Post-Deploy)
1. Implementar health check endpoint
2. Adicionar uptime monitoring
3. Configurar backup automático do SQLite

### Medium Term
1. Migrar para PostgreSQL Production
2. Implementar autenticação de usuários
3. Adicionar rate limiting

### Long Term
1. Multi-tenancy com múltiplos usuários
2. Sincronização cross-device
3. Export/import de dados

## Open Questions

1. **Database Persistence**: SQLite é suficiente ou precisamos de PostgreSQL?
2. **User Authentication**: App é single-user ou multi-user?
3. **Data Backup**: Como garantir backup automático dos dados?
4. **Custom Domain**: Necessário domínio customizado?

## Dependencies

### External Services
- Streamlit Community Cloud
- GitHub (para deploy contínuo)

### Internal Components
- db.py: Camada de dados
- session.py: Gerenciamento de estado
- utils.py: Funções utilitárias
- components/charts.py: Visualizações

## Timeline Estimate

- **Phase 1** (Dependencies): 30 min
- **Phase 2** (Config): 1 hour
- **Phase 3** (Deploy): 30 min
- **Phase 4** (Testing): 1 hour
- **Phase 5** (Documentation): 1 hour

**Total**: ~4 hours
