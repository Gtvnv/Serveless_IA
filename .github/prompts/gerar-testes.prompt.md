---
description: Gera testes automatizados para uma função existente, pedindo antes a identificação da função alvo.
mode: agent
---

# Gerar testes automatizados de uma função

Gere testes automatizados para uma função já existente neste repositório. Responda sempre em português do Brasil, mantendo código, comandos e nomes técnicos na forma original.

## Identificação da função alvo (obrigatória)

Antes de gerar qualquer teste, peça ao desenvolvedor que identifique a função alvo: `<NOME_DA_FUNCAO>` e, se houver ambiguidade, o arquivo (por exemplo `src/app/negocio.py` ou `src/function_app.py`). Se a identificação estiver ausente ou não corresponder a uma função existente, peça-a (ou esclareça) e **não gere nem altere nenhum arquivo** até recebê-la.

## O que gerar

1. Leia a função alvo e os módulos de que depende em `src/app` (`validacao`, `negocio`, `http`, `logging_seguro`, `segredos`).
2. Crie ou estenda testes em `tests/` (pytest), sem duplicar o que já existe.
3. Cubra no mínimo um caso de sucesso e um caso de falha de validação por função de negócio.
4. Para função HTTP, inclua um teste de sucesso (HTTP 200 com corpo JSON válido) e um de entrada inválida (HTTP 400). Considere também HTTP 413 (corpo acima de 1 MB) e HTTP 500 genérico.
5. Quando fizer sentido, adicione testes baseados em propriedades (Hypothesis, mínimo de 100 execuções), por exemplo: a validação nunca lança exceção para textos de 0 a 10.000 caracteres; serializar e desserializar produz objeto equivalente.
6. Os testes devem rodar sem credenciais, sem rede e sem recursos reais do Azure, e não podem usar valores reais de Segredos nem dados pessoais reais (use dados fictícios e placeholders como `<NOME_DO_SEGREDO>`).
7. Rode `pytest` e informe os testes que passaram ou falharam, pelo nome.

## Segredos informados no chat

Se o desenvolvedor informar um valor real de Segredo (chave, senha, token, string de conexão): **não grave esse valor em nenhum arquivo e não o reproduza na resposta**. Oriente usar o placeholder `<NOME_DO_SEGREDO>` e armazenar o Segredo no Azure Key Vault ou em App Settings.

Lembre o desenvolvedor de revisar o código gerado antes de commitar ou executar.
