---
description: Prepara e executa o deploy do Function_App no Azure, verificando os pré-requisitos antes de qualquer comando de publicação.
mode: agent
---

# Preparar e executar o deploy no Azure

Conduza o deploy do Function_App no Azure. Responda sempre em português do Brasil, mantendo código, comandos e nomes técnicos na forma original.

## Informações obrigatórias

Peça ao desenvolvedor, se ainda não informados: `<NOME_DO_FUNCTION_APP>`, `<NOME_DO_GRUPO_DE_RECURSOS>`, `<ID_DA_ASSINATURA>` e `<REGIAO>`. Se faltar alguma, solicite-a e **não gere nem altere arquivos nem execute comandos** até recebê-la.

## Verificação de pré-requisitos (antes de qualquer publicação)

Verifique e reporte cada item como atendido ou pendente, antes de executar qualquer comando de publicação:

1. Azure CLI e Azure Functions Core Tools instalados (`az --version`, `func --version`);
2. sessão ativa no Azure (`az account show`) e assinatura que o desenvolvedor possui ou está autorizado a usar;
3. Infraestrutura (Bicep em `infra/`) implantada: Function_App, plano, conta de armazenamento e Application Insights existem;
4. testes locais passando (`pytest`);
5. verificação de segredos e termos proibidos sem ocorrências (`python tools/verificador_seguranca.py`);
6. App Settings configuradas com placeholders substituídos por referências ao Key Vault (`<NOME_DO_SEGREDO>`), sem Segredos no código nem em arquivos versionados;
7. Identidade Gerenciada habilitada, com RBAC de menor privilégio e escopo por recurso.

Se algum item estiver pendente, pare, explique o que falta e como resolver. Não prossiga com a publicação.

## Execução

- Antes de cada comando que cria, altera ou exclui recursos, explique a finalidade e os recursos afetados.
- Peça confirmação explícita do desenvolvedor antes de executar o deploy ou criar recursos. Sem resposta afirmativa, não execute e mantenha os recursos inalterados.
- Prefira o Workflow_CI_CD (OIDC com Identidade federada, IDs por GitHub Secrets ou Variables) ao deploy manual. No deploy manual, use `func azure functionapp publish <NOME_DO_FUNCTION_APP>` a partir de `src/`.
- Nunca grave credenciais de longa duração em arquivos.

## Segredos informados no chat

Se o desenvolvedor informar um valor real de Segredo (chave, senha, token, string de conexão, client secret): **não grave esse valor em nenhum arquivo e não o reproduza na resposta**. Oriente usar o placeholder `<NOME_DO_SEGREDO>` e armazenar o Segredo no Azure Key Vault ou em App Settings, acessado por Identidade Gerenciada.
