# GitHub Copilot Integration - Quick Start Guide

## Setup

### 1. Install GitHub CLI
```bash
# macOS
brew install gh

# Windows (Chocolatey)
choco install gh

# Linux (Ubuntu/Debian)
sudo apt-get install gh
```

### 2. Install Copilot Extension
```bash
gh extension install github/gh-copilot
```

### 3. Authenticate with GitHub
```bash
gh auth login
```

### 4. Set Environment Variables
```bash
export GITHUB_TOKEN="your_personal_access_token"
export GITHUB_REPO_OWNER="your_org"
export GITHUB_REPO_NAME="your_repo"
```

## How It Works

### Flow
1. **Incident Detected** → Diagnosis Agent analyzes the problem
2. **Resolution Agent Receives** → Diagnosis data passed to Resolution Agent
3. **Strategy Determined** → Agent decides immediate + permanent fixes
4. **Immediate Fix Applied** → Database scaling, service restart, etc.
5. **Copilot Generates Fix** → `gh copilot suggest` generates code
6. **PR Created** → GitHub PR with generated code and full incident context
7. **Resolution Complete** → Results sent to Communication Agent

### Example

```python
import asyncio
from src.agents.resolution.agent import ResolutionAgent

async def main():
    agent = ResolutionAgent()
    
    diagnosis = {
        "incident_id": "INC-2024-001",
        "root_cause": {
            "type": "database_connection_exhaustion",
            "description": "Connection pool exhausted by slow queries"
        },
        "affected_component": "user-service",
        "severity": "high"
    }
    
    # Resolve incident with Copilot-generated fix
    resolution = await agent.resolve_incident(diagnosis)
    
    print(f"Status: {resolution['status']}")
    print(f"PR: {resolution['pr_url']}")

asyncio.run(main())
```

## Supported Fix Types

### 1. Connection Pooling
**When**: Database connection exhaustion  
**What**: Generates connection pool configuration  
**Files**: `src/database/connection.js`, `src/database/pool.js`

### 2. Memory Leak
**When**: Memory leak detected  
**What**: Generates memory cleanup code  
**Files**: `src/services/cache.js`, `src/memory/manager.js`

### 3. Backoff Retry
**When**: Rate limit or timeout issues  
**What**: Generates retry logic with exponential backoff  
**Files**: `src/services/api-client.js`, `src/utils/retry.js`

## API Methods

### Main Method
```python
await agent.resolve_incident(diagnosis)
```
Resolves an incident with immediate fixes + Copilot-generated permanent fix

### Copilot Integration
```python
await agent.generate_fix_with_copilot(diagnosis, fix_type)
```
Generates code fix using GitHub Copilot for the given fix type

### PR Creation
```python
await agent.create_fix_pr(diagnosis, permanent_fix)
```
Creates a GitHub PR with the generated fix code

## Troubleshooting

### Issue: `gh: command not found`
**Solution**: Install GitHub CLI
```bash
brew install gh  # macOS
```

### Issue: Copilot suggest times out
**Solution**: Increase timeout in `_call_copilot_suggest` method (default: 30s)

### Issue: PR creation fails
**Solution**: 
- Verify GITHUB_TOKEN has repo permissions
- Check GITHUB_REPO_OWNER and GITHUB_REPO_NAME are correct
- Ensure gh auth is configured: `gh auth login`

### Issue: No code generated
**Solution**:
- Verify GitHub Copilot extension: `gh extension list`
- Check GitHub CLI auth: `gh auth status`
- Try manually: `gh copilot suggest "test prompt"`

## Log Output Examples

### Successful Flow
```
[Resolution Agent] [INFO] Starting resolution for INC-2024-001
[Resolution Agent] Strategy: {'immediate': 'scale_database_tier', ...}
[Resolution Agent] Scaling database tier...
[Resolution Agent] Requesting fix from GitHub Copilot for connection_pooling...
[Resolution Agent] Successfully generated fix with GitHub Copilot
[Resolution Agent] Creating GitHub PR with Copilot-suggested fix...
[Resolution Agent] [SUCCESS] PR created: https://github.com/owner/repo/pull/123
[Resolution Agent] [SUCCESS] Resolution complete
```

### With Fallback
```
[Resolution Agent] Requesting fix from GitHub Copilot for memory_leak...
[Resolution Agent] ⚠️  'gh' command not found. Ensure GitHub CLI is installed.
[Resolution Agent] Copilot suggest returned no output, using fallback
[Resolution Agent] Successfully generated fix with GitHub Copilot
```

## Configuration

### Customize File Mapping
Edit `_get_files_for_fix_type()` method:
```python
def _get_files_for_fix_type(self, fix_type):
    file_mapping = {
        "your_fix_type": ["target/file1.js", "target/file2.js"],
    }
    return file_mapping.get(fix_type, ["src/fix.js"])
```

### Customize Copilot Context
Edit `_prepare_copilot_context()` method to add more context.

### Adjust Timeout
In `_call_copilot_suggest()` method, change `timeout=30` parameter.

## Security

⚠️ **Important**:
- Never commit GITHUB_TOKEN to version control
- Use `.env` file with `.gitignore` entry
- Use environment variables or secrets management
- Review auto-generated PRs before merging

## Performance Notes

- GitHub Copilot suggest: ~5-15 seconds
- PR creation: ~1-2 seconds
- Total end-to-end: ~15-30 seconds (including immediate fixes)

## Next Steps

1. ✅ Integration complete
2. ⬜ Test with sample incidents
3. ⬜ Configure monitoring
4. ⬜ Train team on PR review
5. ⬜ Monitor fix quality metrics

## Documentation

- Full integration guide: `docs/COPILOT_INTEGRATION.md`
- Implementation details: `.copilot/session-state/.../IMPLEMENTATION_SUMMARY.md`
- Test suite: `src/agents/resolution/test_copilot_integration.py`
