# Requirements Document

## Introduction

Este projeto educacional e prático ensina a criar um agente de IA, construído com as customizações do GitHub Copilot (instruções do repositório, instruções por escopo, prompt files, chat modes e agent mode), que ajuda desenvolvedores a criar, testar e fazer deploy de serviços serverless com Azure Functions. O projeto entrega dois artefatos principais: (1) o Agente Copilot, um conjunto versionado de arquivos de customização, e (2) um Projeto de Exemplo de Azure Functions criado com o auxílio desse agente. O projeto inclui documentação completa em português do Brasil, medidas de segurança (segredos fora do código, menor privilégio) e avisos éticos sobre o uso de IA.

## Glossary

- **Agente_Copilot**: Conjunto de customizações do GitHub Copilot (instruções, prompt files e chat modes) versionadas no repositório, que orienta a criação, o teste e o deploy de Azure Functions.
- **Projeto_Exemplo**: Aplicação Azure Functions de demonstração, criada com o Agente_Copilot e contida neste repositório.
- **Repositorio**: Repositório Git que contém o Agente_Copilot, o Projeto_Exemplo, os workflows e a documentação.
- **Instrucoes_Repositorio**: Arquivo `.github/copilot-instructions.md` com diretrizes gerais para o Copilot.
- **Instrucoes_Escopo**: Arquivos `.github/instructions/*.instructions.md` aplicados a padrões de arquivos específicos.
- **Prompt_File**: Arquivo `.github/prompts/*.prompt.md` que define uma tarefa reutilizável invocável no chat do Copilot.
- **Chat_Mode**: Arquivo `.github/chatmodes/*.chatmode.md` que define um modo de chat com persona, ferramentas permitidas e instruções.
- **Function_App**: Aplicação Azure Functions hospedada no Azure.
- **Workflow_CI_CD**: Pipeline do GitHub Actions que compila, testa e faz deploy do Function_App.
- **Segredo**: Credencial, chave de API, string de conexão ou token que não pode ser versionado.
- **Documentacao**: Conjunto de arquivos Markdown em português do Brasil que descrevem o projeto.
- **Verificador_Seguranca**: Script ou etapa automatizada que procura Segredos e termos proibidos nos arquivos do Repositorio.
- **Termo_Proibido**: Qualquer menção ao nome ou à plataforma da organização educacional que o usuário pediu para não citar, conforme a lista mantida no Verificador_Seguranca.
- **Identidade_Gerenciada**: Managed Identity do Azure usada para acesso a recursos sem Segredos.
- **Infraestrutura**: Definição de infraestrutura como código em Bicep, contida no Repositorio, e sua implantação no Azure para provisionar os recursos do Function_App.

## Requirements

### Requirement 1: Instruções do Copilot no repositório

**User Story:** Como desenvolvedor, quero um conjunto de instruções do Copilot no repositório, para que o agente siga padrões consistentes de Azure Functions.

#### Acceptance Criteria

1. THE Repositorio SHALL conter o arquivo Instrucoes_Repositorio em `.github/copilot-instructions.md`, em formato Markdown com codificação UTF-8 e tamanho máximo de 50 KB.
2. THE Instrucoes_Repositorio SHALL conter quatro seções identificadas por título, uma para cada tópico a seguir: stack (linguagem, runtime e versões do Projeto_Exemplo), estrutura de pastas (diretórios de primeiro nível e a finalidade de cada um), convenções de código (nomenclatura, tratamento de erros e logging) e comandos de build e teste (ao menos um comando executável para build e um para teste do Projeto_Exemplo).
3. THE Instrucoes_Repositorio SHALL conter uma regra explícita que exija que Segredos sejam lidos somente de variáveis de ambiente, App Settings ou Azure Key Vault, e que proíba valores de Segredos escritos diretamente no código-fonte, em arquivos de configuração versionados e em arquivos de workflow.
4. THE Repositorio SHALL conter ao menos um arquivo de Instrucoes_Escopo em `.github/instructions/` com extensão `.instructions.md`, cujo campo `applyTo` no frontmatter contenha ao menos um padrão glob que corresponda a todos os arquivos de código-fonte das funções do Projeto_Exemplo.
5. THE Repositorio SHALL conter ao menos um arquivo de Instrucoes_Escopo em `.github/instructions/` com extensão `.instructions.md`, cujo campo `applyTo` no frontmatter contenha o padrão glob que corresponda a todos os arquivos `.yml` e `.yaml` em `.github/workflows`.
6. IF um arquivo de Instrucoes_Escopo tiver o campo `applyTo` ausente, vazio ou com padrão glob que não corresponda a nenhum arquivo existente no Repositorio, THEN THE Repositorio SHALL ser considerado não conforme com este requisito, e a verificação SHALL indicar o caminho do arquivo e o motivo da não conformidade.

