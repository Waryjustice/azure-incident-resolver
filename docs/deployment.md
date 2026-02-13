# Deployment Guide

## Prerequisites

Before deploying Azure Incident Resolver, ensure you have:

- Azure subscription with sufficient credits
- Azure CLI installed and configured
- GitHub account with Copilot access
- Node.js 18+ or Python 3.11+
- Docker (for containerization)
- kubectl (for Kubernetes deployment)

## Quick Start (Local Development)

### 1. Clone and Setup

```bash
git clone https://github.com/YOUR_USERNAME/azure-incident-resolver.git
cd azure-incident-resolver

# Install dependencies
npm install
# OR
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your Azure credentials:

```bash
# Required
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
```

### 3. Run Locally in Test Mode

```bash
# Set test mode to simulate an incident
export TEST_MODE=true

# Run the orchestrator
python src/orchestration/orchestrator.py
# OR
node src/orchestration/orchestrator.js
```

## Azure Deployment

### Step 1: Create Azure Resources

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription YOUR_SUBSCRIPTION_ID

# Create resource group
az group create \
  --name azure-incident-resolver-rg \
  --location eastus

# Deploy infrastructure (this will create all required resources)
./scripts/deploy-infrastructure.sh
```

This script creates:
- Azure Kubernetes Service (AKS) cluster
- Azure Monitor workspace
- Application Insights
- Azure OpenAI instance
- Azure Container Registry
- Azure Database for incident storage

### Step 2: Configure Microsoft Foundry

```bash
# Create Foundry knowledge base
az foundry knowledge-base create \
  --name incident-knowledge-base \
  --resource-group azure-incident-resolver-rg

# Upload initial incident data (optional)
az foundry data upload \
  --knowledge-base incident-knowledge-base \
  --source ./data/sample-incidents/
```

### Step 3: Setup GitHub Integration

1. Create a GitHub Personal Access Token with repo access
2. Add token to Azure Key Vault:

```bash
az keyvault secret set \
  --vault-name azure-incident-resolver-kv \
  --name github-token \
  --value YOUR_GITHUB_TOKEN
```

3. Configure GitHub Copilot Agent Mode access (follow Microsoft docs)

### Step 4: Build and Push Container Images

```bash
# Login to Azure Container Registry
az acr login --name azureincidentresolveracr

# Build images
docker build -t azureincidentresolveracr.azurecr.io/detection-agent:latest \
  -f docker/detection.Dockerfile .

docker build -t azureincidentresolveracr.azurecr.io/diagnosis-agent:latest \
  -f docker/diagnosis.Dockerfile .

docker build -t azureincidentresolveracr.azurecr.io/resolution-agent:latest \
  -f docker/resolution.Dockerfile .

docker build -t azureincidentresolveracr.azurecr.io/communication-agent:latest \
  -f docker/communication.Dockerfile .

# Push images
docker push azureincidentresolveracr.azurecr.io/detection-agent:latest
docker push azureincidentresolveracr.azurecr.io/diagnosis-agent:latest
docker push azureincidentresolveracr.azurecr.io/resolution-agent:latest
docker push azureincidentresolveracr.azurecr.io/communication-agent:latest
```

### Step 5: Deploy to AKS

```bash
# Get AKS credentials
az aks get-credentials \
  --resource-group azure-incident-resolver-rg \
  --name azure-incident-resolver-aks

# Apply Kubernetes manifests
kubectl apply -f infrastructure/kubernetes/
```

### Step 6: Verify Deployment

```bash
# Check pods are running
kubectl get pods

# Check logs
kubectl logs -f deployment/detection-agent
kubectl logs -f deployment/diagnosis-agent
kubectl logs -f deployment/resolution-agent
kubectl logs -f deployment/communication-agent

# Access dashboard (port forward)
kubectl port-forward service/dashboard 8080:80
# Open http://localhost:8080
```

## Configuration

### Azure Monitor Integration

Configure which resources to monitor:

```yaml
# infrastructure/config/monitored-resources.yaml
resources:
  - type: AppService
    name: my-api-service
    metrics:
      - CPU_PERCENTAGE
      - MEMORY_PERCENTAGE
      - RESPONSE_TIME
    
  - type: Database
    name: production-db
    metrics:
      - CONNECTION_COUNT
      - DTU_PERCENTAGE
      - DEADLOCKS
```

### Agent Configuration

Customize agent behavior:

