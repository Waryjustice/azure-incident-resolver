# Azure Incident Resolver — What's Left To Do

> Last updated: 2026-03-03 (verified against actual codebase)
> Current hackathon score estimate: **78/100**
> Target score after remaining fixes: **90+/100**

---

## ✅ COMPLETED (verified in code)

- Fixed all dashboard bugs — live clock, branding badges, phase pipeline, scenario-specific logs
- **AI model wired up** — GitHub Models `gpt-4o-mini` via `azure-ai-inference` in `src/agents/diagnosis/agent.py`; falls back to rule-based if token missing
- **Semantic Kernel** — orchestrator wraps all 3 agents as SK plugins (`DiagnosisAgent`, `ResolutionAgent`, `CommunicationAgent`)
- **Real Azure SDK remediation** — SQL tier scaling, App Service restart, circuit breaker config update, slot swap rollback (all 4 functions real)
- **All changes committed and pushed** — 10 commits on `main`, latest: `a4c4ae3`
- **Architecture diagram linked** in `README.md`
- **Teams webhook fully removed** from code, `.env`, and docs
- `AZURE_RESOURCE_GROUP=azure-incident-resolver-rg` set in `.env`
- `AZURE_WEBAPP_NAME` derived from `MONITORED_WEBAPP_ID` in resolution agent (no separate var needed)
- Azure App Service deployment configured (`dashboard/.azure/config` → `incident-resolver-dashboard`)

---

## 🔴 BLOCKING — Must Do Before Submission

### 1. Record a 2-Minute Demo Video
**Required submission item — cannot submit without it.** Upload to YouTube or Vimeo (public, no third-party trademarks).

**Script (2 minutes):**
1. `0:00–0:20` — Open dashboard, show live clock, 4 agents with icons, branding badges
2. `0:20–0:45` — Trigger "Database Connection Pool" — show phase pipeline 🔍→🧠→🔧→💬→✅
3. `0:45–1:05` — Trigger "New Feature Bug" — highlight Copilot code fix path
4. `1:05–1:20` — Show MTTR updating, resolved incident greyed out, active count badge
5. `1:20–1:40` — Show architecture diagram, explain 4-agent flow
6. `1:40–2:00` — Show GitHub PR auto-created

**Tools:** OBS Studio (free) or Windows Game Bar (`Win + G`). Record at 1920×1080.

---

### 2. Run the Full End-to-End Pipeline Test
**Must verify everything works together before recording the demo video.**

```bash
pip install -r requirements.txt
TEST_MODE=true python -m src.orchestration.orchestrator
```

Or a specific demo:
```bash
python examples/demo-database-spike.py
```

Expected: Detection → AI Diagnosis → Azure SDK fix → GitHub PR created

---

### 3. Verify Microsoft Learn Profile URL
Required for submission — must be listed for all team members.

Current in README: `https://learn.microsoft.com/en-us/users/shaurya-singh`
Confirm this is your actual profile URL. Update `README.md` if not.

---

## 🟡 HIGH PRIORITY — Significantly Affects Score

### 4. Verify Dashboard is Live on Azure App Service
The deployment config exists (`dashboard/.azure/config` → app name: `incident-resolver-dashboard`), but confirm it's actually accessible:

```bash
az webapp show --name incident-resolver-dashboard --resource-group azure-incident-resolver-rg --query "defaultHostName"
```

If not yet deployed:
```bash
cd dashboard
az webapp up --name incident-resolver-dashboard --runtime PYTHON:3.11 --sku F1
```

---

## 🟢 POLISH — Improves Score, Not Blocking

### 5. Dashboard: MTTR Format
Show `2m 5s` instead of `125s` for readability.
**File:** `dashboard/templates/index.html` → `updateMetrics()` function

### 6. Dashboard: Severity Filter Buttons
Add All / Critical / High / Medium filter buttons above the incidents list.
**File:** `dashboard/templates/index.html`

### 7. Dashboard: Sound Alert on New Incident
Subtle beep when a new incident fires.
**File:** `dashboard/templates/index.html` → `socket.on('new_incident', ...)` handler

### 8. Dashboard: Export Post-Mortem Button
On resolved incidents, add a "Download Post-Mortem" button that saves the timeline as a `.txt` file.
**File:** `dashboard/templates/index.html` + `dashboard/app.py`

### 9. README: Add Screenshots
- Screenshot 1: Dashboard at rest (agent cards, metrics)
- Screenshot 2: Active incident with phase pipeline mid-flow
- Screenshot 3: Resolved incident with timeline expanded

---

## 📋 Submission Checklist

- [x] AI model working in diagnosis agent
- [x] All changes committed and pushed to public GitHub repo
- [x] Semantic Kernel wrapping all agents
- [x] Real Azure SDK remediation (SQL, App Service, circuit breaker, rollback)
- [x] Architecture diagram in README
- [ ] Demo video uploaded to YouTube/Vimeo (2 min max, public link)
- [ ] End-to-end pipeline verified working
- [ ] Live demo URL confirmed accessible
- [ ] Microsoft Learn username verified
- [ ] Project description written (problem, solution, technologies used)

---

## 📊 Score Projection

| Category (20% each)          | Current | After Remaining |
|------------------------------|---------|-----------------|
| Technological Implementation  | 16/20   | 17/20           |
| Agentic Design & Innovation   | 17/20   | 18/20           |
| Real-World Impact             | 16/20   | 19/20           |
| UX & Presentation             | 15/20   | 17/20           |
| Adherence to Category         | 14/20   | 19/20           |
| **Total**                     | **78**  | **90**          |

---

## 🏆 Prize Categories to Target

| Prize | Value | Chance | Key Requirement |
|---|---|---|---|
| Best Azure Integration | $10,000 | **High** | Real Azure SDK calls ✅, live deployment |
| Best Multi-Agent System | $10,000 | **High** | Semantic Kernel ✅, 4-agent pipeline ✅ |
| Grand Prize - Agentic DevOps | $20,000 | **Medium** | Full pipeline verified end-to-end |
| Best Enterprise Solution | $10,000 | **Medium** | Live URL + security story |
| Best Use of Microsoft Foundry | $10,000 | **Low-Medium** | Azure AI Foundry endpoint configured ✅ |

**Best Azure Integration and Best Multi-Agent System are your most winnable categories.**

---

## 🗓 Deadline

**Submission closes: March 15, 2026**
Project review: March 16–22, 2026
Announcements: March 25, 2026
