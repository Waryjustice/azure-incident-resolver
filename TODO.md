# Azure Incident Resolver — What's Left To Do

> Last updated: 2026-02-23 (after dashboard overhaul)
> Current hackathon score estimate: **57/100** (dashboard fixed, AI still stubbed)
> Target score after all fixes: **88+/100**

---

## ✅ COMPLETED THIS SESSION

- Fixed all 6 dashboard bugs (`@apply`, `text-magenta-400`, MTTR `--s`, `$(date)` literal, wrong MTTR averaging, button timeout)
- Added scenario-specific logs for all 11 incident types (was generic "connection pool" for everything)
- Added live clock, Azure/Copilot/MCP branding badges to header
- Added icons + descriptions to all 4 agent cards
- Added phase pipeline indicator (🔍→🧠→🔧→💬→✅) on every incident card
- Resolved incidents now greyed out (opacity-60), active incidents pulse
- Active incident count badge in section heading
- Clear incidents button
- Terminal height increased (h-64 → h-96), clear button moved to header
- Scenarios reorganised into logical groups (Database / Application / Infrastructure)
- `new-feature-bug` added to dropdown (was missing)

---

## 🔴 BLOCKING — Must Fix Before Submission

### 1. Get an AI Model Working (Diagnosis Agent)
**Why:** The entire AI pipeline is broken. `determine_root_cause()`, `analyze_logs()`, `gather_context()`, and `search_past_incidents()` in `src/agents/diagnosis/agent.py` are all hardcoded stubs returning fake data. No real LLM is ever called.

