// Rythu on Azure — one resource group per environment (dev / prod), ≈ $0/month at pilot scale.
//
//   Static Web App (Free) ── the static Next.js app; browsers call the API directly (CORS)
//   Function App (Flex Consumption, Python 3.12) ── managed identity ──▶ Storage (Table cache, host, deploys)
//        │ logs/requests                                                     ▲
//        ▼                                                                   │ no keys: shared-key access off
//   Application Insights ◀── Log Analytics (daily cap)                       │
//   GitHub Actions ── OIDC (federated credential, no secret) ── deploy identity
//   Budget alert (email) on the resource group
//
// Deploy (once per environment, from Azure Cloud Shell — see README.md in this folder):
//   az deployment group create -g rg-rythu-dev -f infra/azure/main.bicep \
//     -p location=<allowed region> env=dev budgetContactEmail=<you@example.com>
// Decisions: docs/architecture/adr/0001 (hosting), 0002 (Table Storage).

targetScope = 'resourceGroup'

@description('Region. Must be allowed by your subscription policy AND support Flex Consumption (see README).')
param location string

@allowed(['dev', 'prod'])
param env string = 'dev'

@description('Short lowercase name used in resource names.')
@maxLength(8)
param baseName string = 'rythu'

@description('GitHub repository allowed to deploy, exactly as GitHub spells it (owner/name, case-sensitive).')
param githubRepo string = 'Ashishkosana/rythu'

@description('Email that receives budget alerts.')
param budgetContactEmail string

@description('Monthly budget in the billing currency. Alerts at 80% actual and 100% forecast.')
param budgetAmount int = 5

@description('Set false if your subscription type does not support Cost Management budgets.')
param deployBudget bool = true

@description('Budget start: first day of the current month (must not be in the past month).')
param budgetStartDate string = utcNow('yyyy-MM-01')

@description('Flex Consumption scale ceiling (the platform minimum may apply).')
param maximumInstanceCount int = 40

@allowed([512, 2048, 4096])
param instanceMemoryMB int = 512

@description('Static Web Apps region: only where its control plane runs (pages are served from a global edge). Must also be allowed by your subscription policy (README step 0).')
@allowed(['eastasia', 'westeurope', 'eastus2', 'centralus', 'westus2'])
param webLocation string = 'eastasia'

var suffix = uniqueString(resourceGroup().id)
var tags = { app: baseName, env: env }
var storageName = take('st${baseName}${env}${suffix}', 24)
var forecastTable = 'forecast'
var deploymentContainer = 'deployments'

// Built-in role IDs (verified against learn.microsoft.com built-in roles reference).
var roleStorageBlobDataOwner = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
var roleStorageTableDataContributor = '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'

// ── Observability ────────────────────────────────────────────────────────────────────────────
resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${baseName}-${env}-${suffix}'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
    // Cost guardrail: ingestion stops for the day past this (pilot volume is a few MB/day).
    workspaceCapping: { dailyQuotaGb: json('0.1') }
  }
}

resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${baseName}-${env}-${suffix}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}

// ── Storage: forecast cache, Functions host state, deployment packages ──────────────────────
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    // Identity-only: no account keys to leak. Everything authenticates with Entra ID.
    allowSharedKeyAccess: false
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource deployments 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: deploymentContainer
}

resource tableService 'Microsoft.Storage/storageAccounts/tableServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource forecast 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-05-01' = {
  parent: tableService
  name: forecastTable
}

// Cells farmers use (what the pre-warm timer refreshes) and the shared hourly upstream budget.
resource cellsTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-05-01' = {
  parent: tableService
  name: 'cells'
}

resource budgetTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-05-01' = {
  parent: tableService
  name: 'budget'
}

// ── Compute: Flex Consumption Function App ──────────────────────────────────────────────────
resource plan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: 'plan-${baseName}-${env}-${suffix}'
  location: location
  tags: tags
  kind: 'functionapp'
  sku: { name: 'FC1', tier: 'FlexConsumption' }
  properties: { reserved: true }
}

