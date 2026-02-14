"""
Test suite for GitHub Copilot integration in Resolution Agent

This test file demonstrates the integration of GitHub Copilot 
for generating code fixes based on incident diagnosis.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from agent import ResolutionAgent


class TestCopilotIntegration:
    """Test GitHub Copilot integration methods"""
    
    @pytest.fixture
    def resolution_agent(self):
        """Create Resolution Agent instance for testing"""
        agent = ResolutionAgent()
        return agent
    
    @pytest.fixture
    def sample_diagnosis(self):
        """Sample incident diagnosis"""
        return {
            "incident_id": "INC-2024-001",
            "root_cause": {
                "type": "database_connection_exhaustion",
                "description": "Database connection pool exhausted due to slow queries"
            },
            "affected_component": "user-service",
            "severity": "high"
        }
    
    def test_prepare_copilot_context(self, resolution_agent, sample_diagnosis):
        """Test context preparation for Copilot"""
        context = resolution_agent._prepare_copilot_context(
            sample_diagnosis, 
            "connection_pooling"
        )
        
        assert "INC-2024-001" in context
        assert "database_connection_exhaustion" in context
        assert "connection_pooling" in context
        assert "error handling" in context
    
    def test_get_files_for_fix_type(self, resolution_agent):
        """Test file mapping for different fix types"""
        # Test connection pooling
        files = resolution_agent._get_files_for_fix_type("connection_pooling")
        assert "src/database/connection.js" in files
        assert "src/database/pool.js" in files
        
        # Test memory leak
        files = resolution_agent._get_files_for_fix_type("memory_leak")
        assert "src/services/cache.js" in files
        assert "src/memory/manager.js" in files
        
        # Test backoff retry
        files = resolution_agent._get_files_for_fix_type("backoff_retry")
        assert "src/services/api-client.js" in files
        assert "src/utils/retry.js" in files
        
        # Test unknown type
        files = resolution_agent._get_files_for_fix_type("unknown")
        assert files == ["src/fix.js"]
    
    def test_parse_copilot_output(self, resolution_agent, sample_diagnosis):
        """Test parsing of Copilot-generated code"""
        copilot_output = """
const pool = new Pool({
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000
});
"""
        
        result = resolution_agent._parse_copilot_output(
            copilot_output, 
            "connection_pooling",
            sample_diagnosis
        )
        
        assert "files" in result
        assert "changes" in result
        assert len(result["changes"]) == 1
        assert result["changes"][0]["suggested_by"] == "github_copilot"
        assert result["changes"][0]["fix_type"] == "connection_pooling"
        assert copilot_output.strip() in result["changes"][0]["diff"]
    
    def test_generate_fallback_fix_connection_pooling(self, resolution_agent, sample_diagnosis):
        """Test fallback fix generation for connection pooling"""
        fallback = resolution_agent._generate_fallback_fix(
            "connection_pooling", 
            sample_diagnosis
        )
        
        assert fallback is not None
        assert "files" in fallback
        assert "src/database/connection.js" in fallback["files"]
        assert "changes" in fallback
    
    def test_generate_fallback_fix_memory_leak(self, resolution_agent, sample_diagnosis):
        """Test fallback fix generation for memory leak"""
        fallback = resolution_agent._generate_fallback_fix(
            "memory_leak", 
            sample_diagnosis
        )
        
        assert fallback is not None
        assert "files" in fallback
        assert "src/services/cache.js" in fallback["files"]
    
    def test_generate_fallback_fix_unknown_type(self, resolution_agent, sample_diagnosis):
        """Test fallback fix generation for unknown type"""
        fallback = resolution_agent._generate_fallback_fix(
            "unknown_type", 
            sample_diagnosis
        )
        
        assert fallback is None
    
    @pytest.mark.asyncio
    async def test_call_copilot_suggest_no_gh_command(self, resolution_agent):
        """Test handling when gh command is not available"""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = await resolution_agent._call_copilot_suggest("test context")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_call_copilot_suggest_timeout(self, resolution_agent):
        """Test handling of subprocess timeout"""
        import subprocess
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("gh", 30)):
            result = await resolution_agent._call_copilot_suggest("test context")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_fix_with_copilot_fallback(self, resolution_agent, sample_diagnosis):
        """Test Copilot fix generation with fallback"""
        with patch.object(
            resolution_agent, 
            '_call_copilot_suggest', 
            return_value=None
        ):
            result = await resolution_agent.generate_fix_with_copilot(
                sample_diagnosis, 
                "connection_pooling"
            )
            
            assert result is not None
            assert "files" in result
    
    def test_generate_pr_description(self, resolution_agent, sample_diagnosis):
        """Test PR description generation"""
        permanent_fix = {
            "action": "implement_connection_pooling",
            "code_changes": {
                "files": ["src/database/connection.js"],
                "changes": [
                    {
                        "file": "src/database/connection.js",
                        "diff": "const pool = new Pool();"
                    }
                ]
            }
        }
        
        description = resolution_agent._generate_pr_description(
            sample_diagnosis, 
            permanent_fix
        )
        
        assert "INC-2024-001" in description
        assert "database_connection_exhaustion" in description
        assert "Database connection pool exhausted" in description
        assert "GitHub Copilot" in description
        assert "Automated Incident Resolution" in description


class TestResolutionWorkflow:
    """Test the complete resolution workflow with Copilot"""
    
    @pytest.fixture
    def resolution_agent(self):
        agent = ResolutionAgent()
        return agent
    
    @pytest.mark.asyncio
    async def test_generate_permanent_fix_with_copilot(self, resolution_agent):
        """Test permanent fix generation with mocked Copilot"""
        diagnosis = {
            "incident_id": "INC-2024-002",
            "root_cause": {
                "type": "memory_leak",
                "description": "Memory leak in cache service"
            },
            "affected_component": "cache-service"
        }
        
        strategy = {
            "permanent": "fix_memory_leak_code"
        }
        
        with patch.object(
            resolution_agent,
            'generate_fix_with_copilot',
            return_value={
                "files": ["src/services/cache.js"],
                "changes": [
                    {
                        "file": "src/services/cache.js",
                        "diff": "// Fixed memory leak"
                    }
                ]
            }
        ):
            result = await resolution_agent.generate_permanent_fix(diagnosis, strategy)
            
            assert result["action"] == "fix_memory_leak_code"
            assert result["code_changes"] is not None
            assert "src/services/cache.js" in result["files_modified"]


class TestErrorHandling:
    """Test error handling in Copilot integration"""
    
    @pytest.fixture
    def resolution_agent(self):
        agent = ResolutionAgent()
        return agent
    
    @pytest.mark.asyncio
    async def test_generate_fix_with_copilot_exception(self, resolution_agent):
        """Test exception handling in fix generation"""
        diagnosis = {
            "incident_id": "INC-2024-003",
            "root_cause": {"type": "unknown"},
            "affected_component": "unknown"
        }
        
        with patch.object(
            resolution_agent,
            '_prepare_copilot_context',
            side_effect=Exception("Context preparation failed")
        ):
            result = await resolution_agent.generate_fix_with_copilot(
                diagnosis, 
                "backoff_retry"
            )
            
            # Should return None (fallback for unknown type)
            assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