### Requirement 2: Prompt files reutilizáveis

**User Story:** Como desenvolvedor, quero prompt files reutilizáveis, para que eu execute as tarefas comuns do ciclo serverless com um comando no chat.

#### Acceptance Criteria

1. THE Repositorio SHALL conter exatamente um Prompt_File dedicado a criar uma nova função HTTP trigger, e esse Prompt_File SHALL instruir a geração de uma função que responde a requisições HTTP e inclui pelo menos um teste automatizado associado.
2. THE Repositorio SHALL conter exatamente um Prompt_File dedicado a criar uma nova função com trigger de temporizador, fila ou blob, e esse Prompt_File SHALL solicitar ao desenvolvedor a escolha de um dos três tipos de trigger antes de gerar o código.
3. THE Repositorio SHALL conter exatamente um Prompt_File dedicado a gerar testes automatizados de uma função existente, e esse Prompt_File SHALL solicitar a identificação da função alvo antes de gerar os testes.
4. THE Repositorio SHALL conter exatamente um Prompt_File dedicado a preparar e executar o deploy do Function_App no Azure, e esse Prompt_File SHALL instruir a verificação dos pré-requisitos de deploy antes de executar qualquer comando de publicação.
5. THE Repositorio SHALL conter exatamente um Prompt_File dedicado a revisar a segurança de uma função, e esse Prompt_File SHALL instruir a produção de uma lista de achados em que cada item indica o arquivo analisado, o risco identificado e a correção recomendada.
6. THE Repositorio SHALL declarar em cada Prompt_File um campo `description` não vazio, com no máximo 200 caracteres, e um campo que define o modo de execução do chat com um dos valores aceitos pelo VS Code para prompt files.
7. WHEN um Prompt_File solicita dados de configuração, THE Prompt_File SHALL instruir o uso de placeholders (por exemplo `<NOME_DO_SEGREDO>`) no lugar de valores reais de Segredos.
8. IF o desenvolvedor informar um valor real de Segredo no chat durante a execução de um Prompt_File, THEN THE Prompt_File SHALL instruir o agente a não gravar esse valor em nenhum arquivo do Repositorio nem reproduzi-lo na resposta, e a orientar o uso de um placeholder e de um mecanismo de armazenamento de Segredos.
9. IF o desenvolvedor invocar um Prompt_File sem fornecer uma informação obrigatória para a tarefa (como nome da função ou tipo de trigger), THEN THE Prompt_File SHALL instruir o agente a solicitar a informação ausente e a não gerar nem alterar arquivos até que ela seja fornecida.

### Requirement 3: Chat mode para Azure Functions

**User Story:** Como desenvolvedor, quero um chat mode dedicado a serverless, para que o Copilot atue como especialista em Azure Functions com ferramentas controladas.

#### Acceptance Criteria

1. THE Repositorio SHALL conter ao menos 1 arquivo de Chat_Mode cujo conteúdo declare como escopo exclusivo o desenvolvimento, a configuração e o deploy de Azure Functions.
2. THE Chat_Mode SHALL declarar no campo `tools` uma lista explícita com ao menos 1 ferramenta permitida, sem uso de curinga que habilite todas as ferramentas.
3. WHEN o agente sugerir um comando que cria, altera ou exclui recursos no Azure, THE Chat_Mode SHALL instruir o agente a explicar, antes de apresentar o comando, a finalidade do comando e os recursos afetados.
4. WHEN o agente precisar executar uma ação de deploy ou de criação de recursos no Azure, THE Chat_Mode SHALL instruir o agente a solicitar confirmação explícita do usuário antes da execução e a não executar a ação até receber resposta afirmativa.
5. IF o usuário não responder afirmativamente à solicitação de confirmação (resposta negativa ou ausência de resposta), THEN THE Chat_Mode SHALL instruir o agente a não executar a ação e a manter o estado atual dos recursos no Azure inalterado.
6. THE Chat_Mode SHALL instruir o agente a redigir 100% das respostas ao usuário em português do Brasil, mantendo em sua forma original apenas código, comandos e nomes técnicos.

