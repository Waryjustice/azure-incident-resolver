# Azure Incident Resolver — Features & Usage Guide

## What Is This Project?

Azure Incident Resolver is an autonomous, multi-agent SRE (Site Reliability Engineering) system built on Azure. It monitors a live Azure environment, detects anomalies, diagnoses root causes using AI, executes automated fixes, and notifies stakeholders — all without human intervention. The agents are coordinated by Microsoft Semantic Kernel and communicate with each other via Azure Service Bus message queues.

---

## Architecture Overview

```
Azure Monitor
     │
     ▼
┌─────────────────┐     Service Bus Queue        ┌─────────────────────┐
│ Detection Agent │ ─── detection-to-diagnosis ──▶│  Diagnosis Agent    │
│                 │                               │  (GitHub Models AI) │
└─────────────────┘                               └──────────┬──────────┘
                                                             │ Service Bus Queue
                                                             │ diagnosis-to-resolution
                                                             ▼
                                                  ┌─────────────────────┐
                                                  │  Resolution Agent   │
                                                  │  (GitHub Copilot)   │
                                                  └──────────┬──────────┘
                                                             │ Service Bus Queue
                                                             │ resolution-to-communication
                                                             ▼
                                                  ┌─────────────────────┐
                                                  │ Communication Agent │
                                                  │  (Post-mortems)     │
                                                  └─────────────────────┘
```

All inter-agent communication flows through **Azure Service Bus** queues. The orchestrator can also run all agents in-process using **Microsoft Semantic Kernel** plugins for demo and testing.

---

## The Four Agents

### 1. Detection Agent (`src/agents/detection/agent.py`)

Continuously polls Azure Monitor (Log Analytics) for anomalies in a monitored Azure Web App.

| Feature | Status |
|---------|--------|
| Connects to Azure Monitor Log Analytics workspace | ✅ Real |
| Runs KQL queries for CPU and Memory metrics | ✅ Real |
| Applies configurable thresholds (CPU: 80%, Memory: 85%) | ✅ Real |
| Calculates incident severity (low / medium / high / critical) | ✅ Real |
| Sends structured incident JSON to Service Bus queue | ✅ Real |
| Polls on a configurable interval (`DETECTION_AGENT_INTERVAL_SECONDS`) | ✅ Real |
| Verifies Azure Monitor connection on startup | ✅ Real |
| Discovers available metrics for the monitored resource | ✅ Real |
| The anomaly data itself (no real Azure resource needed in demo mode) | 🟡 Simulated |

**What it sends downstream:**
```json
{
  "id": "INC-20260308182000",
  "resource": { "type": "WebApp", "id": "...", "name": "..." },
  "anomalies": [
    { "metric": "CPU_PERCENTAGE", "value": 96, "threshold": 80, "severity": "critical" }
  ],
  "detected_at": "2026-03-08T18:20:00Z",
  "severity": "critical"
}
```

---

### 2. Diagnosis Agent (`src/agents/diagnosis/agent.py`)

Receives incidents from the Detection Agent, gathers context, calls GitHub Models AI (GPT-4o-mini) to identify the root cause, and forwards a structured diagnosis.

| Feature | Status |
|---------|--------|
| Receives incident from Service Bus queue | ✅ Real |
| Builds structured context from anomaly data | ✅ Real |
| Calls GitHub Models AI (GPT-4o-mini via `azure-ai-inference` SDK) | ✅ Real |
| AI returns root cause type, description, component, and evidence | ✅ Real |
| In-memory RAG: searches past incidents for similar patterns | ✅ Real |
| Rule-based fallback when AI is unavailable | ✅ Real |
| Confidence score calculation based on evidence and past matches | ✅ Real |
| Sends structured diagnosis to Service Bus queue | ✅ Real |
| Impact assessment (affected users count, business impact) | 🟡 Simulated (placeholder values) |

**AI prompt input:**
```
INCIDENT: INC-20260308182000
SEVERITY: HIGH
RESOURCE: WebApp — Production Web App

ANOMALIES DETECTED:
  • CONNECTION_COUNT at 500 (5.0x threshold of 100)

PEAK VALUES vs THRESHOLDS: { "CONNECTION_COUNT": 500 }

Based on this data, identify the root cause.
```

**AI response (example):**
```json
{
  "type": "database_connection_exhaustion",
  "description": "Database connection pool exhausted due to connection leak",
  "affected_component": "API Gateway",
  "evidence": [
    "CONNECTION_COUNT exceeded threshold by 400%",
    "Severity: high",
    "Incident ID: INC-20260308182000"
  ]
}
```

---

### 3. Resolution Agent (`src/agents/resolution/agent.py`)

