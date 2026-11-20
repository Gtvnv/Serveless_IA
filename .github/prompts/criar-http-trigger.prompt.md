---
description: Cria uma função Azure Functions com trigger HTTP que responde requisições e inclui ao menos um teste automatizado associado.
mode: agent
---

# Criar função com trigger HTTP

Gere uma nova função Azure Functions com trigger HTTP neste repositório. Responda sempre em português do Brasil, mantendo código, comandos e nomes técnicos na forma original.

## Informações obrigatórias

Antes de qualquer ação, confirme que o desenvolvedor informou:

- `<NOME_DA_FUNCAO>`: nome da função (snake_case);
- `<ROTA>` e `<METODOS_HTTP>`: rota e métodos aceitos;
- se a função expõe dados não públicos (define o nível de autorização).

Se alguma informação obrigatória estiver ausente, peça-a ao desenvolvedor e **não gere nem altere nenhum arquivo** até recebê-la.

## O que gerar

Respeite a arquitetura existente:

1. **Gatilho** em `src/function_app.py`: fino, apenas adapta a requisição e delega a `app.http` (como `pedidos_http`). Sem regra de negócio. Use `auth_level=func.AuthLevel.FUNCTION` (ou superior) quando houver dados não públicos; evite `ANONYMOUS` nesses casos.
2. **Validação** em `src/app/validacao.py`: valide tipo, formato e tamanho de cada campo. Corpo acima de 1 MB retorna HTTP 413; campo de texto acima de 256 caracteres retorna HTTP 400. Dados inválidos retornam HTTP 400 com JSON indicando campo e motivo, sem pilha de execução nem nomes internos.
3. **Negócio** em `src/app/negocio.py`: lógica pura, sem I/O de rede e sem depender do runtime do Azure Functions.
4. **Resposta** HTTP 200 com `Content-Type: application/json` e corpo JSON válido. Exceções não tratadas retornam HTTP 500 com mensagem genérica.
5. **Logs** via `src/app/logging_seguro.py`: registre nome da função, identificador de invocação, tipo e mensagem da exceção, sem Segredos nem dados pessoais.
6. **Segredos** somente por `src/app/segredos.py` (Key Vault, App Settings ou variáveis de ambiente).

## Teste automatizado (obrigatório)

Crie ao menos um teste em `tests/` associado à função, executável sem rede e sem credenciais:

- um caso de sucesso (HTTP 200 com corpo JSON válido);
- um caso de entrada inválida (HTTP 400).

Rode `pytest` e informe o resultado.

## Configuração e Segredos

- Use placeholders para qualquer configuração, por exemplo `<NOME_DO_SEGREDO>`, `<NOME_DO_KEY_VAULT>`.
- Se o desenvolvedor informar um valor real de Segredo (chave, senha, token, string de conexão) no chat: **não grave esse valor em nenhum arquivo e não o reproduza na resposta**. Oriente usar o placeholder `<NOME_DO_SEGREDO>` e armazenar o Segredo no Azure Key Vault ou em App Settings, acessado por Identidade Gerenciada.
- Nunca grave valores reais em `local.settings.json`; use `local.settings.json.example` com placeholders.

Lembre o desenvolvedor de revisar o código gerado antes de commitar, executar ou implantar.
