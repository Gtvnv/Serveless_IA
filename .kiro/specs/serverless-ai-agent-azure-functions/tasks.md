# Implementation Plan: Agente de IA Serverless com Azure Functions

## Overview

A implementação segue a ordem: estrutura base, núcleo de lógica pura em Python 3.11 (validação, negócio, logging seguro, segredos, adaptadores HTTP), gatilhos do Azure Functions, ferramentas de verificação em `tools/`, customizações do Agente_Copilot, infraestrutura Bicep, Workflow_CI_CD e documentação em português do Brasil. Os testes usam `pytest` e `Hypothesis` (mínimo de 100 exemplos por propriedade, sem rede e sem Azure).

Regras de trabalho deste plano:
- Todo o trabalho acontece em uma branch de trabalho (por exemplo `feature/agente-copilot-azure-functions`) e chega à `main` somente por Pull Request revisado por uma pessoa. Nenhuma tarefa faz commit ou push na `main`.
- Nenhum arquivo, pasta ou texto pode conter os Termos_Proibidos definidos pelo usuário. A lista fica apenas em `tools/termos_proibidos.txt`.
- Cada teste de propriedade leva o comentário `# Feature: serverless-ai-agent-azure-functions, Property N: <texto>`.

## Tasks

- [x] 1. Estrutura base do repositório
  - [x] 1.1 Criar a estrutura de pastas e arquivos de configuração do Projeto_Exemplo
    - Criar `src/`, `src/app/`, `tests/`, `tools/`, `infra/`, `docs/` e `.github/` com subpastas `instructions/`, `prompts/`, `chatmodes/` e `workflows/`
    - Criar `.gitignore` excluindo `local.settings.json`, `.env`, `.env.*`, `bin/`, `obj/`, `node_modules/`, `.venv/` e `packages/`
    - Criar `LICENSE` (licença de código aberto com ano e titular), `src/host.json`, `src/local.settings.json.example` apenas com placeholders, `src/requirements.txt` (`azure-functions`, `azure-identity`, `azure-keyvault-secrets`), `requirements-dev.txt` (`pytest`, `hypothesis`, `pyyaml`) e `pytest.ini` com `testpaths` e `pythonpath`
    - _Requirements: 4.2, 8.1, 10.7_

  - [x] 1.2 Criar `SECURITY.md` e `ETICA.md`
    - `SECURITY.md`: canal de contato, prazo de resposta inicial de até 5 dias úteis e práticas de gestão de Segredos (armazenamento, rotação, proibição de versionamento)
    - `ETICA.md` com quatro seções: revisão humana do código gerado por IA, o que não enviar em prompts (com exemplo de Segredo, dado pessoal e código proprietário), riscos de erros, vulnerabilidades e licenciamento, e uso apenas em assinaturas Azure autorizadas
    - _Requirements: 8.2, 9.1, 9.2, 9.3, 9.4_