### Requirement 4: Projeto de exemplo de Azure Functions

**User Story:** Como aprendiz, quero um projeto de exemplo de Azure Functions, para que eu veja o resultado prático do uso do agente.

#### Acceptance Criteria

1. THE Projeto_Exemplo SHALL conter ao menos uma função com trigger HTTP e ao menos uma função com trigger de temporizador, fila ou blob.
2. THE Projeto_Exemplo SHALL conter o arquivo `host.json`, um arquivo `local.settings.json.example` contendo apenas valores placeholder (nenhuma credencial, chave ou connection string real) e o arquivo de dependências da linguagem escolhida.
3. IF uma requisição HTTP contém dados inválidos (campo obrigatório ausente, tipo incorreto, tamanho acima do limite ou formato inválido), THEN THE Function_App SHALL responder com código HTTP 400, um corpo JSON com mensagem de erro indicando quais campos são inválidos e o motivo, sem incluir pilha de execução, caminhos de arquivo ou nomes de classes internas, e SHALL NOT executar a lógica de negócio.
4. WHEN uma requisição HTTP com dados válidos é recebida, THE Function_App SHALL responder com código HTTP 200, cabeçalho `Content-Type: application/json` e um corpo JSON válido, em até 2 segundos em execução local.
5. IF ocorre uma exceção não tratada em uma função HTTP, THEN THE Function_App SHALL registrar o erro em log estruturado contendo ao menos o nome da função, o identificador de invocação, o tipo da exceção e a mensagem, e SHALL responder com código HTTP 500 e uma mensagem genérica de erro, sem expor a pilha de execução nem detalhes internos.
6. IF ocorre uma exceção não tratada em uma função de temporizador, fila ou blob, THEN THE Function_App SHALL registrar o erro em log estruturado com os mesmos campos definidos no critério 5 e SHALL permitir que o runtime aplique sua política de nova tentativa, sem encerrar o processo do Function_App.
7. THE Projeto_Exemplo SHALL isolar a lógica de negócio dos gatilhos, de modo que ao menos um teste unitário por função execute a lógica sem o runtime do Azure Functions e sem acesso à rede, e que a suíte de testes seja concluída com todos os testes aprovados.
8. WHEN uma requisição HTTP é recebida, THE Function_App SHALL validar o tipo, o formato e o tamanho de cada campo de entrada e rejeitar com HTTP 413 o corpo da requisição acima de 1 MB e com HTTP 400 qualquer campo de texto acima de 256 caracteres.

### Requirement 5: Testes automatizados

**User Story:** Como desenvolvedor, quero testes automatizados, para que eu valide as funções localmente e na pipeline.

#### Acceptance Criteria

1. THE Projeto_Exemplo SHALL conter ao menos um teste unitário para cada função da lógica de negócio, cobrindo no mínimo um caso de sucesso e um caso de falha de validação por função.
2. THE Projeto_Exemplo SHALL conter, para cada função HTTP, ao menos um teste que verifica a resposta de sucesso (código 200) com corpo válido e ao menos um teste que verifica a resposta de requisição inválida (código 400) com entrada inválida.
3. WHEN o comando de testes documentado é executado sem credenciais, sem conexão de rede com o Azure e sem recursos reais do Azure provisionados, THE Projeto_Exemplo SHALL executar todos os testes e finalizá-los com código de saída 0 quando todos passarem.
4. IF um ou mais testes falham quando o comando de testes documentado é executado, THEN THE Projeto_Exemplo SHALL finalizar a execução com código de saída diferente de 0 e exibir o nome de cada teste que falhou.
5. WHEN o comando de testes documentado é executado, THE Projeto_Exemplo SHALL concluir a execução de todos os testes em até 60 segundos em ambiente local.
6. FOR ALL entradas de texto geradas aleatoriamente, com comprimento de 0 a 10.000 caracteres e em no mínimo 100 execuções por rodada de testes, THE função de validação do Projeto_Exemplo SHALL retornar um resultado válido ou inválido sem lançar exceção (propriedade de erro).
7. FOR ALL objetos válidos de entrada gerados aleatoriamente em no mínimo 100 execuções por rodada de testes, THE serialização para JSON seguida da desserialização SHALL produzir um objeto equivalente ao original, com todos os campos de valor iguais (propriedade de round-trip).

