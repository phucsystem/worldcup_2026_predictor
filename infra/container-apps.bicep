@description('Azure region')
param location string = resourceGroup().location

@description('Unique suffix for resource names')
param envName string

@description('ACR login server, e.g. myreg.azurecr.io')
param acrServer string

@description('API image tag, e.g. myreg.azurecr.io/wc2026-api:latest')
param apiImage string

@description('Frontend image tag, e.g. myreg.azurecr.io/wc2026-frontend:latest')
param frontendImage string

@secure()
@description('PostgreSQL connection string (postgresql+psycopg://...)')
param databaseUrl string

@secure()
@description('API-Football API key')
param apiFootballKey string

@secure()
@description('DeepSeek API key')
param deepseekApiKey string

// Container Apps Environment (Log Analytics workspace auto-created)
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'wc2026-logs-${envName}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource caEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'wc2026-env-${envName}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// ACR pull credentials via admin password — use managed identity for tighter prod setup
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: split(acrServer, '.')[0]
}

// API Container App
resource apiApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'wc2026-api-${envName}'
  location: location
  properties: {
    environmentId: caEnv.id
    configuration: {
      ingress: {
        external: false
        targetPort: 8000
        transport: 'http'
      }
      registries: [
        {
          server: acrServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        { name: 'acr-password', value: acr.listCredentials().passwords[0].value }
        { name: 'database-url', value: databaseUrl }
        { name: 'api-football-key', value: apiFootballKey }
        { name: 'deepseek-api-key', value: deepseekApiKey }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'API_FOOTBALL_KEY', secretRef: 'api-football-key' }
            { name: 'DEEPSEEK_API_KEY', secretRef: 'deepseek-api-key' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

// Next.js SSR Container App (public ingress)
resource frontendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'wc2026-frontend-${envName}'
  location: location
  properties: {
    environmentId: caEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'http'
      }
      registries: [
        {
          server: acrServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        { name: 'acr-password', value: acr.listCredentials().passwords[0].value }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: frontendImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'API_BASE', value: 'https://${apiApp.properties.configuration.ingress.fqdn}' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

output containerAppsEnvId string = caEnv.id
output apiAppFqdn string = apiApp.properties.configuration.ingress.fqdn
output frontendUrl string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'
