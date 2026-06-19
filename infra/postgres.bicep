@description('Azure region')
param location string = resourceGroup().location

@description('Unique suffix for resource names')
param envName string

@secure()
@description('Postgres admin username')
param adminUser string

@secure()
@description('Postgres admin password (min 8 chars, mixed case, digit, special)')
param adminPassword string

var serverName = 'wc2026-pg-${envName}'

resource pgServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: serverName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: adminUser
    administratorLoginPassword: adminPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    version: '16'
    highAvailability: {
      mode: 'Disabled'
    }
  }
}

resource worldcupDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: pgServer
  name: 'worldcup'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// TODO: tighten to Container Apps subnet once VNet integration is configured.
// For V1 speed, allow Azure services; restrict source IPs before going public.
resource firewallAzureServices 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: pgServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

output serverFqdn string = pgServer.properties.fullyQualifiedDomainName
output serverName string = pgServer.name
output databaseName string = worldcupDb.name
// Caller constructs: postgresql+psycopg://{adminUser}:{adminPassword}@{serverFqdn}/{databaseName}?sslmode=require