Receives the diagnosis, determines the best remediation strategy, executes an immediate automated fix against real Azure resources, and creates a GitHub PR with a permanent code fix generated by GitHub Copilot CLI.

| Feature | Status |
|---------|--------|
| Receives diagnosis from Service Bus queue | ✅ Real |
| Strategy selection based on root cause type (keyword matching) | ✅ Real |
| **Scale Azure SQL Database** — upgrades SKU tier using Azure Management SDK | ✅ Real |
| **Restart Azure App Service** — calls App Service restart API | ✅ Real |
| **Enable circuit breaker** — writes app settings to Azure App Service | ✅ Real |
| **Rollback deployment** — swaps staging↔production slot (or restarts) | ✅ Real |
| Calls `gh copilot suggest` CLI for code fix generation | ✅ Real (requires `gh` CLI + Copilot) |
| Creates GitHub branch and PR with the generated fix | ✅ Real (requires `GITHUB_TOKEN`) |
| Masks sensitive data (API keys, passwords, SSNs, emails) before sending to Copilot | ✅ Real |
| Sends resolution to Service Bus queue | ✅ Real |
| Permanent code fix content (stubs for memory leak and retry) | 🟡 Partially simulated |

**Immediate fix strategies:**

| Root Cause | Immediate Fix | Permanent Fix |
|-----------|--------------|--------------|
| Database connection exhaustion | Scale SQL Database tier | Implement connection pooling |
| Memory leak / OOM | Restart App Service | Fix memory leak code |
| Rate limiting / throttling | Enable circuit breaker | Implement backoff retry |
| Failed deployment | Rollback deployment slot | Fix deployment config |
| CPU spike | Restart App Service | Fix memory leak code |

---

### 4. Communication Agent (`src/agents/communication/agent.py`)

Receives the resolution, sends lifecycle notifications, generates a post-mortem report, and escalates to on-call engineers when automation fails.

| Feature | Status |
|---------|--------|
| Receives resolution from Service Bus queue | ✅ Real |
| Formats detection / diagnosis / resolution notification messages | ✅ Real |
| Builds incident timeline from timestamps | ✅ Real |
| Generates post-mortem report structure | ✅ Real |
| Escalation logging (with full incident context) | ✅ Real |
| Sending notifications externally (Teams, email, PagerDuty) | 🟡 Simulated (logs only — webhook removed) |
| Saving post-mortem to persistent database | 🟡 Simulated (in-memory / logs only) |
| AI-generated lessons learned and action items | 🟡 Simulated (placeholder strings) |

**Post-mortem structure generated:**
```json
{
  "incident_id": "INC-20260308182000",
  "title": "Database connection pool exhausted due to connection leak",
  "timeline": [...],
  "root_cause": { "type": "...", "description": "...", "evidence": [...] },
  "impact": { "affected_services": [...], "business_impact": "high" },
  "resolution": { "strategy": {...}, "immediate_fix": {...}, "pr_url": "..." },
  "lessons_learned": [...],
  "action_items": [...],
  "generated_at": "2026-03-08T18:25:00Z"
}
```

---

## Orchestration (Microsoft Semantic Kernel)

The `IncidentOrchestrator` (`src/orchestration/orchestrator.py`) registers all four agents as **Semantic Kernel plugins** and coordinates the full pipeline in-process:

- `DiagnosisAgent` → plugin function `diagnose(incident_json)`
- `ResolutionAgent` → plugin function `resolve(diagnosis_json)`
- `CommunicationAgent` → plugin functions `notify(incident_json)`, `post_mortem(incident_json)`

When running via the orchestrator, agents are invoked directly as function calls (no Service Bus). When running as standalone processes, they communicate exclusively through Service Bus queues.

---

## What Is Real vs Simulated

### ✅ Fully Real (requires Azure credentials)
- Azure Service Bus message passing between all 4 agents
- Azure Monitor KQL queries for CPU and Memory metrics
- Azure SQL Database tier scaling (`SqlManagementClient`)
- Azure App Service restart (`WebSiteManagementClient`)
- Azure App Service circuit breaker settings update
- Azure App Service deployment slot swap (rollback)
- GitHub Models AI inference (GPT-4o-mini via `azure-ai-inference` SDK)
- GitHub PR creation with automated fix (via `PyGithub`)
- GitHub Copilot CLI code suggestion (`gh copilot suggest`)
- Azure Service Bus queue connectivity and message persistence

### 🟡 Simulated / Stubbed
- **Incident data in demo mode** — synthetic JSON injected via `scripts/inject_test_incident.py` or `TEST_MODE=true` orchestrator; no real Azure Monitor anomaly required
- **Impact assessment** — `assess_impact()` returns placeholder values (`"estimated_users_affected": 0`, `"business_impact": "high"`)
- **Lessons learned & action items** — hardcoded example strings in the Communication Agent
- **Post-mortem distribution** — logged to console; no real email, Teams, or PagerDuty call is made
- **Incident database** — post-mortems are logged but not written to persistent storage
- **Memory leak fix code** — stub returns empty `changes: []`
- **Backoff retry fix code** — stub returns empty `changes: []`