### Requirement 6: Pipeline de CI/CD

**User Story:** Como desenvolvedor, quero um pipeline de deploy automatizado, para que o Function_App seja publicado de forma repetível.

#### Acceptance Criteria

1. THE Repositorio SHALL conter um Workflow_CI_CD em `.github/workflows` com etapas, executadas nesta ordem, de instalação de dependências, compilação, execução dos testes e publicação do Function_App.
2. WHEN um push é feito na branch principal, THE Workflow_CI_CD SHALL executar a compilação e os testes e, se ambos concluírem com sucesso, executar a etapa de deploy.
3. IF a compilação ou qualquer teste falha, THEN THE Workflow_CI_CD SHALL encerrar a execução com status de falha, não executar a etapa de deploy e manter inalterada a versão do Function_App já publicada.
4. THE Workflow_CI_CD SHALL autenticar no Azure por OIDC com Identidade federada, sem armazenar credenciais de longa duração (senhas, client secrets ou certificados) no Repositorio, em Secrets ou em Variables.
5. THE Workflow_CI_CD SHALL declarar o bloco `permissions` em nível de workflow ou de job, concedendo somente `contents: read` e `id-token: write`, e nenhuma outra permissão, salvo justificativa documentada em comentário no próprio workflow.
6. THE Workflow_CI_CD SHALL referenciar os IDs de tenant, subscription e client exclusivamente por GitHub Secrets ou Variables, sem nenhum desses valores literais em arquivos do Repositorio.
7. WHERE o ambiente de produção está configurado como GitHub Environment com revisores obrigatórios, THE Workflow_CI_CD SHALL pausar a execução antes da etapa de deploy até que ao menos 1 revisor aprove, e SHALL executar o deploy somente após a aprovação.
8. IF a autenticação OIDC no Azure falha ou a publicação do Function_App falha, THEN THE Workflow_CI_CD SHALL encerrar a execução com status de falha e registrar no log da execução a etapa que falhou, sem expor valores de Secrets.
9. WHERE o ambiente de produção está configurado como GitHub Environment com revisores obrigatórios, WHILE nenhum revisor tiver aprovado o deploy no GitHub Environment de produção, THE Workflow_CI_CD SHALL manter a execução pausada antes da etapa de deploy e SHALL NOT executar o deploy.

### Requirement 7: Infraestrutura como código

**User Story:** Como desenvolvedor, quero provisionar a infraestrutura como código, para que os recursos sejam criados de forma reproduzível e com menor privilégio.

#### Acceptance Criteria

1. THE Repositorio SHALL conter definição de infraestrutura como código (Bicep) que declare exatamente os seguintes recursos: um Function_App, um plano de hospedagem, uma conta de armazenamento e um Application Insights.
2. WHEN a definição de infraestrutura é implantada, THE Infraestrutura SHALL criar o Function_App com Identidade_Gerenciada habilitada, e o identificador principal da identidade SHALL estar disponível no recurso implantado.
3. WHEN a definição de infraestrutura é implantada, THE Infraestrutura SHALL criar atribuições RBAC para a Identidade_Gerenciada somente sobre os recursos que o Function_App acessa, com escopo limitado a cada recurso (nunca à assinatura ou ao grupo de recursos), e SHALL NOT atribuir as funções Owner, Contributor ou User Access Administrator.
4. WHEN a definição de infraestrutura é implantada, THE Infraestrutura SHALL criar o Function_App com tráfego restrito a HTTPS (HTTP rejeitado ou redirecionado) e com versão mínima de TLS igual a 1.2.
5. THE definição de infraestrutura SHALL expor como parâmetros o nome de cada recurso, a região e o SKU do plano de hospedagem, e SHALL NOT conter valores de Segredos (chaves, senhas, cadeias de conexão com credenciais) em arquivos de parâmetros ou no template.
6. IF a implantação da definição de infraestrutura falhar por parâmetro ausente, inválido ou recurso não criado, THEN THE Infraestrutura SHALL reportar a falha indicando o recurso ou parâmetro causador e SHALL NOT deixar atribuições RBAC concedidas a recursos não criados.
7. THE Documentacao SHALL informar o custo mensal estimado em moeda (USD) do SKU padrão, e SHALL conter o comando exato para remover todos os recursos provisionados ao final do estudo.
8. IF a implantação da definição de infraestrutura não foi concluída com sucesso OR alguma restrição RBAC do critério 3 não vale, THEN THE Infraestrutura SHALL ser considerada não conforme com o requisito de RBAC de menor privilégio.
9. WHEN a implantação da definição de infraestrutura foi concluída com sucesso, THE Infraestrutura SHALL ser considerada conforme com o requisito de RBAC de menor privilégio somente se cada atribuição RBAC tiver escopo limitado a um recurso e nenhuma atribuição das funções Owner, Contributor ou User Access Administrator existir.

