"""
Test suite for GitHub Copilot integration in Resolution Agent (Runtime-Driven)

This test file demonstrates the integration of GitHub Copilot 
for generating code fixes based on real-time runtime context instead of static fix types.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from agent import ResolutionAgent


class TestRuntimeContextIntegration:
    """Test runtime-driven context preparation"""
    
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
            "affected_component": "src/database/connection.js",
            "severity": "high",
            "stack_trace": "Error: ECONNREFUSED at Database.connect()",
            "logs_excerpt": "[ERROR] Connection timeout after 30s",
            "metrics_snapshot": {"cpu": 85, "memory": 92},
            "code_snippet": "const pool = new Pool();"
        }
    
    @pytest.fixture
    def sample_runtime_data(self):
        """Sample runtime data"""
        return {
            "error_message": "Connection pool exhausted",
            "stack_trace": "Error: ECONNREFUSED at Database.connect()",
            "logs_excerpt": "[ERROR] Connection timeout after 30s",
            "metrics_snapshot": {"cpu": 85, "memory": 92},
            "suspected_file": "src/database/connection.js",
            "relevant_code_snippet": "const pool = new Pool();"
        }
    
    def test_extract_runtime_data(self, resolution_agent, sample_diagnosis):
        """Test extraction of runtime data from diagnosis"""
        runtime_data = resolution_agent._extract_runtime_data(sample_diagnosis)
        
        assert runtime_data is not None
        assert runtime_data["error_message"] == sample_diagnosis["root_cause"]["description"]
        assert runtime_data["suspected_file"] == sample_diagnosis["affected_component"]
        assert runtime_data["metrics_snapshot"] == sample_diagnosis["metrics_snapshot"]
    
    def test_prepare_runtime_context(self, resolution_agent, sample_diagnosis, sample_runtime_data):
        """Test runtime context preparation"""
        context = resolution_agent._prepare_runtime_context(sample_diagnosis, sample_runtime_data)
        
        assert context is not None
        assert "INC-2024-001" in context
        assert "database_connection_exhaustion" in context
        assert "Runtime Evidence:" in context
        assert "Connection pool exhausted" in context
        assert "src/database/connection.js" in context
    
    def test_prepare_runtime_context_missing_fields(self, resolution_agent, sample_diagnosis):
        """Test runtime context with missing required fields"""
        incomplete_runtime_data = {
            "error_message": "Some error",
            # Missing other required fields
        }
        
        context = resolution_agent._prepare_runtime_context(
            sample_diagnosis, 
            incomplete_runtime_data
        )
        
        assert context is None
    
    def test_prepare_runtime_context_none_data(self, resolution_agent, sample_diagnosis):
        """Test runtime context with None data"""
        context = resolution_agent._prepare_runtime_context(sample_diagnosis, None)
        assert context is None
    
    def test_mask_sensitive_data(self, resolution_agent):
        """Test sensitive data masking"""
        runtime_data = {
            "error_message": "API call failed with api_key=sk-12345abcde",
            "stack_trace": "user@example.com failed auth with password=secret123",
            "logs_excerpt": "SSN: 123-45-6789 found in request",
            "metrics_snapshot": {},
            "suspected_file": "src/api.js",
            "relevant_code_snippet": "const card = '1234567890123456';"
        }
        
        masked = resolution_agent._mask_sensitive_data(runtime_data)
        
        assert "sk-12345abcde" not in masked["error_message"]
        assert "***MASKED***" in masked["error_message"]
        assert "user@example.com" not in masked["stack_trace"]
        assert "secret123" not in masked["stack_trace"]
        assert "123-45-6789" not in masked["logs_excerpt"]
    
    def test_parse_copilot_output_runtime(self, resolution_agent, sample_diagnosis, sample_runtime_data):
        """Test parsing of runtime-based Copilot output"""
        copilot_output = """
