"""
Resolution Agent - Executes automated fixes and generates code solutions

This agent:
- Receives diagnosis from Diagnosis Agent
- Determines appropriate resolution strategy
- Executes automated fixes (scaling, restarts, config changes)
- Uses GitHub Copilot Agent Mode to generate code fixes based on runtime context
- Creates PRs for permanent solutions
"""

import os
import json
import re
from datetime import datetime
import asyncio
import subprocess
import tempfile
from github import Github
from azure.identity import DefaultAzureCredential
from azure.servicebus.aio import ServiceBusClient as AsyncServiceBusClient
from azure.servicebus import ServiceBusMessage


class ResolutionAgent:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_client = Github(self.github_token) if self.github_token else None
        self.repo_owner = os.getenv("GITHUB_REPO_OWNER")
        self.repo_name = os.getenv("GITHUB_REPO_NAME")
        self.auto_approve = os.getenv("RESOLUTION_AUTO_APPROVE", "false").lower() == "true"

        # Azure credentials and resource configuration
        self.credential = DefaultAzureCredential()
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP")
        # Parse webapp name from MONITORED_WEBAPP_ID (last path segment) or explicit env var
        monitored_id = os.getenv("MONITORED_WEBAPP_ID", "")
        self.webapp_name = os.getenv("AZURE_WEBAPP_NAME") or (monitored_id.split("/")[-1] if monitored_id else None)
        self.sql_server = os.getenv("AZURE_SQL_SERVER")
        self.sql_database = os.getenv("AZURE_SQL_DATABASE")

        # Service Bus configuration
        self.servicebus_connection_string = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING")
        self.input_queue_name = "diagnosis-to-resolution"
        self.output_queue_name = "resolution-to-communication"
        self.is_listening = False
        
    async def resolve_incident(self, diagnosis):
        """Main resolution workflow"""
        print(f"[Resolution Agent] [INFO] Starting resolution for {diagnosis['incident_id']}")
        
        try:
            # Step 1: Determine resolution strategy
            strategy = await self.determine_strategy(diagnosis)
            
            # Step 2: Execute immediate fixes
            immediate_result = await self.execute_immediate_fix(diagnosis, strategy)
            
            # Step 3: Generate permanent fix using GitHub Copilot
            permanent_fix = await self.generate_permanent_fix(diagnosis, strategy)
            
            # Step 4: Create PR for permanent fix
            pr_result = await self.create_fix_pr(diagnosis, permanent_fix)
            
            resolution = {
                "incident_id": diagnosis["incident_id"],
                "strategy": strategy,
                "immediate_fix": immediate_result,
                "permanent_fix": permanent_fix,
                "pr_url": pr_result.get("url") if pr_result else None,
                "resolved_at": datetime.utcnow().isoformat(),
                "status": "resolved" if immediate_result["success"] else "failed"
            }
            
            print(f"[Resolution Agent] [SUCCESS] Resolution complete")
            print(f"  Status: {resolution['status']}")
            if pr_result:
                print(f"  PR Created: {pr_result['url']}")
            
            # Send resolution to Communication Agent via Service Bus
            await self.send_to_communication_agent(resolution)
            
            return resolution
            
        except Exception as e:
            print(f"[Resolution Agent] [ERROR] Resolution failed: {e}")
            return None
    
    async def determine_strategy(self, diagnosis):
        """Determine the best resolution strategy"""
        root_cause_type = diagnosis["root_cause"]["type"]
        
        # Strategy mapping based on root cause
        strategies = {
            "database_connection_exhaustion": {
                "immediate": "scale_database_tier",
                "permanent": "implement_connection_pooling"
            },
            "memory_leak": {
                "immediate": "restart_service",
                "permanent": "fix_memory_leak_code"
            },
            "rate_limit_breach": {
                "immediate": "enable_circuit_breaker",
                "permanent": "implement_backoff_retry"
            },
            "deployment_issue": {
                "immediate": "rollback_deployment",
                "permanent": "fix_deployment_config"
            }
        }
        
        strategy = strategies.get(root_cause_type, {
            "immediate": "manual_investigation_required",
            "permanent": "create_incident_report"
        })
        
        print(f"[Resolution Agent] Strategy: {strategy}")
        return strategy
    
    async def execute_immediate_fix(self, diagnosis, strategy):
        """Execute immediate automated fix"""
        immediate_action = strategy.get("immediate")
        
        try:
            if immediate_action == "scale_database_tier":
                result = await self._scale_database(diagnosis)
            elif immediate_action == "restart_service":
                result = await self._restart_service(diagnosis)
            elif immediate_action == "enable_circuit_breaker":
                result = await self._enable_circuit_breaker(diagnosis)
            elif immediate_action == "rollback_deployment":
                result = await self._rollback_deployment(diagnosis)
            else:
                result = {"success": False, "message": "No automated fix available"}
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _scale_database(self, diagnosis):
        """Scale Azure SQL Database to a higher tier using Azure Management SDK"""
        from azure.mgmt.sql import SqlManagementClient
        from azure.mgmt.sql.models import Sku

        affected = diagnosis.get("affected_resource", {})
        sql_server = self.sql_server or affected.get("sql_server")
        sql_database = self.sql_database or affected.get("sql_database")

        if not all([self.subscription_id, self.resource_group, sql_server, sql_database]):
            return {"success": False, "message": "Missing config: set AZURE_SQL_SERVER and AZURE_SQL_DATABASE env vars"}

        try:
            client = SqlManagementClient(self.credential, self.subscription_id)
            loop = asyncio.get_event_loop()

            # Get current database to read existing SKU and location
            db = await loop.run_in_executor(
                None, lambda: client.databases.get(self.resource_group, sql_server, sql_database)
            )
            current_sku = db.sku.name if db.sku else "S1"
            print(f"[Resolution Agent] Current SQL SKU: {current_sku}, scaling up...")

            # Scale up one tier
            scale_map = {"Basic": "S2", "S0": "S2", "S1": "S3", "S2": "S3", "S3": "S4", "S4": "P1"}
            target_sku = scale_map.get(current_sku, "S3")

            poller = await loop.run_in_executor(
                None,
                lambda: client.databases.begin_create_or_update(
                    self.resource_group, sql_server, sql_database,
                    {"location": db.location, "sku": Sku(name=target_sku)}
                )
            )
            await loop.run_in_executor(None, poller.result)

            print(f"[Resolution Agent] Database scaled: {current_sku} → {target_sku}")
            return {
                "success": True,
                "action": "scaled_database",
                "details": f"Scaled from {current_sku} to {target_sku}",
                "resource": f"{sql_server}/{sql_database}"
            }
        except Exception as e:
            print(f"[Resolution Agent] Database scaling failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _restart_service(self, diagnosis):
        """Restart Azure App Service using Azure Management SDK"""
        from azure.mgmt.web import WebSiteManagementClient

        affected = diagnosis.get("affected_resource", {})
        webapp_name = self.webapp_name or affected.get("webapp_name")

        if not all([self.subscription_id, self.resource_group, webapp_name]):
            return {"success": False, "message": "Missing config: set AZURE_WEBAPP_NAME or MONITORED_WEBAPP_ID env vars"}

        try:
            client = WebSiteManagementClient(self.credential, self.subscription_id)
            loop = asyncio.get_event_loop()

            print(f"[Resolution Agent] Restarting App Service: {webapp_name}...")
            await loop.run_in_executor(
                None, lambda: client.web_apps.restart(self.resource_group, webapp_name)
            )

            print(f"[Resolution Agent] App Service {webapp_name} restarted successfully")
            return {
                "success": True,
                "action": "restarted_service",
                "details": f"Restarted App Service: {webapp_name}",
                "resource": webapp_name
            }
        except Exception as e:
            print(f"[Resolution Agent] Service restart failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _enable_circuit_breaker(self, diagnosis):
        """Enable circuit breaker by updating Azure App Service application settings"""
        from azure.mgmt.web import WebSiteManagementClient
        from azure.mgmt.web.models import StringDictionary

        affected = diagnosis.get("affected_resource", {})
        webapp_name = self.webapp_name or affected.get("webapp_name")

        if not all([self.subscription_id, self.resource_group, webapp_name]):
            return {"success": False, "message": "Missing config: set AZURE_WEBAPP_NAME or MONITORED_WEBAPP_ID env vars"}

        try:
            client = WebSiteManagementClient(self.credential, self.subscription_id)
            loop = asyncio.get_event_loop()

            # Read current app settings and add circuit breaker flags
            current = await loop.run_in_executor(
                None, lambda: client.web_apps.list_application_settings(self.resource_group, webapp_name)
            )
            settings = dict(current.properties or {})
            settings["CIRCUIT_BREAKER_ENABLED"] = "true"
            settings["CIRCUIT_BREAKER_THRESHOLD"] = "5"
            settings["CIRCUIT_BREAKER_TIMEOUT_SECONDS"] = "60"

            await loop.run_in_executor(
                None,
                lambda: client.web_apps.update_application_settings(
                    self.resource_group, webapp_name, StringDictionary(properties=settings)
                )
            )

            print(f"[Resolution Agent] Circuit breaker enabled on {webapp_name}")
            return {
                "success": True,
                "action": "enabled_circuit_breaker",
                "details": f"Circuit breaker activated on App Service: {webapp_name} (threshold=5, timeout=60s)",
                "resource": webapp_name
            }
        except Exception as e:
            print(f"[Resolution Agent] Circuit breaker activation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _rollback_deployment(self, diagnosis):
        """Rollback deployment via Azure App Service slot swap or restart"""
        from azure.mgmt.web import WebSiteManagementClient
        from azure.mgmt.web.models import CsmSlotEntity

        affected = diagnosis.get("affected_resource", {})
        webapp_name = self.webapp_name or affected.get("webapp_name")

        if not all([self.subscription_id, self.resource_group, webapp_name]):
            return {"success": False, "message": "Missing config: set AZURE_WEBAPP_NAME or MONITORED_WEBAPP_ID env vars"}

        try:
            client = WebSiteManagementClient(self.credential, self.subscription_id)
            loop = asyncio.get_event_loop()

            # Check for deployment slots
            slots = await loop.run_in_executor(
                None, lambda: list(client.web_apps.list_slots(self.resource_group, webapp_name))
            )
            slot_names = [s.name for s in slots]

            if "staging" in slot_names:
                # Swap staging ↔ production to roll back to previous stable version
                print(f"[Resolution Agent] Swapping production ↔ staging slot for {webapp_name}...")
                poller = await loop.run_in_executor(
                    None,
                    lambda: client.web_apps.begin_swap_slot_with_production(
                        self.resource_group, webapp_name,
                        CsmSlotEntity(target_slot="staging", preserve_vnet=True)
                    )
                )
                await loop.run_in_executor(None, poller.result)
                details = f"Swapped production ↔ staging slot for {webapp_name}"
            else:
                # No staging slot — restart the app to recover from bad state
                print(f"[Resolution Agent] No staging slot found; restarting {webapp_name}...")
                await loop.run_in_executor(
                    None, lambda: client.web_apps.restart(self.resource_group, webapp_name)
                )
                details = f"No staging slot available; restarted {webapp_name} to recover"

            print(f"[Resolution Agent] Rollback complete: {details}")
            return {
                "success": True,
                "action": "rolled_back_deployment",
                "details": details,
                "resource": webapp_name
            }
        except Exception as e:
            print(f"[Resolution Agent] Rollback failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_permanent_fix(self, diagnosis, strategy):
        """Generate permanent fix using GitHub Copilot Agent Mode"""
        permanent_action = strategy.get("permanent")
        
        # Build runtime context from diagnosis
        runtime_data = self._extract_runtime_data(diagnosis)
        
        fix_code = await self.generate_fix_with_copilot(diagnosis, runtime_data)
        
        return {
            "action": permanent_action,
            "code_changes": fix_code,
            "files_modified": fix_code["files"] if fix_code else []
        }
    
    def _generate_connection_pooling_fix(self, diagnosis):
        """Generate connection pooling implementation"""
        # TODO: Use GitHub Copilot to generate actual fix
        # This is a placeholder
        
        return {
            "files": ["src/database/connection.js"],
            "changes": [
                {
                    "file": "src/database/connection.js",
                    "diff": """
+  const poolConfig = {
+    max: 20,
+    min: 5,
+    idleTimeoutMillis: 30000,
+    connectionTimeoutMillis: 2000
+  };
+  const pool = new Pool(poolConfig);
"""
                }
            ]
        }
    
    def _generate_memory_leak_fix(self, diagnosis):
        """Generate memory leak fix"""
        return {
            "files": ["src/services/cache.js"],
            "changes": []
        }
    
    def _generate_backoff_retry_fix(self, diagnosis):
        """Generate backoff retry implementation"""
        return {
            "files": ["src/services/api-client.js"],
            "changes": []
        }
    
    def _extract_runtime_data(self, diagnosis):
        """Extract runtime context data from diagnosis"""
        try:
            root_cause = diagnosis.get("root_cause", {})
            return {
                "error_message": root_cause.get("description", ""),
                "stack_trace": diagnosis.get("stack_trace", ""),
                "logs_excerpt": diagnosis.get("logs_excerpt", ""),
                "metrics_snapshot": diagnosis.get("metrics_snapshot", {}),
                "suspected_file": diagnosis.get("affected_component", ""),
                "relevant_code_snippet": diagnosis.get("code_snippet", "")
            }
        except Exception as e:
            print(f"[Resolution Agent] Error extracting runtime data: {e}")
            return None
    
    def _prepare_runtime_context(self, diagnosis, runtime_data):
        """Prepare real-time incident-driven context for Copilot"""
        if not runtime_data:
            return None
        
        try:
            # Validate required fields
            required_fields = [
                "error_message", "stack_trace", "logs_excerpt",
                "metrics_snapshot", "suspected_file", "relevant_code_snippet"
            ]
            
            for field in required_fields:
                if field not in runtime_data:
                    print(f"[Resolution Agent] Missing runtime data field: {field}")
                    return None
            
            # Mask sensitive data
            masked_data = self._mask_sensitive_data(runtime_data)
            
            # Build context from runtime evidence
            root_cause = diagnosis.get("root_cause", {})
            context = f"""
Incident ID: {diagnosis.get('incident_id')}
Root Cause Type: {root_cause.get('type', 'unknown')}
Root Cause Description: {root_cause.get('description', 'N/A')}
Affected Component: {diagnosis.get('affected_component')}

Runtime Evidence:
- Error Message: {masked_data['error_message'][:500]}
- Stack Trace: {masked_data['stack_trace'][:500]}
- Recent Logs: {masked_data['logs_excerpt'][:500]}
- Performance Metrics: {str(masked_data['metrics_snapshot'])[:500]}
- Suspected File: {masked_data['suspected_file']}

Code Context:
{masked_data['relevant_code_snippet'][:1000]}

Task: Generate a code fix based on the above runtime evidence.
Requirements:
- Address the root cause identified above
- Include proper error handling
- Add logging for debugging
- Follow best practices
- Ensure backward compatibility
- Add unit tests where applicable
"""
            return context.strip()
        
        except Exception as e:
            print(f"[Resolution Agent] Error preparing runtime context: {e}")
            return None
    
    def _mask_sensitive_data(self, runtime_data):
        """Mask sensitive information in runtime data"""
        import re
        masked = runtime_data.copy()
        
        # Mask API keys, passwords, tokens
        patterns = [
            r'(["\']?(?:api_key|password|token|secret)["\']?\s*[:=]\s*)[^,\s}]*',
            r'((?:https?://)?(?:.*@)?)[^/]+@',  # Email addresses
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{16}\b',  # Credit card
        ]
        
        for field in ['error_message', 'stack_trace', 'logs_excerpt']:
            if field in masked:
                text = masked[field]
                for pattern in patterns:
                    text = re.sub(pattern, r'\1***MASKED***', text, flags=re.IGNORECASE)
                masked[field] = text
        
        return masked
    
    async def generate_fix_with_copilot(self, diagnosis, runtime_data):
        """Generate fix code using GitHub Copilot suggest command with runtime context"""
        try:
            # Prepare context from runtime data instead of fix_type
            context = self._prepare_runtime_context(diagnosis, runtime_data)
            
            if not context:
                print("[Resolution Agent] Failed to prepare runtime context, falling back")
                return self._generate_fallback_from_diagnosis(diagnosis)
            
            print(f"[Resolution Agent] Requesting fix from GitHub Copilot using runtime context...")
            
            # Call gh copilot suggest with the runtime context
            copilot_output = await self._call_copilot_suggest(context)
            
            if not copilot_output:
                print("[Resolution Agent] Copilot suggest returned no output, using fallback")
                return self._generate_fallback_from_diagnosis(diagnosis)
            
            # Parse and structure the generated code
            fix_code = self._parse_copilot_output_runtime(copilot_output, diagnosis, runtime_data)
            
            print(f"[Resolution Agent] Successfully generated fix with GitHub Copilot")
            return fix_code
            
        except Exception as e:
            print(f"[Resolution Agent] Error generating fix with Copilot: {e}")
            return self._generate_fallback_from_diagnosis(diagnosis)
    
    def _prepare_copilot_context(self, diagnosis, fix_type):
        """DEPRECATED: Use _prepare_runtime_context instead"""
        root_cause = diagnosis.get("root_cause", {})
        context = f"""
Incident ID: {diagnosis.get('incident_id')}
Root Cause: {root_cause.get('type')}
Description: {root_cause.get('description')}
Affected Component: {diagnosis.get('affected_component')}

Task: Generate a code fix for {fix_type}
Requirements:
- Implement proper error handling
- Include comments
- Follow best practices
- Ensure backward compatibility
"""
        return context.strip()
    
    def _parse_copilot_output(self, copilot_output, fix_type, diagnosis):
        """DEPRECATED: Use _parse_copilot_output_runtime instead"""
        files_to_modify = self._get_files_for_fix_type(fix_type)
        
        return {
            "files": files_to_modify,
            "changes": [
                {
                    "file": files_to_modify[0] if files_to_modify else "src/fix.js",
                    "diff": copilot_output,
                    "suggested_by": "github_copilot",
                    "fix_type": fix_type
                }
            ]
        }
    
    def _parse_copilot_output_runtime(self, copilot_output, diagnosis, runtime_data):
        """Parse Copilot output using runtime context"""
        try:
            suspected_file = runtime_data.get("suspected_file", "")
            files_to_modify = [suspected_file] if suspected_file else ["src/fix.js"]
            
            return {
                "files": files_to_modify,
                "changes": [
                    {
                        "file": files_to_modify[0],
                        "diff": copilot_output,
                        "suggested_by": "github_copilot",
                        "root_cause_type": diagnosis.get("root_cause", {}).get("type", "unknown")
                    }
                ]
            }
        except Exception as e:
            print(f"[Resolution Agent] Error parsing Copilot output: {e}")
            return None
    
    def _get_files_for_fix_type(self, fix_type):
        """Get file paths for specific fix type"""
        file_mapping = {
            "connection_pooling": ["src/database/connection.js", "src/database/pool.js"],
            "memory_leak": ["src/services/cache.js", "src/memory/manager.js"],
            "backoff_retry": ["src/services/api-client.js", "src/utils/retry.js"]
        }
        return file_mapping.get(fix_type, ["src/fix.js"])
    
    def _generate_fallback_fix(self, fix_type, diagnosis):
        """DEPRECATED: Use _generate_fallback_from_diagnosis instead"""
        if fix_type == "connection_pooling":
            return self._generate_connection_pooling_fix(diagnosis)
        elif fix_type == "memory_leak":
            return self._generate_memory_leak_fix(diagnosis)
        elif fix_type == "backoff_retry":
            return self._generate_backoff_retry_fix(diagnosis)
        else:
            return None
    
    def _generate_fallback_from_diagnosis(self, diagnosis):
        """Generate fallback fix based on root cause from diagnosis"""
        try:
            root_cause_type = diagnosis.get("root_cause", {}).get("type", "")
            
            # Map root cause type to fallback fix
            fallback_mapping = {
                "database_connection_exhaustion": self._generate_connection_pooling_fix,
                "memory_leak": self._generate_memory_leak_fix,
                "rate_limit_breach": self._generate_backoff_retry_fix,
            }
            
            fallback_fn = fallback_mapping.get(root_cause_type)
            if fallback_fn:
                return fallback_fn(diagnosis)
            
            return None
        except Exception as e:
            print(f"[Resolution Agent] Error generating fallback: {e}")
            return None
    
    def _parse_copilot_output(self, copilot_output, fix_type, diagnosis):
        """DEPRECATED: Use _parse_copilot_output_runtime instead"""
        files_to_modify = self._get_files_for_fix_type(fix_type)
        
        return {
            "files": files_to_modify,
            "changes": [
                {
                    "file": files_to_modify[0] if files_to_modify else "src/fix.js",
                    "diff": copilot_output,
                    "suggested_by": "github_copilot",
                    "fix_type": fix_type
                }
            ]
        }
    
    def _get_files_for_fix_type(self, fix_type):
        """Get file paths for specific fix type"""
        file_mapping = {
            "connection_pooling": ["src/database/connection.js", "src/database/pool.js"],
            "memory_leak": ["src/services/cache.js", "src/memory/manager.js"],
            "backoff_retry": ["src/services/api-client.js", "src/utils/retry.js"]
        }
        return file_mapping.get(fix_type, ["src/fix.js"])
    
    def _generate_fallback_fix(self, fix_type, diagnosis):
        """DEPRECATED: Use _generate_fallback_from_diagnosis instead"""
        if fix_type == "connection_pooling":
            return self._generate_connection_pooling_fix(diagnosis)
        elif fix_type == "memory_leak":
            return self._generate_memory_leak_fix(diagnosis)
        elif fix_type == "backoff_retry":
            return self._generate_backoff_retry_fix(diagnosis)
        else:
            return None

    
    async def create_fix_pr(self, diagnosis, permanent_fix):
        """Call gh copilot command with diagnosis context using stdin"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Use stdin to avoid interactive prompt issue in subprocess
            # Pass context via stdin ("-") instead of as command argument
            # This prevents gh copilot from waiting for keyboard input
            logger.debug(f"[Resolution Agent] Calling Copilot (context: {len(context)} bytes)")
            
            result = subprocess.run(
                ["gh", "copilot", "-p", "-"],  # "-" means read prompt from stdin
                input=context,                  # Pass prompt via stdin
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60  # Increased from 30 to 60 seconds for slower networks
            )
            
            if result.returncode == 0:
                logger.info("[Resolution Agent] ✓ GitHub Copilot generated fix successfully")
                return result.stdout.strip()
            else:
                logger.warning(f"[Resolution Agent] Copilot returned error code {result.returncode}")
                logger.debug(f"Stderr: {result.stderr[:200] if result.stderr else 'None'}")
                return None
                    
        except FileNotFoundError:
            logger = logging.getLogger(__name__)
            logger.error("[Resolution Agent] ⚠️  'gh' command not found. Ensure GitHub CLI is installed.")
            return None
        except subprocess.TimeoutExpired:
            logger = logging.getLogger(__name__)
            logger.warning("[Resolution Agent] ⚠️  GitHub Copilot suggest command timed out (60s)")
            return None
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"[Resolution Agent] Error calling gh copilot suggest: {e}", exc_info=True)
            return None
    
    def _parse_copilot_output(self, copilot_output, fix_type, diagnosis):
        """Parse and structure Copilot-generated code"""
        files_to_modify = self._get_files_for_fix_type(fix_type)
        
        return {
            "files": files_to_modify,
            "changes": [
                {
                    "file": files_to_modify[0] if files_to_modify else "src/fix.js",
                    "diff": copilot_output,
                    "suggested_by": "github_copilot",
                    "fix_type": fix_type
                }
            ]
        }
    
    def _get_files_for_fix_type(self, fix_type):
        """Get file paths for specific fix type"""
        file_mapping = {
            "connection_pooling": ["src/database/connection.js", "src/database/pool.js"],
            "memory_leak": ["src/services/cache.js", "src/memory/manager.js"],
            "backoff_retry": ["src/services/api-client.js", "src/utils/retry.js"]
        }
        return file_mapping.get(fix_type, ["src/fix.js"])
    
    def _generate_fallback_fix(self, fix_type, diagnosis):
        """Generate fallback fix when Copilot is unavailable"""
        if fix_type == "connection_pooling":
            return self._generate_connection_pooling_fix(diagnosis)
        elif fix_type == "memory_leak":
            return self._generate_memory_leak_fix(diagnosis)
        elif fix_type == "backoff_retry":
            return self._generate_backoff_retry_fix(diagnosis)
        else:
            return None

    
    async def create_fix_pr(self, diagnosis, permanent_fix):
        """Create GitHub PR with permanent fix"""
        if not self.github_client or not permanent_fix["code_changes"]:
            return None
        
        try:
            repo = self.github_client.get_repo(f"{self.repo_owner}/{self.repo_name}")
            branch_name = f"fix/{diagnosis['incident_id'].lower()}"
            
            print("[Resolution Agent] Creating GitHub PR with Copilot-suggested fix...")
            
            # Get the base branch (usually 'main' or 'master')
            base_branch = repo.default_branch
            base = repo.get_branch(base_branch)
            
            # Create new branch from base
            try:
                # Try to get existing branch
                repo.get_branch(branch_name)
                print(f"[Resolution Agent] Branch {branch_name} already exists")
            except:
                # Create new branch if it doesn't exist
                repo.create_git_ref(
                    ref=f"refs/heads/{branch_name}",
                    sha=base.commit.sha
                )
                print(f"[Resolution Agent] Created branch {branch_name}")
            
            # Get fix details
            code_changes = permanent_fix["code_changes"]["changes"]
            fix_type = code_changes[0].get("fix_type", "automated") if code_changes else "automated"
            
            # Create commit message
            root_cause = diagnosis.get("root_cause", {})
            commit_message = f"Fix: {root_cause.get('description', 'Automated incident resolution')}\n\nIncident ID: {diagnosis['incident_id']}\nFix Type: {fix_type}\nGenerated by GitHub Copilot"
            
            # Commit changes to the new branch
            for change in code_changes:
                file_path = change.get("file", "src/fix.js")
                diff_content = change.get("diff", "")
                
                # Get or create file
                try:
                    existing_file = repo.get_contents(file_path, ref=branch_name)
                    # Update existing file
                    repo.update_file(
                        path=file_path,
                        message=commit_message,
                        content=diff_content,
                        sha=existing_file.sha,
                        branch=branch_name
                    )
                except:
                    # Create new file
                    repo.create_file(
                        path=file_path,
                        message=commit_message,
                        content=diff_content,
                        branch=branch_name
                    )
            
            # Create PR
            pr = repo.create_pull(
                title=f"[Incident Resolution] Fix: {root_cause.get('description', 'Automated resolution')}",
                body=self._generate_pr_description(diagnosis, permanent_fix),
                head=branch_name,
                base=base_branch
            )
            
            # Add labels
            pr.add_to_labels("incident-resolution", "automated", fix_type)
            
            print(f"[Resolution Agent] [SUCCESS] PR created: {pr.html_url}")
            
            return {
                "url": pr.html_url,
                "branch": branch_name,
                "title": pr.title,
                "number": pr.number,
                "suggested_by": "github_copilot"
            }
            
        except Exception as e:
            print(f"[Resolution Agent] Failed to create PR: {e}")
            return None
    
    def _generate_pr_description(self, diagnosis, permanent_fix):
        """Generate PR description with incident details"""
        root_cause = diagnosis.get("root_cause", {})
        code_changes = permanent_fix["code_changes"]
        
        description = f"""## Automated Incident Resolution

**Incident ID:** {diagnosis['incident_id']}

### Root Cause
- **Type:** {root_cause.get('type', 'Unknown')}
- **Description:** {root_cause.get('description', 'N/A')}
- **Severity:** {diagnosis.get('severity', 'Unknown')}

### Affected Component
{diagnosis.get('affected_component', 'N/A')}

### Fix Details
- **Action:** {permanent_fix.get('action', 'N/A')}
- **Files Modified:** {', '.join(code_changes.get('files', []))}
- **Generated by:** GitHub Copilot

### Changes
{code_changes.get('changes')[0].get('diff', 'See code changes') if code_changes.get('changes') else 'N/A'}

---
*This PR was automatically generated by the Azure Incident Resolver using GitHub Copilot.*
"""
        return description
    
    async def start_listening(self):
        """Start listening for diagnosis messages from diagnosis agent"""
        if not self.servicebus_connection_string:
            print("[Resolution Agent] ⚠️  AZURE_SERVICEBUS_CONNECTION_STRING not set")
            return
        
        self.is_listening = True
        print(f"[Resolution Agent] [INFO] Starting to listen for messages on queue: {self.input_queue_name}")
        
        try:
            async with AsyncServiceBusClient.from_connection_string(
                self.servicebus_connection_string
            ) as client:
                async with client.get_queue_receiver(self.input_queue_name) as receiver:
                    while self.is_listening:
                        try:
                            messages = await receiver.receive_messages(max_message_count=1, max_wait_time=5)
                            
                            for message in messages:
                                # Parse diagnosis data
                                diagnosis_data = json.loads(str(message))
                                print(f"[Resolution Agent] [INFO] Received diagnosis: {diagnosis_data['incident_id']}")
                                
                                # Process the diagnosis and resolve
                                resolution = await self.resolve_incident(diagnosis_data)
                                
                                # Complete the message
                                await receiver.complete_message(message)
                                
                        except asyncio.TimeoutError:
                            continue
                        except json.JSONDecodeError as e:
                            print(f"[Resolution Agent] [ERROR] Failed to parse message: {e}")
                            
        except Exception as e:
            print(f"[Resolution Agent] [ERROR] Error listening for messages: {e}")
    
    async def send_to_communication_agent(self, resolution):
        """Send resolution results to communication agent via Service Bus queue"""
        if not self.servicebus_connection_string:
            print("[Resolution Agent] ⚠️  AZURE_SERVICEBUS_CONNECTION_STRING not set")
            return
        
        try:
            async with AsyncServiceBusClient.from_connection_string(
                self.servicebus_connection_string
            ) as client:
                async with client.get_queue_sender(self.output_queue_name) as sender:
                    # Serialize resolution to JSON
                    resolution_json = json.dumps(resolution)
                    
                    # Create and send message
                    message = ServiceBusMessage(
                        body=resolution_json,
                        subject="resolution_complete",
                        content_type="application/json"
                    )
                    
                    await sender.send_messages(message)
                    print(f"[Resolution Agent] [SUCCESS] Resolution {resolution['incident_id']} sent to communication agent")
                    
        except Exception as e:
            print(f"[Resolution Agent] [ERROR] Failed to send resolution to communication agent: {e}")


# Main execution for testing
if __name__ == "__main__":
    agent = ResolutionAgent()
    
    # Option 1: Listen for messages from diagnosis agent
    try:
        asyncio.run(agent.start_listening())
    except KeyboardInterrupt:
        print("\n[Resolution Agent] Shutting down gracefully...")
        agent.is_listening = False
