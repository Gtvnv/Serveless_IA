// Infraestrutura do Function_App (Requisitos 7.1 a 7.6).
// Recursos: plano de hospedagem, conta de armazenamento, Application Insights,
// Function_App e atribuições RBAC de menor privilégio.
// Nenhum Segredo neste template nem nos parâmetros: o host acessa o armazenamento
// por identidade gerenciada (AzureWebJobsStorage__accountName), sem chave.

targetScope = 'resourceGroup'

@description('Nome do Function_App (único globalmente).')
param nomeFunctionApp string

@description('Nome do plano de hospedagem.')
param nomePlano string

@description('Nome da conta de armazenamento (3 a 24 caracteres, minúsculas e números).')
@minLength(3)
@maxLength(24)
param nomeContaArmazenamento string

@description('Nome do recurso Application Insights.')
param nomeApplicationInsights string

@description('Região dos recursos.')
param regiao string = resourceGroup().location

@description('SKU do plano de hospedagem. Y1 (Dynamic) é o plano de consumo.')
param skuPlano string = 'Y1'

@description('Camada do plano de hospedagem. Dynamic para consumo.')
param camadaPlano string = 'Dynamic'

@description('SKU da conta de armazenamento.')
param skuArmazenamento string = 'Standard_LRS'

// IDs das funções internas do Azure (somente funções de dados, nunca Owner,
// Contributor ou User Access Administrator).
var funcoesArmazenamento = [
  {
    nome: 'Storage Blob Data Owner'
    id: 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
  }
  {
    nome: 'Storage Queue Data Contributor'
    id: '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
  }
  {
    nome: 'Storage Table Data Contributor'
    id: '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'
  }
]

resource contaArmazenamento 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: nomeContaArmazenamento
  location: regiao
  kind: 'StorageV2'
  sku: {
    name: skuArmazenamento
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

// Application Insights em modo clássico (sem workspace), para manter somente os
// recursos previstos. A Microsoft recomenda o modo baseado em workspace (exige um
// Log Analytics); se a assinatura recusar o modo clássico, adicione o workspace
// e o parâmetro WorkspaceResourceId.
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: nomeApplicationInsights
  location: regiao
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

resource planoHospedagem 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: nomePlano
  location: regiao
  kind: 'functionapp'
  sku: {
    name: skuPlano
    tier: camadaPlano
  }
  properties: {
    reserved: true // obrigatório para Linux
  }
}

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: nomeFunctionApp
  location: regiao
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: planoHospedagem.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: [
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          // Armazenamento do host por identidade gerenciada (sem chave).
          name: 'AzureWebJobsStorage__accountName'
          value: contaArmazenamento.name
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsights.properties.ConnectionString
        }
      ]
    }
  }
}

// RBAC com escopo na conta de armazenamento (um único recurso).
resource atribuicoesArmazenamento 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for funcao in funcoesArmazenamento: {
    name: guid(contaArmazenamento.id, functionApp.id, funcao.id)
    scope: contaArmazenamento
    properties: {
      principalId: functionApp.identity.principalId
      principalType: 'ServicePrincipal'
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', funcao.id)
    }
  }
]

output nomeFunctionApp string = functionApp.name
output principalIdFunctionApp string = functionApp.identity.principalId
