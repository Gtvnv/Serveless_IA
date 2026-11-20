# Política de Segurança

Este documento descreve como reportar vulnerabilidades e como o projeto trata Segredos (credenciais, chaves de API, strings de conexão e tokens).

## Reporte de vulnerabilidades

### Canal de contato

Não abra uma issue pública para reportar uma vulnerabilidade. Use um dos canais privados abaixo:

1. **GitHub Private Vulnerability Reporting**: na aba **Security** do repositório, selecione **Report a vulnerability**.
2. **E-mail**: `<EMAIL_DO_RESPONSAVEL>` (substitua pelo endereço do responsável ao publicar o repositório).

Inclua na mensagem:

- descrição da vulnerabilidade e do impacto;
- passos para reproduzir;
- arquivos, versões ou commits afetados;
- sugestão de correção, se houver.

Não inclua valores reais de Segredos no reporte. Use placeholders como `<NOME_DO_SEGREDO>`.

### Prazo de resposta

- **Resposta inicial**: em até **5 dias úteis** após o recebimento, confirmando o recebimento e informando os próximos passos.
- Depois da resposta inicial, o responsável mantém o autor do reporte informado sobre a análise e a correção.
- Pedimos que a vulnerabilidade não seja divulgada publicamente até que a correção esteja disponível.

## Gestão de Segredos

### Armazenamento

- Segredos são lidos somente de variáveis de ambiente, App Settings do Function_App ou Azure Key Vault.
- Em produção, o acesso ao Key Vault e a outros recursos do Azure usa Identidade Gerenciada (Managed Identity), sem credenciais armazenadas.
- No GitHub Actions, a autenticação no Azure usa OIDC com identidade federada. Não armazene senhas, client secrets ou certificados em Secrets ou Variables.
- Para desenvolvimento local, use o arquivo `local.settings.json`, que fica fora do controle de versão. O repositório versiona apenas `local.settings.json.example`, com valores placeholder.
- Segredos e dados pessoais não devem aparecer em logs.

### Rotação

- Troque qualquer Segredo imediatamente se houver suspeita de exposição.
- Faça rotação periódica das chaves e tokens que não usam Identidade Gerenciada, conforme a política da sua organização (sugestão: ao menos a cada 90 dias).
- Depois de rotacionar, revogue o valor antigo e atualize o Key Vault ou as App Settings.
- Use no Key Vault versões de Segredo com data de expiração quando possível.

### Proibição de versionamento

- É proibido commitar Segredos no código-fonte, em arquivos de configuração versionados, em arquivos de workflow, em documentação ou em exemplos.
- O `.gitignore` exclui `local.settings.json` e arquivos `.env` e `.env.*`.
- O Verificador_Seguranca varre os arquivos versionados e executa no Workflow_CI_CD antes do deploy. Se encontrar um padrão de Segredo, a execução falha e o deploy não ocorre.
- Se um Segredo for versionado por engano, considere-o comprometido: rotacione-o primeiro e depois remova-o do repositório e do histórico.
