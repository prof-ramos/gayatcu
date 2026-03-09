# 📘 GayATCU - Dashboard de Estudos TCU

Dashboard profissional para acompanhamento de estudos do concurso TCU 2021 com sistema de repetição espaçada.

## 🎯 Funcionalidades

- **Dashboard Principal**: Métricas em tempo real do progresso
- **Checklist Interativo**: Marque 345 tópicos como estudados
- **Sistema de Revisões**: Repetição espaçada automática (24h → 7d → 15d → 30d)
- **Estatísticas**: Gráficos interativos e exportação de dados
- **Tema Dark**: Interface profissional e confortável

## 🚀 Como Usar

### 1. Iniciar o Dashboard

```bash
# Navegue até o diretório onde o projeto foi clonado
cd <seu-diretorio-de-clone>
streamlit run app.py
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

- **345 tópicos** organizados em 17 disciplinas
- **2 seções principais**: Conhecimentos Gerais e Específicos
- **Sistema SRS**: Revisões agendadas automaticamente

## 🔧 Tecnologias

- **Streamlit 1.28+**: Framework web
- **SQLite**: Banco de dados
- **Plotly**: Gráficos interativos
- **Python 3.10+**: Linguagem (testado com 3.13)

## 📦 Instalação

```bash
# Certifique-se de estar no diretório do projeto clonado
pip install -r requirements.txt
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

## 🚀 Deploy na Nuvem

Quer acessar seu dashboard de qualquer lugar? Faça o deploy no Streamlit Community Cloud!

### Deploy Rápido

1. **Prepare o repositório**
   ```bash
   git add .
   git commit -m "feat: preparar para deploy"
   git push origin main
   ```

2. **Acesse Streamlit Cloud**
   - Vá para [https://share.streamlit.io](https://share.streamlit.io)
   - Clique em "New app"
   - Selecione seu repositório `gayatcu`
   - Deploy automatico! 🎉

### Documentação Completa

📖 **[Guia Detalhado de Deploy](DEPLOYMENT.md)**

O guia completo inclui:
- ✅ Passo a passo detalhado
- 🔧 Configuração do GitHub
- 📊 Monitoramento e logs
- 🛠️ Troubleshooting de erros
- 💡 Boas práticas e otimização

### Vantagens do Deploy

- 🌐 Acesso de qualquer dispositivo
- 📱 Interface mobile-friendly
- 🔄 Atualizações automáticas
- 📈 Métricas de uso
- 💾 Dados persistentes (com configuração adequada)

### Links Úteis

- [Streamlit Community Cloud](https://streamlit.io/cloud)
- [Documentação Oficial](https://docs.streamlit.io)
- [Exemplos de Apps](https://streamlit.io/gallery)

---

**Bons estudos! 🎓**
