# Uso Ético e Responsável de IA

Este projeto usa o GitHub Copilot para ajudar a criar, testar e implantar Azure Functions. A IA acelera o trabalho, mas a responsabilidade pelo resultado continua sendo da pessoa que o utiliza.

## 1. Revisão humana do código gerado por IA

Todo código gerado por IA deve ser revisado por uma pessoa antes de ser commitado, executado ou implantado. Leia o que foi gerado, entenda o que cada trecho faz e confirme que ele atende ao que você pediu. Execute os testes, inspecione comandos que criam, alteram ou excluem recursos no Azure e verifique se não há Segredos, dados pessoais ou dependências inesperadas. A IA não substitui a revisão de código nem a análise de segurança.

## 2. O que não enviar em prompts

Não envie ao Copilot, no chat, em prompt files ou em arquivos anexados:

- **Segredos**: chaves de API, senhas, tokens, strings de conexão e chaves privadas. Exemplo: uma string de conexão de Storage com `AccountKey=...`. Use um placeholder como `<NOME_DO_SEGREDO>`.
- **Dados pessoais**: nome, CPF, e-mail, telefone e endereço. Exemplo: o CPF e o e-mail de um cliente real colados para "testar" uma validação. Use dados fictícios.
- **Código proprietário**: código-fonte, algoritmos ou documentos internos que você não tem autorização para compartilhar. Exemplo: um módulo de cálculo de preços da sua empresa colado inteiro para pedir uma refatoração.

Se você enviou um Segredo por engano, considere-o comprometido e rotacione-o imediatamente, conforme o [SECURITY.md](SECURITY.md).

## 3. Riscos: erros, vulnerabilidades e licenciamento

O código gerado por IA pode conter:

- **Erros**: lógica incorreta, APIs inexistentes ou desatualizadas e testes que não verificam o que deveriam.
- **Vulnerabilidades**: falta de validação de entrada, exposição de dados em logs, permissões excessivas e dependências inseguras.
- **Problemas de licenciamento**: trechos semelhantes a código sob licenças com obrigações (atribuição, copyleft) ou que não permitem o uso pretendido.

Valide o resultado com testes, análise de segurança e verificação das licenças das dependências antes de usá-lo.

## 4. Uso apenas em assinaturas Azure autorizadas

Use este projeto somente em ambientes e assinaturas Azure que você possui ou para os quais tem autorização formal. A execução de deploys, da infraestrutura ou de qualquer comando deste projeto em assinaturas de terceiros sem autorização é proibida.

Antes de executar comandos que criam recursos, confirme a assinatura ativa, entenda os custos e remova os recursos ao final do estudo.

Este projeto é material de estudo independente, sem afiliação, patrocínio ou endosso de qualquer organização educacional.