### Requirement 8: Segurança do repositório

**User Story:** Como responsável pelo projeto, quero medidas de segurança no repositório, para que Segredos não sejam expostos.

#### Acceptance Criteria

1. THE Repositorio SHALL conter na raiz um arquivo `.gitignore` que exclui `local.settings.json`, arquivos `.env` (incluindo variações `.env.*`), diretórios de artefatos de build (`bin/`, `obj/`) e diretórios de dependências (`node_modules/`, `.venv/`, `packages/`).
2. THE Repositorio SHALL conter na raiz um arquivo `SECURITY.md` com a política de reporte de vulnerabilidades (canal de contato, prazo de resposta inicial de até 5 dias úteis) e as práticas de gestão de Segredos (armazenamento, rotação e proibição de versionamento).
3. WHEN o Verificador_Seguranca é executado, THE Verificador_Seguranca SHALL varrer todos os arquivos versionados, identificar padrões de Segredos (chaves de acesso, strings de conexão, tokens e chaves privadas), listar o caminho do arquivo e o número da linha de cada ocorrência sem exibir o valor do Segredo e retornar código de saída diferente de zero.
4. IF o Verificador_Seguranca não encontra padrões de Segredos nos arquivos versionados, THEN THE Verificador_Seguranca SHALL retornar código de saída igual a zero.
5. WHEN o Workflow_CI_CD é executado, THE Workflow_CI_CD SHALL executar o Verificador_Seguranca antes da etapa de deploy.
6. IF o Verificador_Seguranca retorna código de saída diferente de zero, THEN THE Workflow_CI_CD SHALL interromper a execução, marcar o workflow como falho e não executar a etapa de deploy.
7. THE Repositorio SHALL configurar o Dependabot para verificar atualizações de dependências ao menos uma vez por semana e abrir pull requests para as atualizações encontradas.
8. WHERE o acesso a dados sensíveis é necessário, THE Function_App SHALL obter Segredos do Azure Key Vault por Identidade_Gerenciada, sem Segredos armazenados em código-fonte ou em arquivos versionados.
9. IF a obtenção de um Segredo do Azure Key Vault falha, THEN THE Function_App SHALL registrar um erro sem incluir o valor do Segredo e recusar a operação que depende dele, sem usar valor padrão.
10. THE Function_App SHALL omitir Segredos e dados pessoais (nome, e-mail, CPF, telefone e endereço) dos logs.
11. WHEN uma função HTTP expõe dados não públicos, THE Function_App SHALL exigir nível de autorização diferente de anônimo.
12. IF uma requisição a uma função HTTP com dados não públicos não apresenta credencial válida, THEN THE Function_App SHALL rejeitar a requisição com indicação de falha de autorização e não retornar nenhum dado não público.

### Requirement 9: Avisos éticos

**User Story:** Como aprendiz, quero avisos éticos claros, para que eu use IA de forma responsável.

#### Acceptance Criteria

1. THE Documentacao SHALL conter um documento `ETICA.md` na raiz do repositório, com uma seção própria de no mínimo 1 parágrafo que declare que todo código gerado por IA deve ser revisado por uma pessoa antes de ser commitado, executado ou implantado.
2. THE `ETICA.md` SHALL conter uma seção que oriente a não enviar Segredos (chaves, senhas, tokens, strings de conexão), dados pessoais (nome, CPF, e-mail, telefone, endereço) nem código proprietário em prompts ao Copilot, com no mínimo 1 exemplo de cada categoria.
3. THE `ETICA.md` SHALL conter uma seção que informe que o código gerado pode conter erros, vulnerabilidades ou problemas de licenciamento, e que cite os três riscos de forma explícita.
4. THE `ETICA.md` SHALL conter uma seção que oriente o uso do projeto apenas em ambientes e assinaturas Azure que o usuário possui ou tem autorização formal para usar, e que alerte que a execução em assinaturas de terceiros sem autorização é proibida.
5. THE `ETICA.md` SHALL ser referenciado por link a partir do `README.md`, de modo que seja alcançável em no máximo 1 clique a partir do README.
6. THE Instrucoes_Repositorio SHALL conter uma instrução explícita para que o agente recuse a geração de código malicioso (como malware, exploração de vulnerabilidades sem autorização e negação de serviço) e de código de coleta indevida de dados (como coleta de dados pessoais sem consentimento e exfiltração de Segredos).
7. IF um pedido ao agente exigir código malicioso ou de coleta indevida de dados, THEN THE agente SHALL recusar a parte do pedido que viola a instrução, SHALL informar ao usuário o motivo da recusa e SHALL NOT gerar nenhum trecho do código solicitado.

