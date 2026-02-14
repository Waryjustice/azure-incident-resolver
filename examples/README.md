# Demo Scenarios

This directory contains demonstration scripts that showcase the Azure Incident Resolver's multi-agent system in action.

## Available Demos

### Scenario 1: Database Connection Pool Exhaustion
**File:** `demo-database-spike.py`  
**Type:** Python  
**Description:** Simulates a production database reaching 100% connection pool utilization

**What it demonstrates:**
- Detection Agent identifying connection pool anomalies
- Diagnosis Agent pinpointing connection leak in API Gateway
- Resolution Agent scaling database tier immediately
- Resolution Agent generating GitHub PR for permanent fix
- Communication Agent notifying the team

**Run with:**
```bash
python examples/demo-database-spike.py
```

**Expected MTTR:** ~3-4 minutes (vs 45-60 minutes manual)

---

### Scenario 2: Memory Leak in Caching Service
**File:** `demo-memory-leak.py`  
**Type:** Python  
**Description:** Simulates a memory leak in the caching service causing service degradation

**What it demonstrates:**
- Detection Agent identifying abnormal memory usage patterns
- Diagnosis Agent finding memory leak in cache service
- Resolution Agent restarting the service immediately
- Resolution Agent generating GitHub PR with memory leak fix
- Service recovery and metrics normalization

**Run with:**
```bash
python examples/demo-memory-leak.py
```

**Expected MTTR:** ~2-3 minutes (vs 30-45 minutes manual)

**Key Metrics Shown:**
- Memory usage: 95% → 12% (after restart)
- Cache hit rate: 15% → 94% (after restart)
- Response time: 3500ms → 158ms (after restart)

---

### Scenario 3: Third-Party API Rate Limit Breach
**File:** `demo-api-rate-limit.py`  
**Type:** Python  
**Description:** Simulates rate limit errors from third-party API causing cascading failures

**What it demonstrates:**
- Detection Agent identifying rate limit error spike
- Diagnosis Agent pinpointing third-party API throttling
- Resolution Agent activating circuit breaker immediately
- Resolution Agent generating GitHub PR with exponential backoff
- Request queue management and graceful degradation
- Revenue impact and business continuity

**Run with:**
```bash
python examples/demo-api-rate-limit.py
```

**Expected MTTR:** ~8-10 minutes (vs 45-90 minutes manual)

**Key Metrics Shown:**
- Rate limit errors: 547 errors in 5 minutes
- API error rate: 42% (baseline: 0.1%)
- Transaction latency: 28,000ms (baseline: 800ms)
- Failed transactions: 342 in 5 minutes
- Queue depth: 12,500 pending requests
- Revenue impact: ~$5,000-40,000 per incident

---

## Scenario Comparison

| Aspect | Scenario 1 | Scenario 2 | Scenario 3 |
|--------|-----------|-----------|-----------|
| **Issue Type** | DB Exhaustion | Memory Leak | API Rate Limit |
| **Metric Focus** | Connection pool | Memory usage | Error rate |
| **Immediate Action** | Database scaling | Service restart | Circuit breaker |
| **Permanent Fix** | Connection pooling | Memory cleanup | Backoff/retry logic |
| **Services Affected** | 3 | 4 | 4 |
| **Revenue Impact** | High | Medium | Critical |
| **Typical MTTR** | 45-60 min | 30-45 min | 45-90 min |
| **Automated MTTR** | 3-4 min | 2-3 min | 8-10 min |

---

## How to Run

### Prerequisites
1. Python 3.8+
2. Azure SDK configured
3. GitHub token set up (for PR creation)
4. Orchestrator module available

### Basic Execution
```bash
# Database spike scenario
python examples/demo-database-spike.py

# Memory leak scenario
python examples/demo-memory-leak.py

# API rate limit scenario
python examples/demo-api-rate-limit.py
```

# Memory leak scenario
python examples/demo-memory-leak.py
```

### With Environment Variables
```bash
export GITHUB_TOKEN="your_token"
export GITHUB_REPO_OWNER="your_org"
export GITHUB_REPO_NAME="your_repo"

