---
applyTo: "src/**/*.py"
---

# Instruções para código das Azure Functions (Python)

## Gatilhos finos, lógica pura
- Mantenha o arquivo da função (gatilho/binding) fino: ele apenas lê a entrada, chama a lógica e devolve a resposta.
- Coloque a regra de negócio em funções puras, sem dependência de `azure.functions`, para testar sem infraestrutura.
- Injete clientes externos (modelos de IA, storage) por parâmetro, em vez de criá-los dentro da lógica.

## Validação
- Valide toda entrada (corpo, query string, mensagens de fila) antes de processar.
- Em entrada inválida, retorne HTTP 400 com mensagem objetiva, sem expor detalhes internos.
- Limite o tamanho de prompts e payloads.

## Logging seguro
- Use o módulo `logging`, nunca `print`.
- Não registre segredos, tokens, chaves nem o conteúdo integral de prompts ou dados pessoais.
- Registre identificadores de correlação e duração, não o payload completo.

## Segredos e configuração
- Leia segredos somente de variáveis de ambiente, App Settings ou Azure Key Vault.
- Nunca escreva valores de segredos no código nem em arquivos versionados.

## auth_level
- Prefira `AuthLevel.FUNCTION` ou superior em endpoints HTTP.
- Use `ANONYMOUS` apenas quando houver justificativa explícita, como um endpoint de saúde sem dados sensíveis.
- Nunca exponha chaves de função ao cliente final.

## Erros e tipagem
- Trate exceções esperadas de forma específica e retorne códigos HTTP coerentes (4xx para o cliente, 5xx para falha interna).
- Use type hints e funções `async` apenas quando houver I/O assíncrono real.
