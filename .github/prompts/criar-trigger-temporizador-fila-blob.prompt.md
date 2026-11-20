---
description: Cria uma função Azure Functions com trigger de temporizador, fila ou blob, pedindo antes a escolha de um dos três tipos.
mode: agent
---

# Criar função com trigger de temporizador, fila ou blob

Gere uma nova função Azure Functions orientada a eventos neste repositório. Responda sempre em português do Brasil, mantendo código, comandos e nomes técnicos na forma original.

## Escolha do tipo de trigger (obrigatória)

Antes de gerar qualquer código, pergunte ao desenvolvedor qual dos três tipos usar e aguarde a resposta:

1. **Temporizador** (agenda NCRONTAB com seis campos, por exemplo `<EXPRESSAO_NCRONTAB>`);
2. **Fila** (Azure Queue Storage, com `<NOME_DA_FILA>`);
3. **Blob** (com `<NOME_DO_CONTAINER>` e padrão de caminho).

Peça também `<NOME_DA_FUNCAO>` (snake_case). Se o tipo de trigger ou o nome da função estiver ausente, ou se o tipo não for um dos três, peça a informação e **não gere nem altere nenhum arquivo** até recebê-la.

## O que gerar

Respeite a arquitetura existente:

1. **Gatilho** em `src/function_app.py`: fino, no estilo de `rotina_temporizador`. Apenas delega a `tratar_evento` de `app.http` (que usa `logging_seguro` para registrar falhas).
2. **Negócio** em `src/app/negocio.py`: função pura, sem I/O de rede e sem depender do runtime (como `executar_rotina_periodica`).
3. **Validação** em `src/app/validacao.py` quando o evento carrega dados (mensagem de fila ou conteúdo de blob): valide tipo, formato e tamanho.
4. **Erros**: exceções não tratadas são registradas em log estruturado (nome da função, identificador de invocação, tipo e mensagem da exceção) e **relançadas**, para que o runtime aplique a política de nova tentativa sem encerrar o processo.
5. **Logs** sem Segredos e sem dados pessoais.
6. **Conexões** por Identidade Gerenciada ou App Settings, referenciadas por nome (`<NOME_DA_CONEXAO>`), nunca por valor.
7. **Teste unitário** em `tests/` que execute a lógica sem o runtime e sem rede, com um caso de sucesso e um de falha de validação. Rode `pytest` e informe o resultado.

## Configuração e Segredos

- Use placeholders para configuração, por exemplo `<NOME_DO_SEGREDO>`.
- Se o desenvolvedor informar um valor real de Segredo (chave, string de conexão, token) no chat: **não grave esse valor em nenhum arquivo e não o reproduza na resposta**. Oriente usar o placeholder `<NOME_DO_SEGREDO>` e armazenar o Segredo no Azure Key Vault ou em App Settings.
- Atualize `local.settings.json.example` apenas com placeholders.

Lembre o desenvolvedor de revisar o código gerado antes de commitar, executar ou implantar.