- [x] 2. Núcleo de lógica pura do Projeto_Exemplo
  - [x] 2.1 Implementar modelos e validação em `src/app/validacao.py`
    - Dataclasses `Erro`, `PedidoEntrada` (nome_tarefa 1..256, descricao 0..256, prioridade 1..5, etiquetas até 10 itens de até 32 caracteres) e `ResultadoValidacao`
    - `validar_texto(valor: object)` que nunca lança exceção e `validar_pedido(corpo: bytes)` que rejeita corpo acima de 1 MB e campos de texto acima de 256 caracteres
    - _Requirements: 4.3, 4.8, 5.6_

  - [x] 2.2 Escrever teste de propriedade para a validação total
    - Arquivo `tests/test_prop_validacao.py`
    - **Property 1: Validação total**
    - **Validates: Requirements 5.6**

  - [x] 2.3 Implementar lógica de negócio e serialização em `src/app/negocio.py`
    - `processar_pedido(p) -> SaidaPedido`, `serializar(p) -> str` e `desserializar(s) -> PedidoEntrada`
    - Sem dependência do runtime do Azure Functions
    - _Requirements: 4.4, 4.7, 5.7_

  - [x] 2.4 Escrever teste de propriedade para o round-trip de serialização
    - Arquivo `tests/test_prop_serializacao.py`
    - **Property 5: Round-trip de serialização**
    - **Validates: Requirements 5.7**

  - [x] 2.5 Implementar logging seguro em `src/app/logging_seguro.py`
    - `redigir(texto)` que remove Segredos (chaves, connection strings, tokens) e dados pessoais (nome, e-mail, CPF, telefone, endereço)
    - Função de log estruturado com `funcao`, `invocacao`, `tipo_excecao` e `mensagem`, aplicando `redigir`
    - _Requirements: 4.5, 4.6, 8.10_

  - [x] 2.6 Implementar acesso a segredos em `src/app/segredos.py`
    - `obter_segredo(nome, cliente)` sem valor padrão; em qualquer falha do cliente registra erro sem o valor e propaga a exceção
    - _Requirements: 8.8, 8.9_

  - [x] 2.7 Escrever teste de propriedade para falha no Key Vault
    - Arquivo `tests/test_prop_segredos.py`
    - **Property 9: Falha no Key Vault recusa a operação sem valor padrão**
    - **Validates: Requirements 8.9**

  - [x] 2.8 Implementar adaptadores em `src/app/http.py`
    - `tratar_http(req_corpo, invocacao, logger, processar=processar_pedido)`: 413 para corpo acima de 1 MB, 400 com `{"erros":[{"campo","motivo"}]}` sem chamar `processar`, 200 com `Content-Type: application/json`, e 500 genérico com log estruturado para exceções
    - `tratar_evento(payload, invocacao, logger, processar=...)`: registra o erro com os mesmos campos e relança a exceção
    - _Requirements: 4.3, 4.4, 4.5, 4.6, 4.8_

  - [x] 2.9 Escrever teste de propriedade para entrada inválida
    - Arquivo `tests/test_prop_http_invalido.py`
    - **Property 2: Entrada inválida gera 400 sem vazamento**
    - **Validates: Requirements 4.3**

  - [x] 2.10 Escrever teste de propriedade para limites de tamanho
    - Arquivo `tests/test_prop_http_limites.py`
    - **Property 3: Limites de tamanho**
    - **Validates: Requirements 4.8**

  - [x] 2.11 Escrever teste de propriedade para entrada válida
    - Arquivo `tests/test_prop_http_valido.py`
    - **Property 4: Entrada válida gera 200 JSON**
    - **Validates: Requirements 4.4**

  - [x] 2.12 Escrever teste de propriedade para exceção em função HTTP
    - Arquivo `tests/test_prop_http_excecao.py`
    - **Property 6: Exceção em função HTTP gera 500 genérico e log estruturado**
    - **Validates: Requirements 4.5**

  - [x] 2.13 Escrever teste de propriedade para exceção em função não HTTP
    - Arquivo `tests/test_prop_evento_excecao.py`
    - **Property 7: Exceção em função não HTTP é registrada e propagada**
    - **Validates: Requirements 4.6**

  - [x] 2.14 Escrever teste de propriedade para logs sem Segredos nem dados pessoais
    - Arquivo `tests/test_prop_logs.py`
    - **Property 8: Logs não contêm Segredos nem dados pessoais**
    - **Validates: Requirements 8.10**

  - [x] 2.15 Escrever testes unitários da lógica de negócio e dos adaptadores
    - Arquivo `tests/test_unitarios.py`
    - Para cada função de negócio: um caso de sucesso e um de falha de validação; para a função HTTP: resposta 200 com corpo válido e 400 com entrada inválida
    - Os testes não usam rede, credenciais nem o runtime do Azure Functions
    - _Requirements: 4.7, 5.1, 5.2, 5.3, 5.4_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Gatilhos do Azure Functions
  - [x] 4.1 Implementar `src/function_app.py` (modelo de programação v2)
    - Função HTTP com `@app.route(auth_level=FUNCTION)` delegando a `tratar_http`
    - Função de temporizador (ou fila/blob) delegando a `tratar_evento`
    - Gatilhos finos, sem regra de negócio, e nível de autorização diferente de `ANONYMOUS`
    - _Requirements: 4.1, 4.7, 8.11, 8.12_

  - [x] 4.2 Escrever testes de exemplo da estrutura do Projeto_Exemplo
    - Arquivo `tests/test_estrutura_projeto.py`
    - Verificar presença das duas funções, de `host.json`, de `local.settings.json.example` somente com placeholders, de `requirements.txt` e que `auth_level` não é `ANONYMOUS`
    - _Requirements: 4.1, 4.2, 8.11_