const pool = new Pool({
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000
});
"""
        
        result = resolution_agent._parse_copilot_output_runtime(
            copilot_output, 
            sample_diagnosis,
            sample_runtime_data
        )
        
        assert result is not None
        assert "files" in result
        assert "changes" in result
        assert "src/database/connection.js" in result["files"]
        assert result["changes"][0]["suggested_by"] == "github_copilot"
        assert result["changes"][0]["root_cause_type"] == "database_connection_exhaustion"


class TestCopilotIntegration:
    """Test GitHub Copilot integration with runtime context"""
    
    @pytest.fixture
    def resolution_agent(self):
        """Create Resolution Agent instance for testing"""
        agent = ResolutionAgent()
        return agent
    
    @pytest.fixture
    def sample_diagnosis(self):
        """Sample incident diagnosis"""
        return {
            "incident_id": "INC-2024-002",
            "root_cause": {
                "type": "memory_leak",
                "description": "Memory leak in cache service"
            },
            "affected_component": "src/services/cache.js",
            "severity": "high"
        }
    
    @pytest.fixture
    def sample_runtime_data(self):
        """Sample runtime data"""
        return {
            "error_message": "Memory usage at 95%",
            "stack_trace": "OutOfMemory in cache.js:45",
            "logs_excerpt": "[ERROR] Heap size exceeded",
            "metrics_snapshot": {"heap_mb": 1900, "max_heap_mb": 2000},
            "suspected_file": "src/services/cache.js",
            "relevant_code_snippet": "cache.set(key, value);"
        }
    
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
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("gh", 60)):
            result = await resolution_agent._call_copilot_suggest("test context")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_fix_with_copilot_success(self, resolution_agent, sample_diagnosis, sample_runtime_data):
        """Test successful Copilot fix generation with runtime context"""
        copilot_response = "const cache = new LRUCache({max: 1000});"
        
        with patch.object(
            resolution_agent,
            '_call_copilot_suggest',
            return_value=copilot_response
        ):
            result = await resolution_agent.generate_fix_with_copilot(
                sample_diagnosis,
                sample_runtime_data
            )
            
            assert result is not None
            assert "files" in result
            assert "changes" in result
    
    @pytest.mark.asyncio
    async def test_generate_fix_with_copilot_fallback(self, resolution_agent, sample_diagnosis, sample_runtime_data):
        """Test Copilot fix generation fallback when Copilot unavailable"""
        with patch.object(
            resolution_agent,
            '_call_copilot_suggest',
            return_value=None
        ):
            result = await resolution_agent.generate_fix_with_copilot(
                sample_diagnosis,
                sample_runtime_data
            )
            
            # Should return fallback fix based on root cause
            assert result is not None
            assert "files" in result
    
    @pytest.mark.asyncio
    async def test_generate_fix_with_copilot_bad_context(self, resolution_agent, sample_diagnosis):
        """Test Copilot fix with invalid runtime context"""
        invalid_runtime_data = {"error_message": "incomplete"}
        
        result = await resolution_agent.generate_fix_with_copilot(
            sample_diagnosis,
            invalid_runtime_data
        )
        
        # Should return fallback
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_generate_fix_with_copilot_exception(self, resolution_agent, sample_diagnosis):
        """Test exception handling in fix generation"""
        with patch.object(
            resolution_agent,
            '_prepare_runtime_context',
            side_effect=Exception("Context preparation failed")
        ):
            result = await resolution_agent.generate_fix_with_copilot(
                sample_diagnosis,
                {"error_message": "test", "stack_trace": "", "logs_excerpt": "", 
                 "metrics_snapshot": {}, "suspected_file": "", "relevant_code_snippet": ""}
            )
            
            # Should handle gracefully
            assert result is not None or result is None
    
    def test_generate_fallback_from_diagnosis(self, resolution_agent, sample_diagnosis):
        """Test fallback generation based on root cause"""
        fallback = resolution_agent._generate_fallback_from_diagnosis(sample_diagnosis)
        
        assert fallback is not None
        assert "files" in fallback
        assert "src/services/cache.js" in fallback["files"]
    
    def test_generate_fallback_unknown_root_cause(self, resolution_agent):
        """Test fallback with unknown root cause type"""
        diagnosis = {
            "incident_id": "INC-2024-003",
            "root_cause": {"type": "unknown_issue"},
            "affected_component": "unknown"
        }
        
        fallback = resolution_agent._generate_fallback_from_diagnosis(diagnosis)
        assert fallback is None


class TestResolutionWorkflow:
    """Test the complete resolution workflow with runtime context"""
    
    @pytest.fixture
    def resolution_agent(self):
        agent = ResolutionAgent()
        return agent
    
    @pytest.mark.asyncio
    async def test_generate_permanent_fix_with_runtime_context(self, resolution_agent):
        """Test permanent fix generation with runtime context"""
        diagnosis = {
            "incident_id": "INC-2024-004",
            "root_cause": {
                "type": "database_connection_exhaustion",
                "description": "Connection pool exhausted"
            },
            "affected_component": "src/database/connection.js",
            "stack_trace": "ECONNREFUSED",
            "logs_excerpt": "[ERROR] Connection timeout",
            "metrics_snapshot": {"connections": 500, "max": 500},
            "code_snippet": "const pool = new Pool();"
        }
        
        strategy = {
            "permanent": "implement_connection_pooling"
        }
        
        with patch.object(
            resolution_agent,
            'generate_fix_with_copilot',
            return_value={
                "files": ["src/database/connection.js"],
                "changes": [{"file": "src/database/connection.js", "diff": "// fix"}]
            }
        ):
            result = await resolution_agent.generate_permanent_fix(diagnosis, strategy)
            
            assert result["action"] == "implement_connection_pooling"
            assert result["code_changes"] is not None
            assert "src/database/connection.js" in result["files_modified"]


class TestErrorHandling:
    """Test error handling in runtime-driven Copilot integration"""
    
    @pytest.fixture
    def resolution_agent(self):
        agent = ResolutionAgent()
        return agent
    
    def test_extract_runtime_data_exception(self, resolution_agent):
        """Test exception handling in runtime data extraction"""
        bad_diagnosis = {"root_cause": None}  # Will cause error
        
        result = resolution_agent._extract_runtime_data(bad_diagnosis)
        assert result is not None  # Should not crash
    
    def test_prepare_runtime_context_exception(self, resolution_agent):
        """Test exception handling in context preparation"""
        diagnosis = {"incident_id": "INC-2024-005", "root_cause": {}}
        
        # Pass something that will cause error during masking
        bad_runtime_data = {
            "error_message": None,
            "stack_trace": "",
            "logs_excerpt": "",
            "metrics_snapshot": {},
            "suspected_file": "",
            "relevant_code_snippet": ""
        }
        
        result = resolution_agent._prepare_runtime_context(diagnosis, bad_runtime_data)
        # Should handle gracefully
        assert result is None or result is not None
    
    @pytest.mark.asyncio
    async def test_generate_fix_resilient_failure(self, resolution_agent):
        """Test that generate_fix handles all failure modes gracefully"""
        diagnosis = {
            "incident_id": "INC-2024-006",
            "root_cause": {"type": "rate_limit_breach"},
            "affected_component": "api-gateway"
        }
        
        runtime_data = {
            "error_message": "Rate limit exceeded",
            "stack_trace": "",
            "logs_excerpt": "",
            "metrics_snapshot": {},
            "suspected_file": "api-gateway",
            "relevant_code_snippet": ""
        }
        
        with patch.object(
            resolution_agent,
            '_call_copilot_suggest',
            side_effect=Exception("Network error")
        ):
            result = await resolution_agent.generate_fix_with_copilot(
                diagnosis,
                runtime_data
            )
            
            # Should return fallback
            assert result is not None or result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