```yaml
# infrastructure/config/agents.yaml
detection:
  monitoring_interval: 60  # seconds
  anomaly_threshold: 2.0   # standard deviations
  
diagnosis:
  timeout: 300  # seconds
  confidence_threshold: 70  # minimum confidence %
  
resolution:
  auto_approve_prs: false
  max_retry_attempts: 3
  
communication:
  channels:
    - teams
    - slack
  notification_levels:
    - critical
    - high
```

## Post-Deployment Setup

### 1. Configure Notifications

**Microsoft Teams:**
```bash
# Create incoming webhook in Teams
# Add webhook URL to Key Vault
az keyvault secret set \
  --vault-name azure-incident-resolver-kv \
  --name teams-webhook-url \
  --value YOUR_TEAMS_WEBHOOK_URL
```

**Slack:**
```bash
# Create Slack app and webhook
# Add webhook URL to Key Vault
az keyvault secret set \
  --vault-name azure-incident-resolver-kv \
  --name slack-webhook-url \
  --value YOUR_SLACK_WEBHOOK_URL
```

### 2. Test the System

```bash
# Trigger a test incident
kubectl exec -it deployment/orchestrator -- \
  python scripts/trigger-test-incident.py
```

### 3. Monitor Performance

Access the dashboard at the load balancer IP:

```bash
# Get external IP
kubectl get service dashboard

# Open in browser
# http://EXTERNAL_IP
```

## CI/CD Setup (GitHub Actions)

GitHub Actions workflow is already configured in `.github/workflows/deploy.yml`

Required GitHub Secrets:
- `AZURE_CREDENTIALS`
- `ACR_USERNAME`
- `ACR_PASSWORD`
- `AZURE_SUBSCRIPTION_ID`

The workflow automatically:
1. Runs tests
2. Builds Docker images
3. Pushes to ACR
4. Deploys to AKS

## Troubleshooting

### Agents not detecting incidents

```bash
# Check Azure Monitor connection
kubectl exec -it deployment/detection-agent -- \
  python -c "from agents.detection.agent import DetectionAgent; DetectionAgent().test_connection()"

# Check logs
kubectl logs deployment/detection-agent --tail=100
```

### GitHub Copilot integration failing

```bash
# Verify GitHub token
kubectl get secret github-credentials -o yaml

# Test GitHub API access
kubectl exec -it deployment/resolution-agent -- \
  curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Microsoft Foundry errors

```bash
# Check Foundry endpoint
kubectl exec -it deployment/diagnosis-agent -- \
  curl -X POST $FOUNDRY_ENDPOINT/search \
  -H "Authorization: Bearer $FOUNDRY_API_KEY" \
  -d '{"query": "test"}'
```

## Scaling

### Horizontal Pod Autoscaling

```bash
# Enable autoscaling for detection agent
kubectl autoscale deployment detection-agent \
  --cpu-percent=70 \
  --min=2 \
  --max=10
```

### Database Scaling

```bash
# Scale Azure Database tier
az sql db update \
  --resource-group azure-incident-resolver-rg \
  --server incident-db-server \
  --name incidents \
  --service-objective S3
```

## Backup & Disaster Recovery

### Backup Incident Data

```bash
# Automated daily backups configured
# Manual backup:
az postgres backup create \
  --resource-group azure-incident-resolver-rg \
  --server-name incident-db
```

### Restore from Backup

```bash
az postgres restore \
  --resource-group azure-incident-resolver-rg \
  --name incident-db-restored \
  --source-server incident-db \
  --restore-point-in-time "2026-02-13T12:00:00Z"
```

## Cost Optimization

- Use Azure Reserved Instances for AKS nodes (up to 72% savings)
- Enable autoscaling to scale down during low activity
- Use Azure Spot instances for non-critical workloads
- Monitor with Azure Cost Management

Estimated monthly cost: $200-500 depending on traffic

## Security Checklist

- [ ] Azure Managed Identity enabled for all services
- [ ] Secrets stored in Key Vault (not environment variables)
- [ ] Network policies configured in AKS
- [ ] Private endpoints for Azure services
- [ ] RBAC roles properly assigned
- [ ] Audit logging enabled
- [ ] SSL/TLS for all external connections
- [ ] Regular security scans with Azure Defender

## Support

For issues, please:
1. Check logs: `kubectl logs deployment/[agent-name]`
2. Review GitHub Issues
3. Contact the team via Microsoft Teams
