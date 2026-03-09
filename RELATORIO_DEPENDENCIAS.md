# Relatório de Análise de Dependências

## 1. Pacotes Desatualizados

O projeto define suas restrições de versão no arquivo `requirements.txt`. Todas as dependências principais possuem limitadores (`<`) que atualmente impedem a atualização para as versões "major" e "minor" mais recentes:

- **Streamlit**: Definido como `streamlit>=1.30.0,<1.45.0`.
  - **Instalado/Atual**: `~1.44.1`
  - **Mais Recente Disponível**: `1.55.0`
- **Plotly**: Definido como `plotly>=5.18.0,<6.0.0`.
  - **Instalado/Atual**: `~5.24.1`
  - **Mais Recente Disponível**: `6.6.0`
- **Pandas**: Definido como `pandas>=2.1.4,<3.0.0`.
  - **Instalado/Atual**: `~2.3.3`
  - **Mais Recente Disponível**: `3.0.1`

_Bibliotecas embutidas desatualizadas pelo travamento de versões_: cachetools, protobuf, pillow, altair.

**Recomendação Específica de Atualização do `requirements.txt`:**
Ajuste os limitadores para suportar as versões finais utilizando o gerenciador `uv`, substituindo o conteúdo do arquivo por algo menos restritivo ou usando o padrão caret (`^`) se migrar para `pyproject.toml`. Para `requirements.txt`:

```txt
streamlit>=1.55.0
plotly>=6.6.0
pandas>=3.0.0
```

## 2. Vulnerabilidades de Segurança

A verificação foi executada utilizando ferramentas de auditoria no escopo das bibliotecas atuais:

- **Status**: Nenhuma vulnerabilidade crítica ou CVEs (Common Vulnerabilities and Exposures) registrados ativos para as versões pontuais rodando atualmente.
- **Atenção**: Manter bibliotecas defasadas, como o Streamlit 1.44, previne que você receba backports e patches de segurança automaticamente. Atualizar as barreiras de `requirements.txt` é a principal mitigação contínua recomendada.

## 3. Sugestão de Pacotes Alternativos

1. **Gerenciamento de Dependências**: Você está utilizando o `uv` e um `requirements.txt`. Sugiro a migração de `requirements.txt` para um `pyproject.toml`. Isso permite que o `uv` gerencie as versões e gere um `uv.lock`, trazendo reprodutibilidade universal para o projeto.
2. **Banco de Dados**: O projeto opera utilizando SQL cru nativo (`sqlite3`). Conforme o app cresce, o desenvolvimento manual de strings SQL torna-se um gargalo de manutenção e apresenta riscos de injeção lógica.
   - _Alternativa Sugerida_: **SQLModel** ou **SQLAlchemy**. O `SQLModel` acopla Pydantic e SQLAlchemy permitindo trabalhar de maneira extremamente rápida, garantindo tipagem de dados e esquemas validados para o seu sqlite sem complexidade alta.
3. **Qualidade de Código**: O projeto não explicita a adoção central de linters e formatadores.
   - _Alternativa Sugerida_: Incluir o **Ruff** nas dependências de desenvolvimento (`uv add --dev ruff`). Ele formata e aplica linters aos arquivos instantaneamente.

## 4. Revisão dos Padrões de Uso

Foi executada uma revisão sobre a topologia de importações nos scripts (`app.py`, `db.py`, `utils.py`, `test_app.py`, `pages/`):

- **Boas Práticas Observadas**: O uso de alias na importação está padronizado (`import pandas as pd`, `import plotly.express as px`, `import streamlit as st`), seguindo todas as normas do ecossistema de Data Science via Python (PEP 8 recomendadas).
- **Tratamento de Exceções em BD**: O controle de I/O de arquivos (`json`, banco) é feito manualmente de forma muito solta em alguns utilitários, misturados com bibliotecas de interface gráfica (Streamlit). É recomendado remover lógica pesada de I/O das páginas do `streamlit` e isolar completamente no `db.py` ou `utils.py`, delegando as views do Streamlit somente para exibição de dados e injeção do controller, para separar "Lógica de Negócios" de "Visualização".