resource api 'Microsoft.Web/sites@2024-04-01' = {
  name: 'func-${baseName}-${env}-${suffix}'
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
      appSettings: [
        // Host state via managed identity (no connection string).
        { name: 'AzureWebJobsStorage__accountName', value: storage.name }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: insights.properties.ConnectionString }
        // Rythu settings (services/weather/src/rythu_weather/app/settings.py).
        { name: 'RYTHU_AZURE_TABLES_ENDPOINT', value: storage.properties.primaryEndpoints.table }
        { name: 'RYTHU_AZURE_FORECAST_TABLE', value: forecastTable }
        { name: 'RYTHU_LOG_LEVEL', value: 'INFO' }
      ]
    }
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storage.properties.primaryEndpoints.blob}${deploymentContainer}'
          authentication: { type: 'SystemAssignedIdentity' }
        }
      }
      scaleAndConcurrency: {
        maximumInstanceCount: maximumInstanceCount
        instanceMemoryMB: instanceMemoryMB
      }
      runtime: { name: 'python', version: '3.12' }
    }
  }
  dependsOn: [deployments]
}

// The app's own identity: full blob access (host state + its deployment package) and table data
// access (forecast cache) on this one storage account — nothing else.
resource apiBlobOwner 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, api.id, roleStorageBlobDataOwner)
  scope: storage
  properties: {
    principalId: api.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleStorageBlobDataOwner)
  }
}

resource apiTableContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, api.id, roleStorageTableDataContributor)
  scope: storage
  properties: {
    principalId: api.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleStorageTableDataContributor)
  }
}

// ── Web app: the static export (apps/web/out) on Static Web Apps, Free tier ─────────────────
// Routing, security headers and the CSP come with each deploy in staticwebapp.config.json
// (generated by apps/web/scripts/postbuild.mjs), so this resource stays minimal.
resource web 'Microsoft.Web/staticSites@2024-04-01' = {
  name: 'stapp-${baseName}-${env}-${suffix}'
  location: webLocation
  tags: tags
  sku: { name: 'Free', tier: 'Free' }
  properties: {
    allowConfigFileUpdates: true
    stagingEnvironmentPolicy: 'Disabled' // deploys come only from main, via our own workflow
  }
}

// ── GitHub Actions deploy identity: OIDC, no stored secret ──────────────────────────────────
// Trusts only workflow jobs in `githubRepo` that run in the GitHub Environment named `env`.
// Its two permissions (Website Contributor on the Function App; Contributor on the Static Web App, to
// read the deployment token at deploy time) are granted by name in the README step, so this template
// carries no unverified role IDs.
resource deployer 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${baseName}-${env}-deploy'
  location: location
  tags: tags
}

resource githubTrust 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: deployer
  name: 'github-${env}'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:${githubRepo}:environment:${env}'
    audiences: ['api://AzureADTokenExchange']
  }
}

// ── Cost guardrail ──────────────────────────────────────────────────────────────────────────
resource budget 'Microsoft.Consumption/budgets@2021-10-01' = if (deployBudget) {
  name: 'budget-${baseName}-${env}'
  properties: {
    category: 'Cost'
    amount: budgetAmount
    timeGrain: 'Monthly'
    timePeriod: { startDate: budgetStartDate }
    notifications: {
      actual80: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 80
        thresholdType: 'Actual'
        contactEmails: [budgetContactEmail]
      }
      forecast100: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        thresholdType: 'Forecasted'
        contactEmails: [budgetContactEmail]
      }
    }
  }
}

output functionAppName string = api.name
output functionAppUrl string = 'https://${api.properties.defaultHostName}'
output functionAppId string = api.id
output storageAccountName string = storage.name
output webAppName string = web.name
output webAppUrl string = 'https://${web.properties.defaultHostname}'
output webAppId string = web.id
output deployClientId string = deployer.properties.clientId
output deployPrincipalId string = deployer.properties.principalId
