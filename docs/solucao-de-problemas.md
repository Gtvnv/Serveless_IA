# Solução de problemas e custos

Este guia reúne os problemas mais comuns ao usar o projeto e informa o custo estimado dos recursos no Azure. O projeto é material de estudo independente, sem afiliação, patrocínio ou endosso de qualquer organização.

> Nunca cole valores reais de chaves, senhas ou strings de conexão em issues, prompts ou logs. Use placeholders como `<NOME_DO_SEGREDO>`.

## Índice

1. [Core Tools não encontrado (`func` não é reconhecido)](#1-core-tools-não-encontrado-func-não-é-reconhecido)
2. [Erro de `AzureWebJobsStorage` ao executar localmente](#2-erro-de-azurewebjobsstorage-ao-executar-localmente)
3. [Falha de login OIDC no GitHub Actions](#3-falha-de-login-oidc-no-github-actions)
4. [HTTP 401 ao chamar a função](#4-http-401-ao-chamar-a-função)
5. [Verificador de segurança reprovando](#5-verificador-de-segurança-reprovando)
6. [Deploy Bicep falha com nome de recurso já em uso](#6-deploy-bicep-falha-com-nome-de-recurso-já-em-uso)
7. [Copilot não carrega prompts ou chat mode](#7-copilot-não-carrega-prompts-ou-chat-mode)
8. [Custos e como remover os recursos](#custos-e-limpeza-dos-recursos)

## 1. Core Tools não encontrado (`func` não é reconhecido)

**Sintoma**

Ao executar `func start`, o terminal responde que o comando `func` não foi encontrado ou não é reconhecido.

**Solução**

1. Instale o Azure Functions Core Tools v4: <https://learn.microsoft.com/azure/azure-functions/functions-run-local>.
2. Feche e reabra o terminal (e o VS Code) para atualizar o `PATH`.
3. Confirme a instalação com `func --version`. A saída deve começar com `4.`.
4. Execute `func start` dentro da pasta `src`, onde está o `host.json`.
5. Se a versão for antiga, atualize o Core Tools e confirme que o Python 3.11 está instalado (`python --version`).

## 2. Erro de `AzureWebJobsStorage` ao executar localmente

**Sintoma**

O host falha ao iniciar com mensagens como "Value cannot be null. (Parameter 'provider')", "Azure Storage connection string is missing" ou erro de conexão recusada em `127.0.0.1:10000`.

**Solução**

1. Copie `src/local.settings.json.example` para `src/local.settings.json`. Esse arquivo não é versionado.
2. Para triggers de temporizador, fila e blob, o host precisa de um armazenamento. Use o emulador Azurite: instale a extensão **Azurite** no VS Code ou execute `npm install -g azurite` e depois `azurite --silent`.
3. Com o Azurite em execução, defina `"AzureWebJobsStorage": "UseDevelopmentStorage=true"` em `local.settings.json`. Esse valor é um atalho público do emulador e não contém credencial real.
4. Reinicie com `func start`.
5. Se a porta 10000 estiver ocupada, finalize o processo que a usa ou inicie o Azurite em outra porta.
6. Os testes unitários (`python -m pytest -q`) não precisam do Azurite nem de rede.

## 3. Falha de login OIDC no GitHub Actions

**Sintoma**

A etapa `azure/login` do workflow falha com erros como `AADSTS70021: No matching federated identity record found` ou `AADSTS700016: Application not found`.

**Solução**

1. Confira que o workflow tem `permissions` com `id-token: write` e `contents: read`.
2. Confira os GitHub Secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` e `AZURE_SUBSCRIPTION_ID` (nomes exatos, sem espaços extras).
3. No Microsoft Entra ID, abra o registro do aplicativo e vá em **Certificados e segredos > Credenciais federadas**. Verifique se existe uma credencial para o seu repositório.
4. O campo **Assunto** deve corresponder ao contexto do job. Como o job de deploy usa `environment: production`, o assunto esperado é `repo:<USUARIO_OU_ORG>/<REPOSITORIO>:environment:production`.
5. Confirme que o principal de serviço tem permissão para publicar no Function App, com escopo limitado a esse recurso.
6. Reexecute o workflow. Se o ambiente `production` exige revisores, aprove o deploy na página da execução.

## 4. HTTP 401 ao chamar a função

**Sintoma**

Chamadas `POST /api/pedidos` retornam `401 Unauthorized`.

**Solução**

1. A função usa `auth_level=FUNCTION`, então toda requisição precisa de uma chave de função.
2. Obtenha a chave no portal do Azure, em **Function App > Funções > Chaves de aplicativo / Chaves de função**, ou com `az functionapp function keys list`. Trate a chave como Segredo e não a versione.
3. Envie a chave no cabeçalho `x-functions-key: <CHAVE_DA_FUNCAO>` (preferível à query string `?code=`, que pode aparecer em logs).
4. Em execução local com `func start`, a chave não é exigida. Se o 401 ocorrer só no Azure, a chave está ausente ou foi trocada.
5. Se a chave vazou, gere uma nova no portal e remova a antiga.

## 5. Verificador de segurança reprovando

**Sintoma**

`python tools/verificador_seguranca.py` retorna código de saída diferente de zero, e a pipeline para antes do build e do deploy.

**Solução**

1. Leia a saída. Cada ocorrência mostra o caminho do arquivo e o número da linha, sem exibir o valor encontrado.
2. Se for um Segredo (chave, string de conexão, token ou chave privada), remova o valor do arquivo, troque por um placeholder e **revogue ou rotacione** a credencial, pois ela pode já ter sido exposta.
3. Se for um Termo_Proibido, remova ou reescreva o trecho (ou renomeie o arquivo ou pasta) e execute novamente.
4. O verificador varre arquivos versionados. Rode `git add <arquivo>` nos arquivos novos antes de testar, ou use `--sem-git` para varrer a árvore inteira.
5. Repita o comando até o código de saída ser 0.

## 6. Deploy Bicep falha com nome de recurso já em uso

**Sintoma**

`az deployment group create` falha com erros como `StorageAccountAlreadyTaken`, `Website with given name is already in use` ou `InvalidResourceName`.

**Solução**

1. Nomes de Function App (`<nomeFunctionApp>.azurewebsites.net`) e de conta de armazenamento são únicos globalmente.
2. Edite `infra/main.bicepparam` e escolha nomes únicos, por exemplo com um sufixo curto.
3. A conta de armazenamento aceita de 3 a 24 caracteres, apenas minúsculas e números.
4. Se uma tentativa anterior deixou recursos parciais, remova o grupo de recursos (veja a seção de limpeza) ou use um grupo novo.
5. Se o erro citar cota ou região indisponível para o SKU, troque o parâmetro `regiao` e repita o deploy.
6. Execute `az deployment group validate` com os mesmos parâmetros antes de implantar de novo.

## 7. Copilot não carrega prompts ou chat mode

**Sintoma**

Os comandos `/criar-http-trigger`, `/deploy-azure` e os demais não aparecem no chat, ou o modo **azure-functions** não está na lista de modos.

**Solução**

1. Abra a **raiz do repositório** no VS Code, pois a pasta `.github` precisa estar na raiz do workspace.
2. Confirme que o GitHub Copilot e o Copilot Chat estão instalados, atualizados e com login ativo.
3. Verifique se os arquivos existem: `.github/prompts/*.prompt.md`, `.github/chatmodes/azure-functions.chatmode.md` e `.github/copilot-instructions.md`.
4. Confira o frontmatter (bloco `---` no início). Um YAML inválido faz o arquivo ser ignorado.
5. Rode `python tools/validar_customizacoes.py` para apontar arquivos com problema.
6. Reinicie a janela com **Developer: Reload Window** e abra o chat novamente.
7. Se a organização gerencia o Copilot, confira se o uso de prompt files e chat modes está habilitado nas políticas.

## Custos e limpeza dos recursos

### Custo mensal estimado (SKU padrão)

O SKU padrão é **Y1 (Dynamic, plano de consumo)**, definido no parâmetro `skuPlano` de `infra/main.bicep`. Os valores abaixo são estimativas para uso de estudo, com poucas centenas ou milhares de execuções por mês.

| Recurso | Cobrança | Estimativa mensal (USD) |
|---------|----------|-------------------------|
| Function App no plano Y1 (consumo) | Pago por uso (execuções e GB-s). Cota gratuita mensal de 1 milhão de execuções e 400.000 GB-s por assinatura | 0,00 |
| Conta de armazenamento `Standard_LRS` | Por GB armazenado e por transações. O host grava poucos dados | 0,01 a 0,50 |
| Application Insights | Por GB ingerido. Os primeiros 5 GB por mês costumam ser gratuitos | 0,00 para uso de estudo |
| **Total estimado** | | **cerca de USD 0 a USD 1 por mês** |

Observações:

- Dentro da cota gratuita, o plano de consumo não gera cobrança de execução. Fora dela, o valor sobe de acordo com o uso. Em uso intenso de testes de carga, o total pode chegar a poucos dólares.
- Os valores variam com a região, a moeda, o tipo de assinatura e mudanças de preço. Confirme na página oficial: <https://azure.microsoft.com/pricing/details/functions/> e use a [calculadora de preços do Azure](https://azure.microsoft.com/pricing/calculator/) para simular o seu cenário.
- Defina um orçamento com alertas no **Microsoft Cost Management** para evitar surpresas.

### Remover todos os recursos provisionados

Ao terminar o estudo, remova o grupo de recursos para interromper qualquer cobrança. O comando exclui **todos** os recursos do grupo e não pode ser desfeito, então confirme o nome do grupo antes de executar:

```bash
az group delete --name <NOME_DO_GRUPO_DE_RECURSOS> --yes --no-wait
```

Para acompanhar a exclusão: `az group exists --name <NOME_DO_GRUPO_DE_RECURSOS>` (retorna `false` quando terminar).

Depois, remova também o registro do aplicativo e a credencial federada no Microsoft Entra ID, se tiver criado apenas para este projeto.