### Requirement 10: Documentação em português

**User Story:** Como aprendiz, quero documentação completa em português, para que eu siga o projeto passo a passo.

#### Acceptance Criteria

1. THE Repositorio SHALL conter um arquivo `README.md` na raiz, escrito em português do Brasil, com as quatro seções: visão geral, pré-requisitos, estrutura de pastas e início rápido.
2. THE Documentacao SHALL conter um tutorial passo a passo, escrito em português do Brasil, com uma seção numerada para cada uma das cinco etapas: configurar o ambiente, usar o Agente_Copilot, criar funções, testar localmente e fazer deploy.
3. THE Documentacao SHALL descrever cada arquivo de customização do Agente_Copilot existente no Repositorio, e cada descrição SHALL conter o nome do arquivo, seu propósito em até 3 frases e ao menos um exemplo de uso.
4. THE Documentacao SHALL conter uma seção de solução de problemas com no mínimo 5 problemas comuns, e cada problema SHALL ter um sintoma e ao menos um passo de solução.
5. THE Documentacao SHALL conter ao menos um diagrama de arquitetura em sintaxe Mermaid, em bloco de código `mermaid` que seja renderizado sem erro de sintaxe, mostrando no mínimo os componentes VS Code, Agente_Copilot, Azure Functions e Azure.
6. THE Documentacao SHALL listar os 6 pré-requisitos a seguir, cada um com o nome e um link para a página oficial de download ou cadastro: conta Azure, assinatura do GitHub Copilot, VS Code, Azure Functions Core Tools, Azure CLI e Git.
7. THE Repositorio SHALL conter um arquivo `LICENSE` na raiz com o texto completo de uma licença de código aberto, o ano de copyright e o nome do titular.
8. IF um arquivo de customização do Agente_Copilot for adicionado ao Repositorio sem descrição na Documentacao, THEN THE Documentacao SHALL ser considerada incompleta para o critério 3 e a verificação de documentação SHALL reportar o nome do arquivo sem descrição.

### Requirement 11: Restrição de menção à organização educacional

**User Story:** Como responsável pelo projeto, quero que nenhum artefato mencione a organização educacional original, para respeitar a restrição definida.

#### Acceptance Criteria

1. THE Repositorio SHALL omitir todos os Termos_Proibidos em nomes de arquivos, nomes de pastas e conteúdo de arquivos de texto, em todas as branches e em todo commit enviado ao remoto.
2. WHEN o Verificador_Seguranca é executado, THE Verificador_Seguranca SHALL pesquisar os Termos_Proibidos, sem diferenciar maiúsculas de minúsculas, em nomes de arquivos, nomes de pastas e conteúdo de arquivos de texto do Repositorio, e SHALL retornar código de saída 0 quando nenhum Termo_Proibido for encontrado.
3. IF o Verificador_Seguranca encontrar ao menos um Termo_Proibido, THEN THE Verificador_Seguranca SHALL retornar código de saída diferente de zero e SHALL listar, para cada ocorrência, o caminho do arquivo ou pasta e o número da linha (quando a ocorrência estiver no conteúdo), sem alterar nenhum arquivo.
4. WHEN o Workflow_CI_CD é disparado por push ou pull request, THE Workflow_CI_CD SHALL executar a verificação de Termos_Proibidos junto ao Verificador_Seguranca na mesma execução.
5. IF a verificação de Termos_Proibidos retornar código de saída diferente de zero, THEN THE Workflow_CI_CD SHALL marcar a execução como falha e SHALL impedir as etapas subsequentes de build e deploy.
6. THE Documentacao SHALL descrever o projeto como material de estudo independente, sem afiliação, patrocínio ou endosso de qualquer organização educacional.
