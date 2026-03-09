"""
Diagnosis Agent - Analyzes incidents and determines root cause

This agent:
- Receives incident data from Detection Agent
- Queries logs and metrics across systems
- Uses GitHub Models AI (gpt-4o-mini) to identify root cause
- Searches past incidents for patterns (in-memory RAG)
- Sends diagnosis to Resolution Agent
"""

import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from azure.servicebus.aio import ServiceBusClient as AsyncServiceBusClient
from azure.servicebus import ServiceBusMessage
import asyncio

_SYSTEM_PROMPT = """You are an expert Site Reliability Engineer diagnosing production incidents in Azure environments.
Analyze the incident data provided and identify the root cause.
Respond with ONLY a valid JSON object in this exact format (no markdown, no explanation):
{
  "type": "snake_case_type",
  "description": "Clear one-sentence description of the root cause",
  "affected_component": "Component name",
  "evidence": ["Evidence point 1", "Evidence point 2", "Evidence point 3"]
}"""


class DiagnosisAgent:
    def __init__(self):
        self.timeout = int(os.getenv("DIAGNOSIS_TIMEOUT_SECONDS", 300))
        self._incident_history = []  # In-memory store for simple RAG

        # GitHub Models AI client
        github_token = os.getenv("GITHUB_TOKEN")
        self.model_name = os.getenv("GITHUB_MODEL_NAME", "openai/gpt-4o-mini")
        self._ai_client = None
        if github_token:
            try:
                self._ai_client = ChatCompletionsClient(
                    endpoint="https://models.inference.ai.azure.com",
                    credential=AzureKeyCredential(github_token),
                )
                print(f"[Diagnosis Agent] ✅ GitHub Models AI client initialized ({self.model_name})")
            except Exception as e:
                print(f"[Diagnosis Agent] ⚠️  Could not initialize GitHub Models client: {e}")
        else:
            print("[Diagnosis Agent] ⚠️  GITHUB_TOKEN not set — AI diagnosis unavailable")

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

            # Store in history for future RAG lookups
            self._incident_history.append({
                "incident_id": incident["id"],
                "root_cause": root_cause,
                "context": context,
                "resolution_hint": root_cause.get("type", ""),
            })

            return diagnosis
            
        except Exception as e:
            print(f"[Diagnosis Agent] [ERROR] Diagnosis failed: {e}")
            return None
    
    async def gather_context(self, incident):
        """Gather structured context from the incident"""
        resource = incident.get("resource", {})
        anomalies = incident.get("anomalies", [])
        return {
            "resource_type": resource.get("type", "Unknown"),
            "resource_name": resource.get("name", "Unknown"),
            "anomaly_count": len(anomalies),
            "anomaly_metrics": [a.get("metric") for a in anomalies],
            "peak_values": {a.get("metric"): a.get("value") for a in anomalies},
            "thresholds": {a.get("metric"): a.get("threshold") for a in anomalies},
            "recent_deployments": [],
            "config_changes": [],
        }
    
    async def search_past_incidents(self, context):
        """Search in-memory incident history for similar past incidents (simple RAG)"""
        if not self._incident_history:
            return []

        resource_type = context.get("resource_type", "").lower()
        metrics = [m.lower() for m in context.get("anomaly_metrics", []) if m]

        matches = []
        for past in self._incident_history[-20:]:
            past_rc = past.get("root_cause", {})
            past_resource = past.get("context", {}).get("resource_type", "").lower()
            score = 0
            if past_resource == resource_type:
                score += 2
            for metric in metrics:
                if metric in past_rc.get("type", "").lower() or metric in past_rc.get("description", "").lower():
                    score += 1
            if score > 0:
                matches.append({
                    "similarity": min(score * 0.3, 0.95),
                    "root_cause": past_rc,
                    "resolution_hint": past.get("resolution_hint", ""),
                })
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches[:3]
    
    async def analyze_logs(self, incident, context):
        """Analyze anomaly patterns from incident data"""
        anomalies = incident.get("anomalies", [])
        error_patterns = []
        suspicious_events = []
        for anomaly in anomalies:
            metric = anomaly.get("metric", "UNKNOWN")
            value = anomaly.get("value", 0)
            threshold = anomaly.get("threshold", 1)
            ratio = value / threshold if threshold else 0
            error_patterns.append(f"{metric} at {value} ({ratio:.1f}x threshold of {threshold})")
            if anomaly.get("severity") in ("critical", "high"):
                suspicious_events.append(metric)
        return {
            "error_patterns": error_patterns,
            "suspicious_events": suspicious_events,
            "correlation_id": incident.get("id"),
        }
    
    async def determine_root_cause(self, incident, context, similar_incidents, log_analysis):
        """Determine root cause using GitHub Models AI (gpt-4o-mini)"""
        if self._ai_client:
            prompt = self._build_prompt(incident, context, similar_incidents, log_analysis)
            try:
                response = await asyncio.to_thread(
                    self._ai_client.complete,
                    messages=[
                        SystemMessage(content=_SYSTEM_PROMPT),
                        UserMessage(content=prompt),
                    ],
                    model=self.model_name,
                    temperature=0.2,
                    max_tokens=400,
                )
                raw = response.choices[0].message.content.strip()
                # Strip markdown code fences if present (handles ```json, ```JSON, ``` etc.)
                raw = re.sub(r'^```[a-zA-Z]*\n?', '', raw)
                raw = re.sub(r'\n?```$', '', raw)
                raw = raw.strip()
                root_cause = json.loads(raw)
                print(f"[Diagnosis Agent] 🤖 AI diagnosis: {root_cause.get('description', '')}")
                return root_cause
            except json.JSONDecodeError as e:
                print(f"[Diagnosis Agent] ⚠️  Could not parse AI response as JSON: {e}")
            except Exception as e:
                print(f"[Diagnosis Agent] ⚠️  AI call failed ({e}), using rule-based fallback")

        return self._rule_based_root_cause(incident)

    def _build_prompt(self, incident, context, similar_incidents, log_analysis):
        """Build a structured prompt for AI diagnosis"""
        similar_text = ""
        if similar_incidents:
            similar_text = "\n\nSIMILAR PAST INCIDENTS:\n"
            for s in similar_incidents[:2]:
                rc = s.get("root_cause", {})
                similar_text += f"  - {rc.get('description', 'Unknown')} (similarity: {s['similarity']:.0%})\n"

        patterns = "\n".join(f"  • {p}" for p in log_analysis.get("error_patterns", []))
        return f"""INCIDENT: {incident.get('id', 'Unknown')}
SEVERITY: {incident.get('severity', 'unknown').upper()}
RESOURCE: {context.get('resource_type')} — {context.get('resource_name')}

ANOMALIES DETECTED:
{patterns}

PEAK VALUES vs THRESHOLDS:
{json.dumps(context.get('peak_values', {}), indent=2)}{similar_text}

Based on this data, identify the root cause."""

    def _rule_based_root_cause(self, incident):
        """Rule-based fallback when AI is unavailable"""
        anomalies = incident.get("anomalies", [])
        metric = anomalies[0].get("metric", "UNKNOWN") if anomalies else "UNKNOWN"
        resource_type = incident.get("resource", {}).get("type", "Unknown")
        type_map = {
            "CONNECTION_COUNT":   ("database_connection_exhaustion", "Database connection pool exhausted", "Database"),
            "MEMORY_USAGE":       ("memory_leak", "Service memory usage critical — likely memory leak", "Application Service"),
            "ERROR_RATE":         ("elevated_error_rate", "Error rate spike detected", "API Gateway"),
            "CPU_USAGE":          ("cpu_spike", "CPU utilization exceeded safe threshold", resource_type),
            "DISK_USAGE":         ("disk_space_exhaustion", "Disk space critically low", resource_type),
            "QUERY_DURATION":     ("slow_database_query", "Database query performance degraded", "Database"),
            "RATE_LIMIT_ERRORS":  ("api_rate_limit_breach", "Third-party API rate limit exceeded", "API Gateway"),
            "DEPLOYMENT_ERROR_RATE": ("failed_deployment", "Recent deployment causing elevated error rate", "Deployment"),
        }
        type_key, description, component = type_map.get(
            metric,
            ("unknown_anomaly", f"Anomaly detected in {resource_type}: {metric}", resource_type),
        )
        value = anomalies[0].get("value", 0) if anomalies else 0
        threshold = anomalies[0].get("threshold", 1) if anomalies else 1
        ratio = (value / max(threshold, 1) - 1) * 100
        return {
            "type": type_key,
            "description": description,
            "affected_component": component,
            "evidence": [
                f"{metric} exceeded threshold by {ratio:.0f}%" if anomalies else "Anomaly detected",
                f"Severity: {incident.get('severity', 'unknown')}",
                f"Incident ID: {incident.get('id', 'Unknown')}",
            ],
        }
    
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

        while self.is_listening:
            try:
                async with AsyncServiceBusClient.from_connection_string(
                    self.servicebus_connection_string
                ) as client:
                    async with client.get_queue_receiver(self.input_queue_name) as receiver:
                        print("[Diagnosis Agent] [INFO] Service Bus connection established, waiting for messages...")
                        while self.is_listening:
                            try:
                                messages = await receiver.receive_messages(max_message_count=1, max_wait_time=5)

                                for message in messages:
                                    try:
                                        incident_data = json.loads(str(message))
                                        print(f"[Diagnosis Agent] [INFO] Received incident: {incident_data['id']}")

                                        diagnosis = await self.diagnose_incident(incident_data)

                                        # Always complete the message to remove it from the queue
                                        await receiver.complete_message(message)

                                        if diagnosis:
                                            # Only send to next queue when running as a standalone listener
                                            await self.send_to_resolution_agent(diagnosis)
                                            print(f"[Diagnosis Agent] [INFO] Diagnosis forwarded to resolution queue for: {incident_data['id']}")
                                        else:
                                            print(f"[Diagnosis Agent] [WARNING] Diagnosis returned None for: {incident_data['id']}")

                                    except json.JSONDecodeError as e:
                                        print(f"[Diagnosis Agent] [ERROR] Failed to parse message body: {e}")
                                        await receiver.dead_letter_message(message, reason="InvalidJSON")
                                    except Exception as e:
                                        print(f"[Diagnosis Agent] [ERROR] Failed to process message: {e}")
                                        # Abandon so the message becomes available again (up to max delivery count)
                                        await receiver.abandon_message(message)

                                await asyncio.sleep(0)  # Yield control to the event loop

                            except asyncio.TimeoutError:
                                continue

            except Exception as e:
                print(f"[Diagnosis Agent] [ERROR] Service Bus connection lost: {e}")
                if self.is_listening:
                    print("[Diagnosis Agent] [INFO] Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)
    
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
    import sys

    agent = DiagnosisAgent()

    if "--test" in sys.argv or os.getenv("TEST_MODE", "false").lower() == "true":
        # Standalone test: inject a synthetic incident directly without needing Service Bus
        print("\n[Diagnosis Agent] TEST MODE — running with synthetic incident\n")
        test_incident = {
            "id": f"INC-TEST-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "resource": {"type": "Database", "id": "db-prod-001", "name": "Production SQL Database"},
            "anomalies": [
                {"metric": "CONNECTION_COUNT", "value": 500, "threshold": 100, "severity": "high"},
                {"metric": "CPU_PERCENTAGE",   "value": 92,  "threshold": 80,  "severity": "critical"},
            ],
            "detected_at": datetime.utcnow().isoformat(),
            "severity": "high"
        }
        import json as _json
        print(f"[Diagnosis Agent] Injecting test incident: {_json.dumps(test_incident, indent=2)}\n")
        try:
            diagnosis = asyncio.run(agent.diagnose_incident(test_incident))
            if diagnosis:
                print(f"\n[Diagnosis Agent] ✅ Diagnosis result:")
                print(_json.dumps(diagnosis, indent=2, default=str))
            else:
                print("\n[Diagnosis Agent] ❌ Diagnosis returned None")
        except KeyboardInterrupt:
            print("\n[Diagnosis Agent] Test interrupted.")
    else:
        # Listen for real messages from the Detection Agent via Service Bus
        try:
            asyncio.run(agent.start_listening())
        except KeyboardInterrupt:
            print("\n[Diagnosis Agent] Shutting down gracefully...")
            agent.is_listening = False
