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
        
        if permanent_action == "implement_connection_pooling":
            fix_code = await self.generate_fix_with_copilot(diagnosis, "connection_pooling")
        elif permanent_action == "fix_memory_leak_code":
            fix_code = await self.generate_fix_with_copilot(diagnosis, "memory_leak")
        elif permanent_action == "implement_backoff_retry":
            fix_code = await self.generate_fix_with_copilot(diagnosis, "backoff_retry")
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
    
    async def generate_fix_with_copilot(self, diagnosis, fix_type):
        """Generate fix code using GitHub Copilot suggest command"""
        try:
            # Prepare context for Copilot based on diagnosis and fix type
            context = self._prepare_copilot_context(diagnosis, fix_type)
            
            print(f"[Resolution Agent] Requesting fix from GitHub Copilot for {fix_type}...")
            
            # Call gh copilot suggest with the diagnosis context
            copilot_output = await self._call_copilot_suggest(context)
            
            if not copilot_output:
                print("[Resolution Agent] Copilot suggest returned no output, using fallback")
                return self._generate_fallback_fix(fix_type, diagnosis)
            
            # Parse and structure the generated code
            fix_code = self._parse_copilot_output(copilot_output, fix_type, diagnosis)
            
            print(f"[Resolution Agent] Successfully generated fix with GitHub Copilot")
            return fix_code
            
        except Exception as e:
            print(f"[Resolution Agent] Error generating fix with Copilot: {e}")
            return self._generate_fallback_fix(fix_type, diagnosis)
    
    def _prepare_copilot_context(self, diagnosis, fix_type):
        """Prepare context information for Copilot"""
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
    
    async def _call_copilot_suggest(self, context):
        """Call gh copilot suggest command with diagnosis context"""
        try:
            # Create a temporary file for the context prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(context)
                temp_file = f.name
            
            try:
                # Call gh copilot suggest command
                result = subprocess.run(
                    ["gh", "copilot", "suggest", "-t", "shell", context],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return result.stdout.strip()
                else:
                    print(f"[Resolution Agent] Copilot suggest error: {result.stderr}")
                    return None
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except FileNotFoundError:
            print("[Resolution Agent] ⚠️  'gh' command not found. Ensure GitHub CLI is installed.")
            return None
        except subprocess.TimeoutExpired:
            print("[Resolution Agent] ⚠️  GitHub Copilot suggest command timed out")
            return None
        except Exception as e:
            print(f"[Resolution Agent] Error calling gh copilot suggest: {e}")
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