- [x] 5. Ferramentas de verificação em `tools/`
  - [x] 5.1 Implementar `tools/verificador_seguranca.py` e `tools/termos_proibidos.txt`
    - Varrer arquivos versionados (`git ls-files`) em busca de padrões de Segredos e de Termos_Proibidos (sem diferenciar maiúsculas) em nomes de arquivos, pastas e conteúdo
    - Imprimir `caminho:linha` sem o valor, retornar código diferente de zero com ocorrência e zero sem ocorrência, sem alterar arquivos
    - Excluir de forma explícita e documentada a própria lista de termos da verificação
    - _Requirements: 8.3, 8.4, 11.1, 11.2, 11.3_

  - [x] 5.2 Escrever teste de propriedade para o verificador de Segredos
    - Arquivo `tests/test_prop_verificador_segredos.py`
    - **Property 10: Verificador de Segredos**
    - **Validates: Requirements 8.3, 8.4**

  - [x] 5.3 Escrever teste de propriedade para o verificador de Termos_Proibidos
    - Arquivo `tests/test_prop_verificador_termos.py`
    - **Property 11: Verificador de Termos_Proibidos**
    - **Validates: Requirements 11.1, 11.2, 11.3**

  - [x] 5.4 Implementar `tools/validar_customizacoes.py`
    - Validar frontmatter: `applyTo` presente, não vazio e com correspondência; `description` não vazio e de até 200 caracteres; `mode` válido; `tools` explícito e sem curinga
    - Relatar caminho e motivo de cada não conformidade
    - _Requirements: 1.6, 2.6, 3.2_

  - [x] 5.5 Escrever teste de propriedade para o validador de customizações
    - Arquivo `tests/test_prop_validador_customizacoes.py`
    - **Property 12: Validador de customizações**
    - **Validates: Requirements 1.6, 2.6, 3.2**

  - [x] 5.6 Implementar `tools/verificar_rbac.py`
    - Ler o JSON compilado do Bicep e reprovar atribuições com escopo de assinatura ou grupo de recursos e as funções Owner, Contributor e User Access Administrator
    - _Requirements: 7.3, 7.8, 7.9_

  - [x] 5.7 Escrever teste de propriedade para o verificador de RBAC
    - Arquivo `tests/test_prop_rbac.py`
    - **Property 13: Verificador de RBAC de menor privilégio**
    - **Validates: Requirements 7.3, 7.8, 7.9**

  - [x] 5.8 Implementar `tools/validar_documentacao.py`
    - Conferir que cada arquivo de customização tem entrada em `docs/customizacoes.md` e reportar o nome dos que faltam
    - _Requirements: 10.3, 10.8_

  - [x] 5.9 Escrever teste de propriedade para o verificador de documentação
    - Arquivo `tests/test_prop_documentacao.py`
    - **Property 14: Verificador de documentação**
    - **Validates: Requirements 10.3, 10.8**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Customizações do Agente_Copilot
  - [x] 7.1 Criar `.github/copilot-instructions.md`
    - Quatro seções: stack, estrutura de pastas, convenções de código e comandos de build e teste
    - Regra de Segredos (somente variáveis de ambiente, App Settings ou Key Vault) e regra de recusa de código malicioso e de coleta indevida de dados
    - Tamanho máximo de 50 KB, UTF-8
    - _Requirements: 1.1, 1.2, 1.3, 9.6_

  - [x] 7.2 Criar as Instrucoes_Escopo em `.github/instructions/`
    - `azure-functions.instructions.md` com `applyTo: "src/**/*.py"`
    - `workflows.instructions.md` com `applyTo: ".github/workflows/*.{yml,yaml}"`
    - _Requirements: 1.4, 1.5_

  - [x] 7.3 Criar os cinco Prompt_Files em `.github/prompts/`
    - `criar-http-trigger`, `criar-trigger-temporizador-fila-blob`, `gerar-testes`, `deploy-azure` e `revisar-seguranca`, cada um com `description` de até 200 caracteres e `mode` válido
    - Usar placeholders como `<NOME_DO_SEGREDO>`, pedir dados obrigatórios ausentes sem alterar arquivos e proibir gravar ou repetir Segredos informados no chat
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

  - [x] 7.4 Criar `.github/chatmodes/azure-functions.chatmode.md`
    - Escopo exclusivo em Azure Functions, `tools` com lista explícita sem curinga
    - Explicar finalidade e recursos afetados antes de comandos que alteram o Azure, exigir confirmação explícita e não agir sem resposta afirmativa
    - Respostas em português do Brasil
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 7.5 Escrever testes de exemplo das customizações
    - Arquivo `tests/test_customizacoes.py`
    - Verificar seções, regras, cinco Prompt_Files (um por tarefa), Chat_Mode e execução de `validar_customizacoes.py` sem não conformidades
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 9.6_

- [x] 8. Infraestrutura como código
  - [x] 8.1 Criar `infra/main.bicep` e `infra/main.bicepparam`
    - Recursos exatos: Function_App com identidade gerenciada de sistema, plano de hospedagem, conta de armazenamento e Application Insights
    - `httpsOnly: true`, `minTlsVersion: '1.2'`, parâmetros para nomes, região e SKU, sem Segredos
    - RBAC com `principalId` da identidade e escopo no recurso, dependendo da criação dele, sem Owner, Contributor ou User Access Administrator
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [x] 8.2 Escrever teste de exemplo do Bicep
    - Arquivo `tests/test_bicep.py`
    - Compilar com `bicep build` (ignorar se a CLI não existir), checar recursos, identidade, HTTPS, TLS 1.2, parâmetros, ausência de Segredos e executar `verificar_rbac.py`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.8, 7.9_

