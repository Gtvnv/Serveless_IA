# Customizações do GitHub Copilot

Este documento descreve cada arquivo de customização existente em `.github/`. Cada entrada traz o nome do arquivo, o propósito e um exemplo de uso. Para conferir se todos os arquivos estão documentados, execute `python tools/validar_documentacao.py`.

## Instruções gerais

### **`copilot-instructions.md`**

**Propósito:** reúne as diretrizes que valem para todo o repositório: stack (Python 3.11 e Azure Functions v2), estrutura de pastas, convenções de código, comandos de build e teste, regras para Segredos e recusa de código malicioso. O Copilot lê este arquivo automaticamente em todas as conversas. As respostas são sempre em português do Brasil.

**Exemplo de uso:** peça no chat "Crie uma função utilitária para formatar datas". O Copilot segue as convenções do arquivo (`snake_case`, type hints, docstring curta) e sugere `python -m pytest -q` para testar.

## Instruções por tipo de arquivo (`.github/instructions/`)

### **`azure-functions.instructions.md`**

**Propósito:** define regras para o código em `src/**/*.py`: gatilhos finos, lógica de negócio em funções puras, validação de entrada, logging seguro e leitura de Segredos somente de variáveis de ambiente, App Settings ou Key Vault. É aplicado automaticamente aos arquivos Python de `src/`.

**Exemplo de uso:** ao editar `src/function_app.py` e pedir "Adicione um campo `nome` ao corpo da requisição", o Copilot valida o campo na borda HTTP, devolve HTTP 400 em caso de erro e não registra o conteúdo completo do payload nos logs.

### **`workflows.instructions.md`**

**Propósito:** define regras para os workflows do GitHub Actions em `.github/workflows/`: login no Azure com OIDC, `permissions` mínimas, uso de `secrets.*` e `vars.*` e execução do verificador e dos testes antes do deploy. É aplicado automaticamente aos arquivos `.yml` e `.yaml` dessa pasta.

**Exemplo de uso:** ao abrir um workflow e pedir "Adicione um job de deploy", o Copilot cria o job com `needs:` apontando para os testes, `environment:` e `id-token: write` somente nesse job.

## Prompts reutilizáveis (`.github/prompts/`)

Os prompts são executados no chat do Copilot digitando `/` seguido do nome do arquivo, sem o sufixo `.prompt.md`.

### **`criar-http-trigger.prompt.md`**

**Propósito:** gera uma função Azure Functions com trigger HTTP, com validação de entrada e ao menos um teste automatizado. Antes de gerar qualquer arquivo, pede o nome da função, a rota e os métodos HTTP.

**Exemplo de uso:** no chat, digite `/criar-http-trigger` e responda com `pedidos`, rota `pedidos` e método `POST`. O Copilot cria o gatilho, a validação e o teste correspondente.

### **`criar-trigger-temporizador-fila-blob.prompt.md`**

**Propósito:** gera uma função orientada a eventos, com trigger de temporizador, fila ou blob. Antes de gerar código, pergunta qual dos três tipos usar e pede o nome da função.

**Exemplo de uso:** digite `/criar-trigger-temporizador-fila-blob`, escolha "Temporizador" e informe a expressão NCRONTAB `0 */5 * * * *` para executar a rotina a cada 5 minutos.

### **`deploy-azure.prompt.md`**

**Propósito:** prepara e executa o deploy do Function_App no Azure. Verifica os pré-requisitos (ferramentas, sessão ativa, infraestrutura, testes e verificador de segurança) antes de qualquer comando de publicação.

**Exemplo de uso:** digite `/deploy-azure` e informe o nome do Function App, o grupo de recursos, a assinatura e a região. O Copilot reporta cada pré-requisito como atendido ou pendente antes de publicar.

### **`gerar-testes.prompt.md`**

**Propósito:** gera testes automatizados em `tests/` para uma função existente, com casos de sucesso e de falha de validação e, quando fizer sentido, testes baseados em propriedades com Hypothesis. Os testes rodam sem credenciais e sem recursos reais do Azure.

**Exemplo de uso:** digite `/gerar-testes` e informe `executar_rotina_periodica` (em `src/app/negocio.py`). O Copilot cria os testes e roda `pytest`.

### **`revisar-seguranca.prompt.md`**

**Propósito:** revisa a segurança de uma função e produz uma lista de achados, cada um com arquivo analisado, risco e correção recomendada. Apenas lê e reporta, sem alterar arquivos sem pedido explícito.

**Exemplo de uso:** digite `/revisar-seguranca` e informe `pedidos_http`. O Copilot verifica Segredos, nível de autorização, validação, logs e privilégios, e lista os achados.

## Modos de chat (`.github/chatmodes/`)

### **`azure-functions.chatmode.md`**

**Propósito:** ativa um modo de chat especializado em desenvolvimento, configuração e deploy de Azure Functions. Pedidos fora desse escopo são recusados. Antes de qualquer ação que altere o Azure, o modo explica a finalidade, lista os recursos afetados e pede confirmação explícita.

**Exemplo de uso:** selecione o modo "azure-functions" no seletor de modos do chat e peça "Publique o Function App". O Copilot descreve o comando e os recursos afetados e só executa depois de você responder "sim".
