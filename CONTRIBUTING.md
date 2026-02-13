# Contributing to Azure Incident Resolver

Thank you for your interest in contributing to Azure Incident Resolver! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/azure-incident-resolver.git`
3. Install dependencies: `npm install` or `pip install -r requirements.txt`
4. Create a branch: `git checkout -b feature/your-feature-name`

## Code Standards

### Python Code
- Follow PEP 8 style guide
- Use type hints where possible
- Write docstrings for all functions and classes
- Maximum line length: 100 characters

```python
def diagnose_incident(self, incident: dict) -> Optional[dict]:
    """
    Diagnose an incident and determine root cause.
    
    Args:
        incident: Dictionary containing incident details
        
    Returns:
        Dictionary with diagnosis results or None if diagnosis fails
    """
    pass
```

### JavaScript Code
- Use ES6+ syntax
- Follow Airbnb style guide
- Use async/await instead of callbacks
- Add JSDoc comments for functions

```javascript
/**
 * Detect anomalies in resource metrics
 * @param {Object} resource - Resource to analyze
 * @returns {Promise<Array>} Array of detected anomalies
 */
async function detectAnomalies(resource) {
  // Implementation
}
```

## Testing

### Unit Tests
Write unit tests for all new functionality:

```python
# tests/test_diagnosis_agent.py
import pytest
from agents.diagnosis.agent import DiagnosisAgent

def test_diagnose_incident():
    agent = DiagnosisAgent()
    incident = {"id": "INC-123", "anomalies": [...]}
    diagnosis = await agent.diagnose_incident(incident)
    assert diagnosis is not None
    assert "root_cause" in diagnosis
```

Run tests:
```bash
npm test
# or
pytest
```

### Integration Tests
Test agent interactions:

```python
# tests/integration/test_workflow.py
async def test_full_incident_workflow():
    orchestrator = IncidentOrchestrator()
    incident = create_test_incident()
    result = await orchestrator.handle_incident(incident)
    assert result["status"] == "resolved"
```

## Agent Development Guidelines

### Adding a New Agent

1. Create agent directory: `src/agents/your-agent/`
2. Implement agent class with standard interface:

```python
class YourAgent:
    def __init__(self):
        # Initialize agent
        pass
    
    async def process(self, input_data):
        # Main agent logic
        pass
```

3. Add agent to orchestrator
4. Write tests
5. Update documentation

### Agent Communication

Use Azure MCP for inter-agent communication:

```python
# Send message to next agent
await self.send_via_mcp(
    target_agent="diagnosis",
    message_type="incident_detected",
    data=incident
)
```

## Documentation

### Code Documentation
- Add docstrings to all public functions and classes
- Include examples in docstrings when helpful
- Update README.md if adding new features

### Architecture Documentation
Update `docs/architecture.md` when:
- Adding new agents
- Changing data flow
- Integrating new services

## Commit Guidelines

### Commit Messages
Follow conventional commits:

```
feat: add memory leak detection to diagnosis agent
fix: resolve connection timeout in resolution agent
docs: update deployment guide with AKS instructions
test: add integration tests for communication agent
```

### Pull Requests

1. Update documentation
2. Add/update tests
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Reference related issues

PR template:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] No new warnings
```

## Hackathon-Specific Notes

### Fast Iteration
During the hackathon, it's okay to:
- Skip some tests for rapid prototyping
- Use TODO comments for future improvements
- Prioritize demo-ready features

### But Always:
- Keep code readable
- Comment complex logic
- Update README with new features
- Ensure demo scenarios work

## Getting Help

- Check existing issues and documentation
- Ask in the team's Microsoft Teams channel
- Tag @team-lead in your PR for review

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Hackathon Submission Checklist

Before final submission:
- [ ] All demo scenarios work
- [ ] README is complete
- [ ] Architecture diagram is current
- [ ] Demo video is recorded
- [ ] Code is well-commented
- [ ] GitHub repository is public
- [ ] All team members listed in README

Thank you for contributing to Azure Incident Resolver! 🚀
