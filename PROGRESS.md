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
- [x] Removed all Teams/webhook references (code, `.env`, docs)
- [x] Removed broken demo video link from README
- [x] Replaced `YOUR_USERNAME_HERE` with `Shaurya Singh` in README
- [x] Fixed deployment.md GitHub URL to use real repo
- [x] **Wired GitHub Models AI** (`gpt-4o-mini`) into diagnosis agent via `azure-ai-inference`
- [x] **Added Semantic Kernel** — orchestrator wraps all 3 agents as SK plugins
- [x] Dashboard overhauled — scenario-specific logs, live clock, phase pipeline, branding badges
- [x] All changes committed and pushed to GitHub (latest: `a4c4ae3`)
- [x] Architecture diagram linked in README
- [x] Azure App Service deployment configured (`incident-resolver-dashboard`)

### Azure Resources Created
- [x] Azure SQL Database — `incident-demo-db` on `incident-reolver-sql`
- [x] Application Insights — `incident-resolver-insights`
- [x] Azure AI Foundry — `incident-resolver-foundry`

### .env Values Filled In
- [x] `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `AZURE_RESOURCE_GROUP`
- [x] `AZURE_SQL_SERVER=incident-reolver-sql.database.windows.net`
- [x] `AZURE_SQL_DATABASE=incident-demo-db`
- [x] `AZURE_APP_INSIGHTS_KEY` and `AZURE_APP_INSIGHTS_CONNECTION_STRING`
- [x] `FOUNDRY_ENDPOINT` and `FOUNDRY_API_KEY`
- [x] `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY`
- [x] `GITHUB_TOKEN`, `GITHUB_REPO_NAME`, `GITHUB_REPO_OWNER`
- [x] `AZURE_SERVICEBUS_CONNECTION_STRING`

---

## ❌ Not Done Yet

### 1. Test the Full Pipeline
- Run `python examples/demo-database-spike.py` to verify end-to-end flow
- Verify GitHub PR is created automatically

### 2. Record Demo Video
- Required submission item — see TODO.md for full script

### 3. README — Microsoft Learn Profile Link
- Currently set to: `https://learn.microsoft.com/en-us/users/shaurya-singh`
- Verify this is your actual Microsoft Learn profile URL
- If different, update it

### 4. Confirm Dashboard is Live
- App name: `incident-resolver-dashboard` (configured in `dashboard/.azure/config`)
- Run `az webapp show --name incident-resolver-dashboard --resource-group azure-incident-resolver-rg --query defaultHostName` to get the live URL

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
