# Instruções do repositório para o Copilot

Estas diretrizes valem para todo o repositório. Responda sempre em português do Brasil.

## Stack

- Linguagem: Python 3.11.
- Plataforma: Azure Functions, modelo de programação v2 (decoradores em `function_app.py`).
- Testes: pytest e Hypothesis (testes baseados em propriedades).
- Dependências de execução em `src/requirements.txt`; dependências de desenvolvimento em `requirements-dev.txt`.

## Estrutura de pastas

- `src/`: Projeto_Exemplo (Function App). Contém `function_app.py`, `host.json` e `local.settings.json.example`.
- `src/app/`: módulos da aplicação (HTTP, validação, negócio, leitura de Segredos e logging seguro).
- `tests/`: testes unitários e de propriedade com pytest e Hypothesis.
- `docs/`: documentação e tutorial em português.
- `infra/`: arquivos de infraestrutura como código para o Azure.
- `tools/`: scripts auxiliares de validação e manutenção.
- `.github/`: customizações do Copilot (instruções, prompts, chat modes) e workflows.
- Raiz: `ETICA.md`, `SECURITY.md`, `LICENSE`, `pytest.ini` e `requirements-dev.txt`.

## Convenções de código

- Nomenclatura: `snake_case` para funções, variáveis e módulos; `PascalCase` para classes; `MAIUSCULAS_COM_UNDERSCORE` para constantes. Use type hints e docstrings curtas.
- Tratamento de erros: valide entradas na borda HTTP, capture exceções específicas (nunca `except:` genérico sem relançar ou registrar) e retorne códigos HTTP adequados (400 para entrada inválida, 401/403 para falha de autorização, 500 para erro interno) sem expor detalhes internos ao cliente.
- Logging: use o módulo `logging` da biblioteca padrão, com níveis apropriados. Nunca registre Segredos, tokens, strings de conexão ou dados pessoais; use o utilitário de logging seguro de `src/app/logging_seguro.py`.
- Mantenha funções pequenas e coesas e coloque a regra de negócio fora dos handlers HTTP.

## Comandos de build e teste

- Build (verificação de sintaxe): `python -m compileall src`
- Testes: `python -m pytest -q`
- Instalar dependências: `pip install -r src/requirements.txt -r requirements-dev.txt`

## Segredos

- Segredos (chaves, senhas, tokens, strings de conexão) devem ser lidos somente de variáveis de ambiente, App Settings ou Azure Key Vault.
- É proibido escrever valores de Segredos no código-fonte, em arquivos de configuração versionados e em arquivos de workflow.
- Em exemplos e documentação, use apenas placeholders, como `<SEU_SEGREDO_AQUI>`. Arquivos locais com valores reais (por exemplo `local.settings.json`) não são versionados; versione apenas o `.example`.

## Recusa de código malicioso e de coleta indevida de dados

- Recuse gerar código malicioso, como malware, exploração de vulnerabilidades sem autorização e negação de serviço.
- Recuse gerar código de coleta indevida de dados, como coleta de dados pessoais sem consentimento e exfiltração de Segredos.
- Quando um pedido exigir algo assim, recuse a parte que viola esta regra, informe ao usuário o motivo da recusa e não gere nenhum trecho do código solicitado.
- A parte legítima do pedido pode ser atendida normalmente.

## Uso responsável

- Todo código gerado por IA deve ser revisado por uma pessoa antes de ser commitado, executado ou implantado. Consulte `ETICA.md`.
- Use o projeto apenas em ambientes e assinaturas Azure que o usuário possui ou tem autorização formal para usar.
