Starting CodeRabbit review in plain text mode...

Connecting to review service
Setting up
Analyzing
Reviewing

============================================================================
File: pyproject.toml
Line: 22 to 24
Type: nitpick

Prompt for AI Agent:
Verify each finding against the current code and only fix it if needed.

In @pyproject.toml around lines 22 - 24, A configuração atual em [tool.ruff.lint] usa uma seleção muito restrita (select = ["E4","E7","E9","F"]); expanda essa chave select para ativar um conjunto mais abrangente de regras (por exemplo incluir categorias como "E","F","W","C","B","S","D","I","UP" ou usar "ALL") e, opcionalmente, adicione chaves úteis na mesma seção como extend-select, ignore, line-length e per-file-ignores; edite a seção [tool.ruff.lint] no pyproject.toml para substituir o valor atual de select por essa configuração mais completa e ajustar ignores/line-length conforme o estilo do projeto.


