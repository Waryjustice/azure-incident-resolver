"""
Resolution Agent - Executes automated fixes and generates code solutions

This agent:
- Receives diagnosis from Diagnosis Agent
- Determines appropriate resolution strategy
- Executes automated fixes (scaling, restarts, config changes)
- Uses GitHub Copilot Agent Mode to generate code fixes
- Creates PRs for permanent solutions
"""

import os
import json
from datetime import datetime
import asyncio
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
        """Scale database tier"""
        # TODO: Implement Azure Database scaling
        # - Get current tier
        # - Scale to higher tier
        # - Monitor scaling progress
        
        print("[Resolution Agent] Scaling database tier...")
        await asyncio.sleep(2)  # Simulate scaling
        
        return {
            "success": True,
            "action": "scaled_database",
            "details": "Scaled from S1 to S3"
        }
    
    async def _restart_service(self, diagnosis):
        """Restart affected service"""
        # TODO: Implement service restart
        # - Identify pods/instances
        # - Perform rolling restart
        # - Verify health
        
        print("[Resolution Agent] Restarting service...")
        await asyncio.sleep(2)  # Simulate restart
        
        return {
            "success": True,
            "action": "restarted_service",
            "details": "Restarted 3 pods"
        }
    
    async def _enable_circuit_breaker(self, diagnosis):
        """Enable circuit breaker"""
        # TODO: Implement circuit breaker activation
        
        print("[Resolution Agent] Enabling circuit breaker...")
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "action": "enabled_circuit_breaker",
            "details": "Circuit breaker activated for API gateway"
        }
    
    async def _rollback_deployment(self, diagnosis):
        """Rollback recent deployment"""
        # TODO: Implement deployment rollback via GitHub Actions or Azure DevOps
        
        print("[Resolution Agent] Rolling back deployment...")
        await asyncio.sleep(2)
        
        return {
            "success": True,
            "action": "rolled_back_deployment",
            "details": "Rolled back to previous stable version"
        }
    
    async def generate_permanent_fix(self, diagnosis, strategy):
        """Generate permanent fix using GitHub Copilot Agent Mode"""
        permanent_action = strategy.get("permanent")
        
        # TODO: Integrate with GitHub Copilot Agent Mode
        # - Analyze codebase
        # - Generate fix code
        # - Run tests
        
        if permanent_action == "implement_connection_pooling":
            fix_code = self._generate_connection_pooling_fix(diagnosis)
        elif permanent_action == "fix_memory_leak_code":
            fix_code = self._generate_memory_leak_fix(diagnosis)
        elif permanent_action == "implement_backoff_retry":
            fix_code = self._generate_backoff_retry_fix(diagnosis)
        else:
            fix_code = None
        
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
    
    async def create_fix_pr(self, diagnosis, permanent_fix):
        """Create GitHub PR with permanent fix"""
        if not self.github_client or not permanent_fix["code_changes"]:
            return None
        
        try:
            # TODO: Implement actual GitHub PR creation
            # - Create branch
            # - Commit changes
            # - Create PR
            # - Add labels and reviewers
            
            print("[Resolution Agent] Creating GitHub PR...")
            
            pr_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/pull/123"
            
            return {
                "url": pr_url,
                "branch": f"fix/{diagnosis['incident_id'].lower()}",
                "title": f"Fix: {diagnosis['root_cause']['description']}"
            }
            
        except Exception as e:
            print(f"[Resolution Agent] Failed to create PR: {e}")
            return None
    
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