python examples/demo-memory-leak.py
```

---

## What Happens in Each Demo

### Initial Phase
1. Demo scenario is created with realistic incident data
2. Anomalies are populated with exceeding thresholds
3. User prompted to start the simulation

### Detection Phase
- System detects anomalies from metrics
- Incident severity calculated
- Impact estimate generated

### Diagnosis Phase
- Root cause analysis performed
- Affected services identified
- Recommendations generated

### Resolution Phase
- Immediate automated action taken
- Service restored to normal operation
- GitHub PR created with permanent fix

### Communication Phase
- Team notifications sent
- Post-mortem generated
- Incident documented

---

## Customizing Demos

### Modify Incident Data
Edit the `incident` dictionary in the demo file to change:
- Resource names and types
- Metric values and baselines
- Anomaly thresholds
- Impact estimates

### Change Severity Levels
Adjust the `severity` field:
- `low` - Non-critical
- `medium` - Important
- `high` - Urgent
- `critical` - Immediate action required

### Add Custom Anomalies
Add entries to the `anomalies` list with:
- `metric` - Name of metric
- `value` - Current value
- `baseline` - Normal value
- `threshold` - Alert threshold
- `severity` - How critical
- `description` - Human-readable explanation

---

## Demo Output

Each demo will show:

### Incident Creation
```
🚨 Incident Created!
   ID: INC-20260214111300
   Service: Production Caching Service
   Severity: CRITICAL
   Anomalies Detected: 5
   Estimated Users Affected: ~8000
```

### Key Metrics
```
📊 Key Metrics:
   • Memory Usage: 95% (baseline: 40%)
   • Memory Growth: 2.5 MB/sec
   • Response Time: 3500ms (baseline: 150ms)
   • Cache Miss Ratio: 85% (baseline: 5%)
   • OOM Events: 3 in last 5 minutes
```

### Workflow Progress
```
[Detection Agent] ✓ Incident detected
[Diagnosis Agent] ✓ Root cause identified
[Resolution Agent] ✓ Immediate fix applied
[Resolution Agent] ✓ GitHub PR created
[Communication Agent] ✓ Team notified
```

### Completion Summary
```
What just happened:
✓ Incident detected and categorized automatically
✓ Root cause identified (memory leak in cache service)
✓ Cache service restarted immediately
✓ Memory cleared, service returned to normal
✓ GitHub PR created with memory leak fix
✓ Team notified of incident and resolution
```

---

## Troubleshooting

### Demo hangs after starting
- Check if waiting for user input (press ENTER)
- Verify GitHub token is valid if PR creation is enabled

### Metrics seem unrealistic
- Edit the `incident` dictionary to use different values
- Increase/decrease severity to see different responses

### Missing orchestrator module
- Ensure orchestration module is properly implemented
- Check Python path includes project root

### GitHub PR not created
- Verify `GITHUB_TOKEN` environment variable is set
- Check repository permissions
- Ensure `GITHUB_REPO_OWNER` and `GITHUB_REPO_NAME` are configured

---

## Creating New Scenarios

To create a new scenario:

1. Copy an existing demo file
2. Update scenario name and description
3. Create custom incident data with appropriate metrics
4. Define expected agent actions
5. Set realistic baseline and threshold values
6. Add custom anomalies relevant to the scenario

Example scenario candidates:
- Rate limit violations
- Deployment failures
- API latency spikes
- Disk space exhaustion
- Authentication service failures

---

## Integration Testing

Use these demos for:
- **End-to-end testing** - Verify full workflow
- **Agent validation** - Test each agent's capability
- **Performance testing** - Measure response times
- **Integration testing** - Verify inter-agent communication
- **Demo purposes** - Show capabilities to stakeholders

---

## Next Steps

After running the demos:
1. Review the generated GitHub PRs
2. Check the incident logs
3. Examine the post-mortem documents
4. Analyze the MTTR improvements
5. Customize scenarios for your environment
