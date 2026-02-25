# Azure Incident Resolver — Session Progress

## ✅ Completed

### Code Changes
- [x] Replaced all 4 fake remediation functions with real Azure SDK calls
  - `_scale_database()` → real Azure SQL scaling via `azure-mgmt-sql`
  - `_restart_service()` → real App Service restart via `azure-mgmt-web`
  - `_enable_circuit_breaker()` → real App Service settings update via `azure-mgmt-web`
  - `_rollback_deployment()` → real slot swap or restart via `azure-mgmt-web`
- [x] Added `azure-mgmt-sql==3.0.1` and `azure-mgmt-web==7.2.0` to `requirements.txt`
- [x] Added Azure credential + resource config to `__init__` (DefaultAzureCredential)
- [x] Removed all Slack references (webhook URL, bot token, docs, code)
- [x] Removed broken demo video link from README
- [x] Replaced `YOUR_USERNAME_HERE` with `Shaurya Singh` in README
- [x] Fixed deployment.md GitHub URL to use real repo
- [x] Removed CLEANUP_WEBHOOK_FILES.txt from repo

### Azure Resources Created
- [x] Azure SQL Database — `incident-demo-db` on `incident-reolver-sql`
- [x] Application Insights — `incident-resolver-insights`
- [x] Azure AI Foundry — `incident-resolver-foundry`

### .env Values Filled In
- [x] `AZURE_SQL_SERVER=incident-reolver-sql.database.windows.net`
- [x] `AZURE_SQL_DATABASE=incident-demo-db`
- [x] `AZURE_APP_INSIGHTS_KEY=1d3c7b6f-c1a5-4369-a5f0-7c57d72313ca`
- [x] `AZURE_APP_INSIGHTS_CONNECTION_STRING=...` (full connection string added)
- [x] `FOUNDRY_ENDPOINT=https://incident-resolver-foundry.services.ai.azure.com/`
- [x] `FOUNDRY_API_KEY=[REDACTED]`
- [x] `AZURE_OPENAI_ENDPOINT=https://incident-resolver-foundry.openai.azure.com/`
- [x] `AZURE_OPENAI_API_KEY=[REDACTED]`

---

## ❌ Not Done Yet

### 1. GPT Model Deployment (BLOCKING — needed for AI diagnosis to work)
- Azure for Students subscription is region-locked to Southeast Asia
- Azure OpenAI model deployment is NOT available in Southeast Asia
- Sweden Central and East US 2 are available but blocked by student subscription policy
- **Solution: Use Groq (free alternative)**
  1. Go to https://console.groq.com
  2. Sign up with Google or GitHub
  3. Click "API Keys" → "Create API Key" → name it `incident-resolver`
  4. Copy the key (starts with `gsk_...`)
  5. Tell Copilot the key — it will update the code to use Groq instead of Azure OpenAI
  6. Model to use: `llama-3.3-70b-versatile` (free, comparable to GPT-4o-mini)

### 2. Commit All Changes to GitHub
- All the changes from this session have NOT been committed yet
- Run this when ready:
  ```
  cd "C:\Users\shaur\Downloads\azure-incident-resolver"
  git add -A
  git commit -m "Configure all Azure resources and real SDK remediation"
  git push origin main
  ```
- Or just tell Copilot "commit all changes" in the next session

### 3. README — Microsoft Learn Profile Link
- Currently set to: `https://learn.microsoft.com/en-us/users/shaurya-singh`
- Verify this is your actual Microsoft Learn profile URL
- If different, update it

### 4. Deploy a GPT Model (after Groq setup)
- Once Groq key is obtained, Copilot will:
  - Update `src/agents/diagnosis/agent.py` to use Groq API
  - Add `groq` package to `requirements.txt`
  - Add `GROQ_API_KEY` to `.env`

### 5. Test the Full Pipeline
- Run `python examples/demo-database-spike.py` to verify end-to-end flow
- Check Teams notification is received
- Verify GitHub PR is created automatically

---

## 📋 Azure Resources Summary

| Resource | Name | Status |
|---|---|---|
| App Service | `incident-demo-app-ss2026` | ✅ Existing |
| SQL Database | `incident-demo-db` | ✅ Created today |
| SQL Server | `incident-reolver-sql` | ✅ Created today (note typo: "reolver") |
| Log Analytics | `incident-resolver-logs` | ✅ Existing |
| Service Bus | `incident-resolver-mcp` | ✅ Existing |
| App Insights | `incident-resolver-insights` | ✅ Created today |
| AI Foundry | `incident-resolver-foundry` | ✅ Created today |
| GPT Model | `gpt-4` deployment | ❌ Not deployed (region issue) |

---

## ⚠️ Notes
- SQL server has a typo in the name: `incident-reolver-sql` (missing 's' in resolver)
  - This is fine — doesn't affect functionality, just cosmetic
- `.env` file has real credentials — do NOT commit it to GitHub (already in .gitignore)
- All code changes are saved locally but not yet pushed to GitHub