---

## How to Run

### Quick Demo (recommended — no Azure Monitor needed)
```bash
# Runs all agents in-process, simulates a database spike
python examples/demo-database-spike.py

# Other scenarios
python examples/demo-memory-leak.py
python examples/demo-cpu-spike.py
python examples/demo-api-rate-limit.py
python examples/demo-failed-deployment.py
```

### Test Mode via Orchestrator
```bash
TEST_MODE=true python src/orchestration/orchestrator.py
```

### Standalone Agent Test (no Service Bus needed)
```bash
python src/agents/diagnosis/agent.py --test
```

### Full Distributed Mode (4 terminals — requires Azure Service Bus)

**Terminal 1 — Diagnosis Agent:**
```bash
python src/agents/diagnosis/agent.py
```

**Terminal 2 — Resolution Agent:**
```bash
python src/agents/resolution/agent.py
```

**Terminal 3 — Communication Agent:**
```bash
python src/agents/communication/agent.py
```

**Terminal 4 — Inject a test incident (triggers the whole chain):**
```bash
python scripts/inject_test_incident.py database   # Database connection spike
python scripts/inject_test_incident.py memory     # Memory leak
python scripts/inject_test_incident.py cpu        # CPU spike
python scripts/inject_test_incident.py rate       # API rate limit breach
```

### Production Mode (requires real Azure Monitor data)
```bash
python src/orchestration/orchestrator.py
# The detection loop polls Azure Monitor every DETECTION_AGENT_INTERVAL_SECONDS
# and automatically triggers the full pipeline on real anomalies
```

---

## Environment Variables Required

| Variable | Used By | Required For |
|----------|---------|-------------|
| `AZURE_SERVICEBUS_CONNECTION_STRING` | All agents | Service Bus messaging (distributed mode) |
| `GITHUB_TOKEN` | Diagnosis, Resolution | AI diagnosis (GitHub Models) + PR creation |
| `AZURE_SUBSCRIPTION_ID` | Resolution | Azure resource management (fixes) |
| `AZURE_RESOURCE_GROUP` | Resolution | Azure resource management (fixes) |
| `AZURE_MONITOR_WORKSPACE_ID` | Detection | Real Azure Monitor queries |
| `MONITORED_WEBAPP_ID` | Detection, Resolution | Resource to monitor and remediate |
| `AZURE_SQL_SERVER` | Resolution | Database scaling fix |
| `AZURE_SQL_DATABASE` | Resolution | Database scaling fix |
| `GITHUB_REPO_OWNER` | Resolution | PR creation |
| `GITHUB_REPO_NAME` | Resolution | PR creation |
| `GITHUB_MODEL_NAME` | Diagnosis | AI model selection (default: `gpt-4o-mini`) |

> Copy `.env.example` to `.env` and fill in your values. Never commit `.env` to Git.

---

## Demo Scenarios Available

| Script | Incident Type | Root Cause Detected | Immediate Fix |
|--------|--------------|--------------------|----|
| `demo-database-spike.py` | DB connection pool exhaustion | `database_connection_exhaustion` | Scale SQL tier |
| `demo-memory-leak.py` | Memory usage critical | `memory_leak` | Restart App Service |
| `demo-cpu-spike.py` | CPU utilization > 95% | `cpu_spike` | Restart App Service |
| `demo-api-rate-limit.py` | Third-party API throttling | `api_rate_limit_breach` | Enable circuit breaker |
| `demo-failed-deployment.py` | Deployment error spike | `failed_deployment` | Rollback deployment slot |
| `demo-slow-query.py` | Database query degradation | `slow_database_query` | Scale SQL tier |
| `demo-disk-space.py` | Disk space critical | `disk_space_exhaustion` | Restart App Service |

---

## Key Technologies

| Technology | Role |
|-----------|------|
| **Azure Service Bus** | Async message queue between agents |
| **Azure Monitor / Log Analytics** | Real-time metric queries (KQL) |
| **Azure Management SDK** | Execute fixes on Azure resources |
| **GitHub Models (GPT-4o-mini)** | AI-powered root cause analysis |
| **GitHub Copilot CLI** | Code fix generation |
| **PyGithub** | Automated PR creation |
| **Microsoft Semantic Kernel** | Agent orchestration and plugin system |
| **Python `azure-ai-inference`** | GitHub Models API client |
| **`python-dotenv`** | Environment variable management |
