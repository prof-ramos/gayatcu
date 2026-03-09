# 🚀 Guia de Deploy - GayATCU

Guia completo para deploy do GayATCU no Streamlit Community Cloud.

## 📋 Índice

- [Pré-requisitos](#pré-requisitos)
- [Preparação do Repositório](#preparação-do-repositório)
- [Deploy no Streamlit Cloud](#deploy-no-streamlit-cloud)
- [Configuração do GitHub](#configuração-do-github)
- [Monitoramento e Logs](#monitoramento-e-logs)
- [Troubleshooting](#troubleshooting)
- [Boas Práticas](#boas-práticas)

## 🎯 Pré-requisitos

### Contas Necessárias

- **GitHub**: [Criar conta](https://github.com/signup)
- **Streamlit Community Cloud**: [Criar conta](https://streamlit.io/cloud) (use sua conta GitHub)

### Requisitos do Projeto

- Repositório Git público ou privado no GitHub
- Arquivo `requirements.txt` atualizado
- Arquivo `app.py` como ponto de entrada
- Dependências compatíveis com Linux x86/x64

## 📦 Preparação do Repositório

### 1. Verificar Estrutura do Projeto

```bash
# Estrutura mínima necessária:
gayatcu/
├── .git/
├── .gitignore
├── app.py              # Arquivo principal
├── requirements.txt    # Dependências
├── README.md          # Documentação
├── data/              # Diretório para dados (criado automaticamente)
├── db.py              # Banco de dados
├── session.py         # Gerenciamento de sessão
└── utils.py           # Funções auxiliares
```

### 2. Validar requirements.txt

Certifique-se de que seu `requirements.txt` está completo:

```bash
# Visualizar requirements.txt
cat requirements.txt
```

**Conteúdo esperado:**

```txt
streamlit>=1.28.0
plotly>=5.18.0
```

### 3. Commit e Push das Alterações

```bash
# Adicionar todas as alterações
git add .

# Commit com mensagem descritiva
git commit -m "feat: preparar projeto para deploy no Streamlit Cloud"

# Push para o GitHub
git push origin main
```

### 4. Verificar .gitignore

Certifique-se de que o `.gitignore` está configurado corretamente:

```bash
# Visualizar .gitignore
cat .gitignore
```

**Conteúdo recomendado:**

```gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.env
.venv
env/
venv/
ENV/
data/*.db
data/*.db-journal
.DS_Store
```

## 🌐 Deploy no Streamlit Cloud

### Passo 1: Acessar Streamlit Cloud

1. Acesse [https://share.streamlit.io](https://share.streamlit.io)
2. Clique em **"Sign up"** ou **"Log in"**
3. Autorize o acesso à sua conta GitHub

### Passo 2: Criar Novo App

1. Clique no botão **"New app"**
2. Preencha o formulário:

   **Repository:**
   - Selecione seu repositório `gayatcu`

   **Branch:**
   - Selecione `main` (ou sua branch principal)

   **Main file path:**
   - Digite: `app.py`

   **App URL (opcional):**
   - Deixe em branco para usar URL automática
   - Ou personalize: `seu-nome-gayatcu`

3. Clique em **"Deploy"**

### Passo 3: Aguardar Deploy

- O deploy leva 2-5 minutos na primeira vez
- Você verá logs em tempo real
- Ao final, seu app estará disponível em: `https://seu-app.streamlit.app`

## 🔗 Configuração do GitHub

### Integrar com GitHub (Opcional)

Para deploys automáticos a cada push:

1. No Streamlit Cloud, vá em **Settings** do seu app
2. Selecione **"Connected GitHub repository"**
3. Configure:
   - **Auto-deploy**: Ative para deploy automático
   - **Branch to deploy**: `main`
   - **Python version**: `3.10` ou superior

### Webhooks (Avançado)

Para notificações de deploy:

```bash
# No seu repositório GitHub:
# Settings → Webhooks → Add webhook
# URL: https://streamlit.io/cloud-webhook
```

## 📊 Monitoramento e Logs

### Acessar Logs

1. No Streamlit Cloud, selecione seu app
2. Clique em **"Manage app"**
3. Vá para **"Logs"**

### Tipos de Logs

- **Recent Logs**: Últimas 100 linhas
- **Full Logs**: Logs completos da sessão
- **Download Logs**: Baixar logs para análise

### Métricas Disponíveis

- **Visitors**: Número de visitantes únicos
- **Page Views**: Total de visualizações
- **Run Time**: Tempo de execução
- **CPU Usage**: Uso de CPU
- **Memory Usage**: Uso de memória

### Alertas

Configure alertas de uso:

1. Vá em **Settings** → **Monitoring**
2. Configure limites de:
   - CPU (recomendado: alerta em 80%)
   - Memória (recomendado: alerta em 85%)
   - Tempo de resposta

## 🔧 Troubleshooting

### Erro: Module Not Found

**Sintoma:**
```
ModuleNotFoundError: No module named 'plotly'
```

**Solução:**
1. Verifique se `requirements.txt` está no repositório
2. Confirme que todas as dependências estão listadas
3. Faça um novo commit com `requirements.txt` atualizado
4. Redeploy no Streamlit Cloud

### Erro: File Not Found

**Sintoma:**
```
FileNotFoundError: data/study_tracker.db
```

**Solução:**
1. O diretório `data/` é criado automaticamente
2. Verifique se o código trata a criação do diretório:
```python
import os
os.makedirs('data', exist_ok=True)
```

### Erro: App Não Inicia

**Sintoma:** App mostra "Application not responding"

**Solução:**
1. Verifique os logs completos
2. Procure por erros de import ou sintaxe
3. Teste localmente: `streamlit run app.py`
4. Corrija erros e faça novo commit

### Erro: Timeout

**Sintoma:** App demora muito para carregar

**Solução:**
1. Otimize consultas ao banco de dados
2. Adicione cache com `@st.cache_data`
3. Reduza tamanho dos dados carregados
4. Use paginação para listas grandes

### Erro: Dependências Conflitantes

**Sintoma:**
```
ERROR: ResolutionImpossible
```

**Solução:**
1. Use versões específicas em `requirements.txt`:
```txt
streamlit==1.28.0
plotly==5.18.0
```
2. Teste localmente com:
```bash
pip install -r requirements.txt
```

### App Funciona Localmente Mas Não na Nuvem

**Causas comuns:**

1. **Caminhos relativos**
```python
# ERRADO
df = pd.read_csv('data.csv')

# CORRETO
import os
BASE_DIR = os.path.dirname(__file__)
df = pd.read_csv(os.path.join(BASE_DIR, 'data.csv'))
```

2. **Variáveis de ambiente**
```python
# Use variáveis de ambiente para dados sensíveis
import os
api_key = os.getenv('API_KEY', 'default_value')
```

3. **Banco de dados**
- SQLite funciona, mas os dados são voláteis
- Considere usar Banco de Dados externo para produção

## 💡 Boas Práticas

### Performance

1. **Use Cache Inteligentemente**
```python
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_data():
    # Código caro
    return data
```

2. **Evite Recálculos**
```python
# Use st.session_state para manter estado
if 'df' not in st.session_state:
    st.session_state.df = load_data()
```

3. **Otimize Gráficos**
```python
# Limite quantidade de pontos
fig = px.line(df[:1000], x='date', y='value')
```

### Segurança

1. **Nunca commit credenciais**
```python
# ERRADO
api_key = "sk-1234567890"

# CORRETO
api_key = st.secrets["API_KEY"]
```

2. **Use .streamlit/secrets.toml** para dados sensíveis
```toml
# .streamlit/secrets.toml
[database]
username = "admin"
password = "senha_secreta"
```

3. **Valide Inputs do Usuário**
```python
user_input = st.text_input("Digite algo")
if not user_input or len(user_input) > 100:
    st.error("Input inválido")
```

### Manutenção

1. **Versionamento Semântico**
```bash
git tag -a v1.0.0 -m "Primeira versão estável"
git push origin v1.0.0
```

2. **Branches de Features**
```bash
git checkout -b feature/nova-funcionalidade
# Desenvolva
git push origin feature/nova-funcionalidade
# Pull request no GitHub
```

3. **Testes Antes do Deploy**
```bash
# Teste localmente
streamlit run app.py

# Verifique requirements
pip check

# Valide sintaxe
python -m py_compile app.py
```

### Backup e Recuperação

1. **Backup Automático do Banco**
```python
import os
import shutil
from datetime import datetime

backup_dir = "backups"
os.makedirs(backup_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(
    "data/study_tracker.db",
    f"{backup_dir}/backup_{timestamp}.db"
)
```

2. **Exportação de Dados**
- Use a página de Estatísticas para exportar CSV
- Agende backups regulares se usar dados persistentes

3. **Monitoramento de Saúde**
```python
import time
import psutil

def health_check():
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent

    if cpu_percent > 90:
        st.warning(f"Alto uso de CPU: {cpu_percent}%")

    if memory_percent > 90:
        st.warning(f"Alto uso de memória: {memory_percent}%")
```

## 🔄 Atualizações e Manutenção

### Atualizar o App

1. Faça alterações localmente
2. Teste: `streamlit run app.py`
3. Commit e push:
```bash
git add .
git commit -m "feat: nova funcionalidade"
git push origin main
```
4. Streamlit Cloud fará deploy automático (se configurado)

### Rollback

Se algo der errado:

```bash
# Voltar ao commit anterior
git log --oneline
git revert HEAD
git push origin main
```

Ou no Streamlit Cloud:
- Settings → Deploy History
- Selecione versão anterior
- Clique em "Redeploy"

## 📚 Recursos Adicionais

- [Documentação Oficial Streamlit](https://docs.streamlit.io)
- [Streamlit Community Cloud](https://streamlit.io/cloud)
- [Guia de Deploy](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-your-app)
- [Best Practices](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-your-app#best-practices)

## 🆘 Suporte

Se encontrar problemas:

1. Verifique os [logs completos](#monitoramento-e-logs)
2. Consulte a [documentação oficial](https://docs.streamlit.io)
3. Busque no [GitHub Discussions](https://github.com/streamlit/streamlit/discussions)
4. Verifique issues do projeto

---

**Última atualização:** 2026-03-08
