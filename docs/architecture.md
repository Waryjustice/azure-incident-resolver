# Architecture Overview

## System Architecture

Azure Incident Resolver is a multi-agent system that automates incident detection, diagnosis, and resolution in Azure environments.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure Resources                           │
│  (App Services, Databases, VMs, AKS, Functions, etc.)           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Metrics & Logs
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Azure Monitor                               │
│              Application Insights                                │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Event Stream
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DETECTION AGENT                               │
│  • Monitors Azure resources                                      │
│  • AI-powered anomaly detection                                  │
│  • Triggers incident workflow                                    │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Azure MCP
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DIAGNOSIS AGENT                               │
│  • Analyzes logs and metrics                                     │
│  • Microsoft Foundry RAG search                                  │
│  • Identifies root cause                                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Azure MCP
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESOLUTION AGENT                              │
│  • Executes automated fixes                                      │
│  • GitHub Copilot Agent Mode                                     │
│  • Creates fix PRs                                               │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Azure MCP
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  COMMUNICATION AGENT                             │
│  • Stakeholder notifications                                     │
│  • Post-mortem generation                                        │
│  • Incident learning                                             │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  External Integrations                           │
│         Teams, GitHub, Status Pages                              │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Communication Flow

Agents communicate using Azure MCP (Model Context Protocol) for standardized message passing:

```
Detection Agent ──[incident_detected]──> Diagnosis Agent
                                              │
                                              ▼
Diagnosis Agent ──[diagnosis_complete]──> Resolution Agent
                                              │
                                              ▼
Resolution Agent ──[resolution_complete]──> Communication Agent
```

## Technology Stack

### Core Technologies (Required by Hackathon)
- **Microsoft Foundry**: Knowledge base and RAG for past incidents
- **Microsoft Agent Framework**: Multi-agent orchestration
- **Azure MCP**: Inter-agent communication protocol
- **GitHub Copilot Agent Mode**: Automated code generation

### Azure Services
- **Azure Monitor**: Metrics collection
- **Application Insights**: Log aggregation and tracing
- **Azure Functions**: Serverless agent hosting
- **Azure OpenAI**: Natural language processing
- **Azure Database**: Incident history storage
- **Azure Key Vault**: Secrets management

### Development Tools
- **GitHub**: Source code management
- **GitHub Actions**: CI/CD automation
- **VS Code**: Development environment
- **GitHub Copilot**: AI-assisted development

## Data Flow

1. **Detection Phase**
   - Azure Monitor streams metrics to Detection Agent
   - Agent applies anomaly detection algorithms
   - Incidents created when thresholds exceeded

2. **Diagnosis Phase**
   - Incident data sent to Diagnosis Agent via Azure MCP
   - Agent queries logs from Application Insights
   - Microsoft Foundry RAG searches past incidents
   - Azure OpenAI analyzes data for root cause

3. **Resolution Phase**
   - Diagnosis sent to Resolution Agent
   - Agent determines resolution strategy
   - Immediate fixes executed via Azure APIs
   - GitHub Copilot generates permanent fix code
   - PR created with proposed changes

4. **Communication Phase**
   - Updates sent throughout workflow
   - Final post-mortem generated using Azure OpenAI
   - Incident saved to knowledge base for future RAG

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Azure Kubernetes Service                    │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Detection   │  │  Diagnosis   │  │  Resolution  │          │
│  │    Agent     │  │    Agent     │  │    Agent     │          │
│  │  (Pod)       │  │  (Pod)       │  │  (Pod)       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │Communication │  │ Orchestrator │                             │
│  │    Agent     │  │   (Pod)      │                             │
│  │  (Pod)       │  │              │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘

         ▲                    ▲                     ▲
         │                    │                     │
         ├────────────────────┴─────────────────────┤
         │         Azure Load Balancer               │
         └───────────────────────────────────────────┘
```

## Scalability & Resilience

- **Horizontal Scaling**: Each agent can scale independently
- **Load Balancing**: Azure Load Balancer distributes traffic
- **State Management**: Incident state stored in Azure Database
- **Retry Logic**: Failed operations retry with exponential backoff
- **Circuit Breakers**: Prevent cascade failures
- **Health Checks**: Kubernetes liveness and readiness probes

## Security

- **Authentication**: Azure Managed Identity
- **Authorization**: Azure RBAC for resource access
- **Secrets**: Azure Key Vault for credentials
- **Network**: Private endpoints and VNet integration
- **Audit**: All actions logged to Azure Monitor

## Monitoring & Observability

- **Metrics**: Prometheus metrics exported from each agent
- **Logs**: Structured logging to Application Insights
- **Traces**: Distributed tracing with correlation IDs
- **Dashboard**: Real-time incident dashboard
- **Alerts**: Configured for agent health and performance

## Demo Scenarios

### Scenario 1: Database Connection Spike
```
Detection: Connection pool at 100%
Diagnosis: Connection leak in API Gateway
Resolution: Scale database tier + Create PR to fix leak
Time: < 5 minutes
```

### Scenario 2: Memory Leak
```
Detection: Pod memory usage exceeds 90%
Diagnosis: Memory leak in caching service
Resolution: Restart pod + Generate fix code
Time: < 3 minutes
```

### Scenario 3: API Rate Limit
```
Detection: Rate limit errors increasing
Diagnosis: Third-party API throttling
Resolution: Enable circuit breaker + Implement backoff
Time: < 2 minutes
```

## Future Enhancements

- **Predictive Detection**: ML models to predict incidents before they occur
- **Self-Learning**: Agents improve strategies based on outcomes
- **Multi-Cloud**: Support for AWS and GCP resources
- **Custom Runbooks**: User-defined resolution workflows
- **A/B Testing**: Test different resolution strategies