**Options (pick one):**
- **GitHub Models (fastest, free):** Go to [github.com/settings/tokens](https://github.com/settings/tokens) → generate a classic token with `models:read` → use `Phi-4` at endpoint `https://models.github.ai/inference`
- **Azure AI Foundry (best for hackathon score):** Contact hackathon organizers at the Innovation Studio page and ask for an Azure pass — your Azure for Students subscription is region-locked and cannot deploy AI resources in any supported region.

**Once you have a key, tell Copilot:** "Wire up the diagnosis agent with [key]" — it will implement:
- Real LLM call in `determine_root_cause()` with full incident context as prompt
- `analyze_logs()` querying Application Insights via REST
- `search_past_incidents()` using in-memory incident history as simple RAG
- `gather_context()` pulling Azure Monitor data (already available in detection agent)

**File:** `src/agents/diagnosis/agent.py`
**Package needed:** `azure-ai-inference` or `openai`

---

### 2. Commit and Push Everything to GitHub
**Why:** Nothing from the last two sessions has been committed. Judges need to see an active public repo with real commit history.

```bash
cd "C:\Users\shaur\Downloads\azure-incident-resolver"
git add -A
git commit -m "Add real Azure SDK remediation, overhaul dashboard with scenario-specific logs and UI improvements"
git push origin main
```

Or tell Copilot: "commit all changes"

---

### 3. Record a 2-Minute Demo Video
**Why:** **Required submission item.** Cannot submit without it. Upload to YouTube or Vimeo (must be public, no third-party trademarks).

**Script (2 minutes):**
1. `0:00–0:20` — Open dashboard, show live clock, 4 agents with icons, branding badges
2. `0:20–0:45` — Trigger "Database Connection Pool" — show phase pipeline animating 🔍→🧠→🔧→💬→✅
3. `0:45–1:05` — Trigger "New Feature Bug" — highlight Copilot code fix path, no rollback scenario
4. `1:05–1:20` — Show MTTR updating, resolved incident greyed out, active count badge
5. `1:20–1:40` — Show architecture diagram, explain 4-agent flow
6. `1:40–2:00` — Show GitHub PR auto-created, Teams notification received

**Tools:** OBS Studio (free) or Windows Game Bar (`Win + G`). Record at 1920×1080.

---

## 🟡 HIGH PRIORITY — Significantly Affects Score

### 4. Add Microsoft Agent Framework (Semantic Kernel)
**Why:** Hackathon hero technologies are: Microsoft Foundry, Microsoft Agent Framework, Azure MCP, GitHub Copilot Agent Mode. Your agents are plain Python classes — no Microsoft Agent Framework SDK used anywhere. Hurts "Adherence to Hackathon Category" (20% of judging).

**What to do:** Wrap the orchestrator with Semantic Kernel (~50 lines).

```bash
pip install semantic-kernel
```

**File:** `src/orchestration/orchestrator.py`
Tell Copilot: "Wrap the orchestrator with Semantic Kernel so agents are registered as SK plugins"

---

### 5. Deploy Dashboard to Azure App Service
**Why:** Judges want a live URL. Scores higher on "Real-World Impact" and "User Experience". Azure App Service F1 (free tier) works on student subscriptions.

```bash
az webapp up --name incident-resolver-dashboard --runtime PYTHON:3.11 --sku F1
```

Or tell Copilot: "Deploy the dashboard to Azure App Service"

---

### 6. Configure Microsoft Teams Webhook
**Why:** The communication agent has `_send_teams_message()` fully implemented but `TEAMS_WEBHOOK_URL` is not set, so no notifications are actually sent. Judges will want to see this in the demo.

**Steps:**
1. Teams → any channel → Manage Channel → Connectors → Incoming Webhook → Create
2. Copy the webhook URL
3. Add to `.env`: `TEAMS_WEBHOOK_URL=https://your-org.webhook.office.com/...`

---

### 7. Run the Full End-to-End Pipeline
**Why:** Must verify everything works together before recording the demo video.

```bash
pip install -r requirements.txt
TEST_MODE=true python -m src.orchestration.orchestrator
```

Or a specific demo:
```bash
python examples/demo-database-spike.py
```

Expected: Detection → AI Diagnosis → Azure SDK fix → Teams notification → GitHub PR created

---

### 8. Add Missing `.env` Values
The resolution agent needs these to run real Azure SDK fixes:

```
AZURE_WEBAPP_NAME=incident-demo-app-ss2026
AZURE_RESOURCE_GROUP=<your-resource-group-name>
```

Check `az group list` to find the right resource group name.

---

### 9. Verify Your Microsoft Learn Profile URL
**Why:** Required for submission — team member Microsoft Learn usernames must be listed.

Current in README: `https://learn.microsoft.com/en-us/users/shaurya-singh`
Confirm this is your actual profile URL. Update `README.md` if not.

---

## 🟢 POLISH — Improves Score, Not Blocking

### 10. Dashboard: MTTR Format
Show `2m 5s` instead of `125s` for readability.
**File:** `dashboard/templates/index.html` → `updateMetrics()` function
Tell Copilot: "Format MTTR display as minutes and seconds"

### 11. Dashboard: Severity Filter Buttons
Add All / Critical / High / Medium filter buttons above the incidents list.
**File:** `dashboard/templates/index.html`

### 12. Dashboard: Sound Alert on New Incident
Subtle beep when a new incident fires — makes it feel like a real ops tool during demo.
**File:** `dashboard/templates/index.html` → `socket.on('new_incident', ...)` handler

### 13. Dashboard: Export Post-Mortem Button
On resolved incidents, add a "Download Post-Mortem" button that saves the timeline as a `.txt` file.
**File:** `dashboard/templates/index.html` + `dashboard/app.py`

### 14. README: Add Screenshots
Judges see the README before they run the code.
- Screenshot 1: Dashboard at rest (agent cards, metrics)
- Screenshot 2: Active incident with phase pipeline mid-flow
- Screenshot 3: Resolved incident with timeline expanded

### 15. README: Link Architecture Diagram
The SVG exists (`architecture-diagram (3).svg`) but isn't referenced anywhere in `README.md`.
Add: `![Architecture](architecture-diagram%20(3).svg)`

---

## 📋 Submission Checklist

- [ ] AI model working in diagnosis agent
- [ ] All changes committed and pushed to public GitHub repo
- [ ] Demo video uploaded to YouTube/Vimeo (2 min max, public link)
- [ ] Architecture diagram included in submission
- [ ] Project description written (problem, solution, technologies used)
- [ ] Microsoft Learn usernames for all team members listed
- [ ] Live demo URL (if deployed to App Service)

---

## 📊 Score Projection

| Category (20% each)          | Before Session | After Dashboard | After All Fixes |
|------------------------------|----------------|-----------------|-----------------|
| Technological Implementation  | 10/20          | 10/20           | 17/20           |
| Agentic Design & Innovation   | 12/20          | 12/20           | 18/20           |
| Real-World Impact             | 15/20          | 15/20           | 19/20           |
| UX & Presentation             | 12/20          | 15/20 ✅        | 17/20           |
| Adherence to Category         | 5/20           | 5/20            | 17/20           |
| **Total**                     | **54**         | **57**          | **88**          |

---

## 🏆 Prize Categories to Target

| Prize | Value | Chance | Key Requirement |
|---|---|---|---|
| Best Azure Integration | $10,000 | **High** | Real Azure SDK calls ✅, deploy to Azure |
| Best Multi-Agent System | $10,000 | **Medium-High** | Add Semantic Kernel |
| Grand Prize - Agentic DevOps | $20,000 | **Medium** | Full pipeline working end-to-end |
| Best Enterprise Solution | $10,000 | **Medium** | Deploy to Azure + security story |
| Best Use of Microsoft Foundry | $10,000 | **Low-Medium** | Need real Foundry model deployment |

**Best Azure Integration is your most winnable category.** Focus the demo video on the real Azure SDK calls — SQL tier scaling, App Service restart, circuit breaker config update, slot swap rollback.

---

## 🗓 Deadline

**Submission closes: March 15, 2026**
Project review: March 16–22, 2026
Announcements: March 25, 2026