- [x] 9. Workflow_CI_CD e Dependabot
  - [x] 9.1 Criar `.github/workflows/ci-cd.yml`
    - Etapas em ordem: checkout, verificador de segurança e de termos, instalação de dependências, compilação (`python -m compileall`), testes (`pytest`), login OIDC (`azure/login` com IDs vindos de `secrets` ou `vars`) e publicação
    - Job de deploy separado com `needs` do job de testes e `environment: production`, executado apenas em push na branch principal
    - `permissions` somente `contents: read` e `id-token: write`, sem IDs literais nem client secret
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 8.5, 8.6, 11.4, 11.5_

  - [x] 9.2 Criar `.github/dependabot.yml`
    - Verificação semanal de `pip` (em `/src`) e de `github-actions`
    - _Requirements: 8.7_

  - [x] 9.3 Escrever testes de exemplo do workflow
    - Arquivo `tests/test_workflow.py`
    - Análise estática do YAML: ordem das etapas, `permissions`, ausência de IDs literais, OIDC sem client secret, verificador antes do deploy, `environment` e `needs`
    - _Requirements: 6.1, 6.4, 6.5, 6.6, 6.7, 8.5, 11.4_

- [x] 10. Documentação em português do Brasil
  - [x] 10.1 Criar `README.md`
    - Seções: visão geral, pré-requisitos, estrutura de pastas e início rápido, com link para `ETICA.md`
    - Aviso de material de estudo independente, sem afiliação, patrocínio ou endosso de qualquer organização educacional
    - _Requirements: 9.5, 10.1, 11.6_

  - [x] 10.2 Criar `docs/tutorial.md`
    - Cinco seções numeradas: configurar o ambiente, usar o Agente_Copilot, criar funções, testar localmente e fazer deploy
    - Os 6 pré-requisitos (conta Azure, assinatura do GitHub Copilot, VS Code, Azure Functions Core Tools, Azure CLI e Git) cada um com link oficial
    - Diagrama de arquitetura em Mermaid com VS Code, Agente_Copilot, Azure Functions e Azure
    - _Requirements: 10.2, 10.5, 10.6_

  - [x] 10.3 Criar `docs/customizacoes.md`
    - Uma entrada por arquivo de customização com nome, propósito em até 3 frases e ao menos um exemplo de uso
    - _Requirements: 10.3, 10.8_

  - [x] 10.4 Criar `docs/solucao-de-problemas.md`
    - Ao menos 5 problemas comuns, cada um com sintoma e passo de solução
    - Custo mensal estimado em USD do SKU padrão e comando exato para remover todos os recursos provisionados
    - _Requirements: 7.7, 10.4_

  - [x] 10.5 Escrever testes de exemplo da documentação
    - Arquivo `tests/test_documentacao.py`
    - Verificar seções do README e do tutorial, 6 pré-requisitos com link, mínimo de 5 problemas, custo em USD, comando de remoção, aviso de independência, link do `ETICA.md` e execução de `validar_documentacao.py` sem pendências
    - _Requirements: 7.7, 9.5, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 11.6_

- [x] 11. Integração final
  - [x] 11.1 Executar os verificadores sobre o próprio repositório e corrigir pendências
    - Criar `tests/test_repositorio.py` que roda `verificador_seguranca.py` e `validar_customizacoes.py` sobre o repositório e exige código de saída 0
    - Corrigir qualquer Segredo, Termo_Proibido ou não conformidade encontrada, sem fazer commit ou push na `main`
    - _Requirements: 8.3, 8.4, 11.1, 11.2_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido.
- Cada tarefa referencia requisitos específicos para rastreabilidade.
- Testes de propriedade validam as 14 propriedades de corretude do design; testes de exemplo validam conteúdo estático.
- O comportamento do modelo de linguagem (Req. 2.7 a 2.9 e 9.7) não tem teste automatizado; fica coberto pela presença das instruções e pela revisão humana descrita em `ETICA.md`.
- A integração com `main` acontece somente por Pull Request revisado por uma pessoa.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1", "2.5", "2.6", "5.1", "5.4", "5.6", "5.8"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.7", "5.2", "5.3", "5.5", "5.7", "5.9"] },
    { "id": 3, "tasks": ["2.4", "2.8"] },
    { "id": 4, "tasks": ["2.9", "2.10", "2.11", "2.12", "2.13", "2.14", "2.15", "4.1"] },
    { "id": 5, "tasks": ["4.2", "7.1", "7.2", "7.3", "7.4", "8.1", "9.1", "9.2"] },
    { "id": 6, "tasks": ["7.5", "8.2", "9.3", "10.1", "10.2", "10.3", "10.4"] },
    { "id": 7, "tasks": ["10.5", "11.1"] }
  ]
}
```
