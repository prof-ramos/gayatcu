# 📘 GayATCU - Dashboard de Estudos TCU

Dashboard profissional para acompanhamento de estudos do concurso TCU 2021 com sistema de repetição espaçada.

## 🎯 Funcionalidades

- **Dashboard Principal**: Métricas em tempo real do progresso
- **Checklist Interativo**: Marque 344 tópicos como estudados
- **Sistema de Revisões**: Repetição espaçada automática (24h → 7d → 15d → 30d)
- **Estatísticas**: Gráficos interativos e exportação de dados
- **Tema Dark**: Interface profissional e confortável

## 🚀 Como Usar

### 1. Iniciar o Dashboard

```bash
# Navegue até o diretório onde o projeto foi clonado
cd <seu-diretorio-de-clone>
uv run streamlit run app.py
```

O dashboard abrirá automaticamente em: http://localhost:8501

### 2. Primeiros Passos

1. **Explore o Dashboard Principal** - Veja suas métricas gerais
2. **Vá ao Checklist** - Marque os tópicos que você já estudou
3. **Volte amanhã** - Acesse a página de Revisões para consolidar o aprendizado

### 3. Páginas Disponíveis

#### 🏠 Dashboard Principal

- Visão geral do progresso
- Métricas por seção
- Barras de progresso

#### 📋 Checklist

- Marque tópicos como estudados
- Acompanhe conclusão por disciplina
- Filtre por seção/disciplina

#### 📅 Revisões

- Fila de tópicos para revisar hoje
- Marque revisões como concluídas
- Veja próximas revisões no calendário

#### 📊 Estatísticas

- Gráficos de progresso
- Distribuição por seção
- Exporte dados para CSV

## 📊 Estrutura dos Dados

- **344 tópicos** organizados em 17 disciplinas
- **2 seções principais**: Conhecimentos Gerais e Específicos
- **Sistema SRS**: Revisões agendadas automaticamente

## 🔧 Tecnologias

- **Streamlit 1.55+**: Framework web
- **SQLModel**: ORM (SQLAlchemy + Pydantic)
- **SQLite**: Banco de dados
- **Plotly**: Gráficos interativos
- **Pandas**: Manipulação de dados
- **Python 3.11+**: Linguagem (Community Cloud usa 3.12 por padrão)

## 📦 Instalação

```bash
# Instale as dependências com uv
uv sync
```

## 🧪 Testes

```bash
# Rodar todos os testes
uv run pytest tests/ -v

# Rodar apenas testes do banco de dados
uv run pytest tests/test_db.py -v

# Rodar apenas testes de utilitários
uv run pytest tests/test_utils.py -v
```

## 🔍 Qualidade de Código

```bash
# Verificar lint
uv run ruff check .

# Formatar código
uv run ruff format .
```

## 🎓 Sistema de Repetição Espaçada

O sistema agenda automaticamente as revisões:

1. **24h** após estudar um tópico
2. **7 dias** após completar a revisão de 24h
3. **15 dias** após completar a revisão de 7d
4. **30 dias** após completar a revisão de 15d

Se você errar uma revisão, o ciclo reinicia para 24h.

## 💾 Backup dos Dados

Seus dados ficam em `data/study_tracker.db`. Para backup:

**Linux / macOS (Bash):**

```bash
cp data/study_tracker.db data/study_tracker_backup_$(date +%Y%m%d).db
```

**Windows (PowerShell):**

```powershell
Copy-Item data/study_tracker.db "data/study_tracker_backup_$(Get-Date -Format 'yyyyMMdd').db"
```

**Windows (CMD):**
_(O CMD não possui formatação de data nativa simples, use cópia manual)_

```cmd
copy data\study_tracker.db data\study_tracker_backup_manual.db
```

Ou use a exportação na página de Estatísticas.

## 🚀 Deploy para Streamlit Community Cloud

Este aplicativo está preparado para deploy na Streamlit Community Cloud.

### Deploy Rápido

```bash
# 1. Prepare o repositório
git add pyproject.toml uv.lock .streamlit/config.toml monitoring.py DEPLOYMENT.md README.md
git commit -m "chore: prepare for Streamlit Cloud deploy"
git push origin main

# 2. Acesse share.streamlit.io e faça o deploy
# - Selecione seu repositório GitHub
# - Main file path: app.py
# - Python version: 3.12 (default) ou ajuste em Advanced settings
```

### Documentação Completa

Para instruções detalhadas de deployment, consulte **[DEPLOYMENT.md](DEPLOYMENT.md)**.

### ⚠️ Limitação Importante: Persistência de Dados

**O banco de dados SQLite NÃO persiste entre deploys na Streamlit Community Cloud.**

- Seus dados de progresso serão **resetados** a cada novo deploy
- **Solução**: Exporte seus dados regularmente via página "📊 Estatísticas" → "💾 Exportar"
- **Recomendação**: Para produção, considere migrar para PostgreSQL

Veja detalhes completos em [DEPLOYMENT.md](DEPLOYMENT.md#-critical-sqlite-data-does-not-persist-between-deploys).

### Deploy URL

🔗 **[gayatcu.streamlit.app](https://gayatcu.streamlit.app)** *(placeholder - atualize após o primeiro deploy)*

---

**Bons estudos! 🎓**
