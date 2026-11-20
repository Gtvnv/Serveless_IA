---
description: Revisa a segurança de uma função e produz uma lista de achados com arquivo analisado, risco e correção recomendada.
mode: ask
---

# Revisar a segurança de uma função

Revise a segurança de uma função deste repositório. Responda sempre em português do Brasil, mantendo código, comandos e nomes técnicos na forma original.

## Informação obrigatória

Peça ao desenvolvedor, se ainda não informado, `<NOME_DA_FUNCAO>` (e o arquivo, se houver ambiguidade). Se estiver ausente, solicite-a e **não gere nem altere nenhum arquivo** até recebê-la. Esta revisão apenas lê e reporta; não altera arquivos sem pedido explícito.

## O que analisar

Leia a função, seu gatilho em `src/function_app.py` e os módulos relacionados em `src/app` (`validacao`, `negocio`, `http`, `logging_seguro`, `segredos`). Verifique:

- Segredos no código, em configuração versionada ou em workflows (devem vir de variáveis de ambiente, App Settings ou Key Vault);
- nível de autorização HTTP (função com dados não públicos não pode ser anônima);
- validação de tipo, formato e tamanho (corpo até 1 MB, textos até 256 caracteres) e erros sem pilha de execução nem nomes internos;
- logs sem Segredos nem dados pessoais (nome, e-mail, CPF, telefone, endereço);
- falha na leitura de Segredo: erro registrado sem o valor e operação recusada, sem valor padrão;
- menor privilégio (Identidade Gerenciada, RBAC por recurso, sem Owner/Contributor/User Access Administrator);
- dependências desatualizadas ou vulneráveis.

## Formato da resposta

Produza uma lista de achados. Cada item deve conter:

- **Arquivo analisado**: caminho (e linha, quando aplicável);
- **Risco**: o problema identificado e seu impacto;
- **Correção recomendada**: ação concreta, usando placeholders como `<NOME_DO_SEGREDO>`.

Se nada for encontrado, diga explicitamente quais arquivos foram analisados e que não houve achados.

## Segredos informados no chat

Se o desenvolvedor informar um valor real de Segredo, ou se encontrar um no código: **não grave esse valor em nenhum arquivo e não o reproduza na resposta** (indique apenas arquivo e linha). Oriente usar o placeholder `<NOME_DO_SEGREDO>`, armazenar o Segredo no Azure Key Vault ou em App Settings e rotacionar o Segredo exposto.
