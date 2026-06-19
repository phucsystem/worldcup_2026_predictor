// Azure Container Apps Job — World Cup 2026 Daily Brief Scheduler
//
// DST strategy: Container Apps cron is UTC-only. Two cron expressions cover
// 07:00 Australia/Melbourne across both offsets:
//   "0 20 * * *"  → 07:00 AEDT (UTC+11, Oct–Apr daylight saving)
//   "0 21 * * *"  → 07:00 AEST (UTC+10, Apr–Oct standard time)
// The in-process TZ guard (scheduler_entry.py) ensures exactly one of the two
// daily triggers actually runs the pipeline; the other exits 0 immediately.
//
// RECOMMENDED: deploy this module twice with distinct jobName params:
//   jobName = 'wc2026-brief-job-aest'  cronExpression = '0 21 * * *'
//   jobName = 'wc2026-brief-job-aedt'  cronExpression = '0 20 * * *'

@description('Name for the Container Apps Job resource')
param jobName string = 'wc2026-brief-job'

@description('Azure region for deployment')
param location string = resourceGroup().location

@description('Container Apps Environment resource ID')
param containerAppsEnvId string

@description('Full image reference, e.g. myregistry.azurecr.io/wc2026-brief-job:latest')
param jobImage string

@secure()
@description('PostgreSQL connection string')
param databaseUrl string

@secure()
@description('API-Football API key')
param apiFootballKey string

@secure()
@description('DeepSeek API key')
param deepseekApiKey string

@description('CRON expression in UTC (default: 07:00 AEST = 21:00 UTC)')
param cronExpression string = '0 21 * * *'

@description('CPU cores allocated per replica')
param cpuCores string = '0.5'

@description('Memory allocated per replica')
param memoryGi string = '1Gi'

resource briefJob 'Microsoft.App/jobs@2023-05-01' = {
  name: jobName
  location: location
  properties: {
    environmentId: containerAppsEnvId
    configuration: {
      triggerType: 'Schedule'
      replicaTimeout: 1800
      replicaRetryLimit: 1
      scheduleTriggerConfig: {
        cronExpression: cronExpression
        parallelism: 1
        replicaCompletionCount: 1
      }
      secrets: [
        { name: 'database-url', value: databaseUrl }
        { name: 'football-key', value: apiFootballKey }
        { name: 'deepseek-key', value: deepseekApiKey }
      ]
    }
    template: {
      containers: [
        {
          name: 'brief-runner'
          image: jobImage
          resources: {
            cpu: json(cpuCores)
            memory: memoryGi
          }
          env: [
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'API_FOOTBALL_KEY', secretRef: 'football-key' }
            { name: 'DEEPSEEK_API_KEY', secretRef: 'deepseek-key' }
            { name: 'BRIEF_TIMEZONE', value: 'Australia/Melbourne' }
          ]
        }
      ]
    }
  }
}

output jobResourceId string = briefJob.id
output jobName string = briefJob.name
