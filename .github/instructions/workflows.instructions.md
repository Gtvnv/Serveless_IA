---
applyTo: ".github/workflows/*.{yml,yaml}"
---

# Instruções para workflows do GitHub Actions

## Autenticação no Azure com OIDC
- Use `azure/login` com OIDC (`client-id`, `tenant-id`, `subscription-id`), sem credenciais de longa duração.
- Declare `id-token: write` somente nos jobs que fazem login no Azure.

## Permissions mínimas
- Defina `permissions:` explicitamente no topo do workflow, começando por `contents: read`.
- Eleve permissões apenas no job que precisa delas.

## Secrets e variables
- Segredos ficam em `secrets.*`; valores não sensíveis ficam em `vars.*`.
- Nunca escreva valores de segredos no arquivo do workflow nem os imprima nos logs.
- Não use `pull_request_target` com checkout de código de forks.

## Verificador antes do deploy
- Execute o verificador do repositório e os testes antes de qualquer job de deploy.
- Faça o job de deploy depender deles com `needs:` e rode-o somente na branch de entrega.
- Use `environment:` para permitir aprovação e escopo de segredos no deploy.

## Boas práticas
- Fixe versões das actions (tag principal ou SHA) e as versões do runtime, como a do Python.
- Use `concurrency` para evitar deploys simultâneos.
- Mantenha os jobs curtos e com nomes descritivos.
