# Agente Copilot para Azure Functions (serverless)

> **Aviso:** este projeto é material de estudo independente. Não possui afiliação, patrocínio ou endosso de qualquer organização educacional.

## Visão geral

Este repositório mostra como usar o GitHub Copilot, com arquivos de customização versionados, para desenvolver e publicar uma aplicação serverless em Azure Functions. Ele reúne:

- **Agente Copilot:** instruções do repositório, instruções por escopo, prompt files e um chat mode dedicado a Azure Functions, todos em `.github/`.
- **Projeto de exemplo:** um Function App em Python 3.11 (modelo de programação v2) com uma função HTTP e uma função de temporizador, fila ou blob, com lógica de negócio isolada dos gatilhos.
- **Testes:** `pytest` e `Hypothesis`, executados sem credenciais e sem acesso ao Azure.
- **Infraestrutura como código:** templates Bicep em `infra/`, com identidade gerenciada e permissões de menor privilégio.
- **CI/CD:** workflow do GitHub Actions com autenticação OIDC e verificações de segurança antes do deploy.
- **Documentação:** tutorial passo a passo, avisos éticos e política de segurança.

Antes de usar o Copilot neste projeto, leia o [ETICA.md](ETICA.md). O passo a passo completo está em [docs/tutorial.md](docs/tutorial.md).

## Pré-requisitos

Você precisa de:

1. Conta Azure
2. Assinatura do GitHub Copilot
3. Visual Studio Code (VS Code)
4. Azure Functions Core Tools
5. Azure CLI
6. Git

Os links oficiais de download e cadastro de cada item estão em [docs/tutorial.md](docs/tutorial.md). Para rodar os testes, instale também o Python 3.11.

## Estrutura de pastas

| Caminho | Finalidade |
|---|---|
| `.github/` | Agente Copilot (`copilot-instructions.md`, `instructions/`, `prompts/`, `chatmodes/`), workflow de CI/CD e `dependabot.yml` |
| `src/` | Function App em Python: `function_app.py` (gatilhos), `app/` (validação, lógica de negócio, HTTP, logging seguro e segredos), `host.json`, `local.settings.json.example` e `requirements.txt` |
| `tests/` | Testes unitários e de propriedade (`pytest` e `Hypothesis`) |
| `tools/` | Verificador de segurança e de termos proibidos, validadores de customizações e de documentação, verificador de RBAC |
| `infra/` | Infraestrutura em Bicep (`main.bicep` e parâmetros) |
| `docs/` | Tutorial, descrição das customizações e solução de problemas |
| `ETICA.md` | Avisos éticos sobre o uso de IA |
| `SECURITY.md` | Política de segurança |
| `LICENSE` | Licença do projeto |

## Início rápido

Execute os comandos na raiz do repositório.

1. Instale as dependências:

   ```powershell
   pip install -r requirements-dev.txt
   pip install -r src/requirements.txt
   ```

2. Rode os testes (não exigem credenciais nem acesso ao Azure):

   ```powershell
   python -m pytest -q
   ```

3. Copie `src/local.settings.json.example` para `src/local.settings.json` e substitua os placeholders. Nunca versione esse arquivo nem coloque Segredos nele no repositório.

4. Inicie o Function App localmente, a partir da pasta `src`:

   ```powershell
   cd src
   func start
   ```

Para criar funções com o Copilot, publicar no Azure e resolver problemas, siga o [tutorial](docs/tutorial.md).

## Licença

Consulte o arquivo [LICENSE](LICENSE).
