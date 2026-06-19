@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Short environment name, e.g. prod or staging — used as resource name suffix')
param envName string = 'prod'

@description('ACR login server, e.g. myregistry.azurecr.io')
param acrServer string

@description('API image reference, e.g. myregistry.azurecr.io/wc2026-api:sha-abc123')
param apiImageTag string

@description('Frontend image reference, e.g. myregistry.azurecr.io/wc2026-frontend:sha-abc123')
param frontendImageTag string

@description('Job image reference, e.g. myregistry.azurecr.io/wc2026-job:sha-abc123')
param jobImageTag string

@secure()
param postgresAdminUser string

@secure()
param postgresAdminPassword string

@secure()
param apiFootballKey string

@secure()
param deepseekApiKey string

// ---------------------------------------------------------------------------
// Postgres
// ---------------------------------------------------------------------------

module postgres 'postgres.bicep' = {
  name: 'postgres'
  params: {
    location: location
    envName: envName
    adminUser: postgresAdminUser
    adminPassword: postgresAdminPassword
  }
}

// Construct DATABASE_URL from postgres module outputs + secure params.
// psycopg v3 DSN — sslmode=require is mandatory for Azure Flexible Server.
var databaseUrl = 'postgresql+psycopg://${postgresAdminUser}:${postgresAdminPassword}@${postgres.outputs.serverFqdn}/${postgres.outputs.databaseName}?sslmode=require'

// ---------------------------------------------------------------------------
// Container Apps + Job
// ---------------------------------------------------------------------------

module containerApps 'container-apps.bicep' = {
  name: 'containerApps'
  params: {
    location: location
    envName: envName
    acrServer: acrServer
    apiImage: apiImageTag
    frontendImage: frontendImageTag
    databaseUrl: databaseUrl
    apiFootballKey: apiFootballKey
    deepseekApiKey: deepseekApiKey
  }
}

module briefJob 'container-app-job.bicep' = {
  name: 'briefJob'
  params: {
    location: location
    containerAppsEnvId: containerApps.outputs.containerAppsEnvId
    jobImage: jobImageTag
    databaseUrl: databaseUrl
    apiFootballKey: apiFootballKey
    deepseekApiKey: deepseekApiKey
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

output apiUrl string = 'https://${containerApps.outputs.apiAppFqdn}'
output frontendUrl string = containerApps.outputs.frontendUrl
output postgresServerFqdn string = postgres.outputs.serverFqdn
