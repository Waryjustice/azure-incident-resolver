"""
Diagnosis Agent - Analyzes incidents and determines root cause

This agent:
- Receives incident data from Detection Agent
- Queries logs, traces, and metrics across systems
- Uses Microsoft Foundry RAG to search past incidents
- Identifies root cause and impact scope
- Sends diagnosis to Resolution Agent
"""

import os
import json
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.servicebus.aio import ServiceBusClient as AsyncServiceBusClient
from azure.servicebus import ServiceBusMessage
import asyncio


class DiagnosisAgent:
    def __init__(self):
        self.foundry_endpoint = os.getenv("FOUNDRY_ENDPOINT")
        self.foundry_api_key = os.getenv("FOUNDRY_API_KEY")
        self.timeout = int(os.getenv("DIAGNOSIS_TIMEOUT_SECONDS", 300))
        
        # Service Bus configuration
        self.servicebus_connection_string = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING")
        self.input_queue_name = "detection-to-diagnosis"
        self.output_queue_name = "diagnosis-to-resolution"
        self.is_listening = False
        
    async def diagnose_incident(self, incident):
        """Main diagnosis workflow"""
        print(f"[Diagnosis Agent] [INFO] Starting diagnosis for {incident['id']}")
        
        try:
            # Step 1: Gather additional context
            context = await self.gather_context(incident)
            
            # Step 2: Search for similar past incidents
            similar_incidents = await self.search_past_incidents(context)
            
            # Step 3: Analyze logs and traces
            log_analysis = await self.analyze_logs(incident, context)
            
            # Step 4: Determine root cause
            root_cause = await self.determine_root_cause(
                incident, context, similar_incidents, log_analysis
            )
            
            # Step 5: Assess impact
            impact = await self.assess_impact(incident, root_cause)
            
            diagnosis = {
                "incident_id": incident["id"],
                "root_cause": root_cause,
                "impact": impact,
                "context": context,
                "similar_incidents": similar_incidents,
                "diagnosed_at": datetime.utcnow().isoformat(),
                "confidence": self._calculate_confidence(root_cause, similar_incidents)
            }
            
            print(f"[Diagnosis Agent] [SUCCESS] Diagnosis complete")
            print(f"  Root Cause: {root_cause['description']}")
            print(f"  Confidence: {diagnosis['confidence']}%")
            
            # Send diagnosis to Resolution Agent via Service Bus
            await self.send_to_resolution_agent(diagnosis)
            
            return diagnosis
            
        except Exception as e:
            print(f"[Diagnosis Agent] [ERROR] Diagnosis failed: {e}")
            return None
    
    async def gather_context(self, incident):
        """Gather additional context about the incident"""
        # TODO: Implement context gathering
        # - Query related resources
        # - Get recent deployments
        # - Check for configuration changes
        # - Gather dependency health status
        
        context = {
            "resource_details": {},
            "recent_deployments": [],
            "config_changes": [],
            "dependencies": []
        }
        
        return context
    
    async def search_past_incidents(self, context):
        """Search for similar past incidents using Microsoft Foundry RAG"""
        # TODO: Implement Microsoft Foundry integration
        # - Convert incident to embedding
        # - Search vector database of past incidents
        # - Retrieve relevant runbooks and solutions
        
        try:
            # Example Foundry query
            # query = self._build_foundry_query(context)
            # response = await self.foundry_client.search(query)
            
            similar_incidents = [
                # {
                #     "id": "INC-20250101120000",
                #     "similarity": 0.89,
                #     "resolution": "Scaled database tier from S1 to S3"
                # }
            ]
            
            return similar_incidents
            
        except Exception as e:
            print(f"[Diagnosis Agent] Failed to search past incidents: {e}")
            return []
    
    async def analyze_logs(self, incident, context):
        """Analyze logs and traces for patterns"""
        # TODO: Implement log analysis
        # - Query Application Insights
        # - Parse error messages
        # - Identify error patterns
        # - Correlate events across services
        
        analysis = {
            "error_patterns": [],
            "suspicious_events": [],
            "correlation_id": None
        }
        
        return analysis
    
    async def determine_root_cause(self, incident, context, similar_incidents, log_analysis):
        """Determine the root cause using AI analysis"""
        # TODO: Use Azure OpenAI to analyze all gathered data
        # - Combine all context, logs, and historical data
        # - Use LLM to reason about root cause
        # - Cross-reference with similar incidents
        
        # Example root cause determination
        root_cause = {
            "type": "database_connection_exhaustion",
            "description": "Database connection pool exhausted due to connection leaks",
            "affected_component": "API Gateway",
            "evidence": [
                "Connection pool at 100% utilization",
                "Timeout errors in application logs",
                "Similar pattern in INC-20250101120000"
            ]
        }
        
        return root_cause
    
    async def assess_impact(self, incident, root_cause):
        """Assess the impact scope of the incident"""
        # TODO: Implement impact assessment
        # - Identify affected services
        # - Estimate user impact
        # - Calculate business impact
        
        impact = {
            "affected_services": ["API Gateway", "User Service"],
            "estimated_users_affected": 0,  # TODO: Calculate
            "business_impact": "high",
            "sla_breach": False
        }
        
        return impact
    
    def _calculate_confidence(self, root_cause, similar_incidents):
        """Calculate confidence level in diagnosis"""
        # Simple confidence calculation
        base_confidence = 60
        
        if similar_incidents:
            base_confidence += 20
        
        if len(root_cause.get("evidence", [])) >= 3:
            base_confidence += 20
        
        return min(base_confidence, 95)
    
    async def start_listening(self):
        """Start listening for incident messages from detection agent"""
        if not self.servicebus_connection_string:
            print("[Diagnosis Agent] ⚠️  AZURE_SERVICEBUS_CONNECTION_STRING not set")
            return
        
        self.is_listening = True
        print(f"[Diagnosis Agent] [INFO] Starting to listen for messages on queue: {self.input_queue_name}")
        
        try:
            async with AsyncServiceBusClient.from_connection_string(
                self.servicebus_connection_string
            ) as client:
                async with client.get_queue_receiver(self.input_queue_name) as receiver:
                    while self.is_listening:
                        try:
                            messages = await receiver.receive_messages(max_message_count=1, max_wait_time=5)
                            
                            for message in messages:
                                # Parse incident data
                                incident_data = json.loads(str(message))
                                print(f"[Diagnosis Agent] [INFO] Received incident: {incident_data['id']}")
                                
                                # Process the incident
                                diagnosis = await self.diagnose_incident(incident_data)
                                
                                # Complete the message
                                await receiver.complete_message(message)
                                
                        except asyncio.TimeoutError:
                            continue
                        except json.JSONDecodeError as e:
                    print(f"[Diagnosis Agent] [ERROR] Failed to parse message: {e}")
                            
        except Exception as e:
            print(f"[Diagnosis Agent] [ERROR] Error listening for messages: {e}")
    
    async def send_to_resolution_agent(self, diagnosis):
        """Send diagnosis results to resolution agent via Service Bus queue"""
        if not self.servicebus_connection_string:
            print("[Diagnosis Agent] ⚠️  AZURE_SERVICEBUS_CONNECTION_STRING not set")
            return
        
        try:
            async with AsyncServiceBusClient.from_connection_string(
                self.servicebus_connection_string
            ) as client:
                async with client.get_queue_sender(self.output_queue_name) as sender:
                    # Serialize diagnosis to JSON
                    diagnosis_json = json.dumps(diagnosis)
                    
                    # Create and send message
                    message = ServiceBusMessage(
                        body=diagnosis_json,
                        subject="diagnosis_complete",
                        content_type="application/json"
                    )
                    
                    await sender.send_messages(message)
                    print(f"[Diagnosis Agent] [SUCCESS] Diagnosis {diagnosis['incident_id']} sent to resolution agent")
                    
        except Exception as e:
            print(f"[Diagnosis Agent] [ERROR] Failed to send diagnosis to resolution agent: {e}")


# Main execution for testing
if __name__ == "__main__":
    agent = DiagnosisAgent()
    
    # Option 1: Listen for messages from detection agent
    try:
        asyncio.run(agent.start_listening())
    except KeyboardInterrupt:
        print("\n[Diagnosis Agent] Shutting down gracefully...")
        agent.is_listening = False
