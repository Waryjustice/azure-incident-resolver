"""
Communication Agent - Handles stakeholder notifications and reporting

This agent:
- Sends real-time updates to stakeholders (Teams/Slack)
- Generates incident reports and post-mortems
- Creates timeline of incident events
- Learns from incidents for future prevention
- Updates status pages
"""

import os
import json
from datetime import datetime
import asyncio
from azure.identity import DefaultAzureCredential
from azure.servicebus.aio import ServiceBusClient as AsyncServiceBusClient
from azure.servicebus import ServiceBusMessage


class CommunicationAgent:
    def __init__(self):
        self.teams_webhook = os.getenv("TEAMS_WEBHOOK_URL")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        
        # Service Bus configuration
        self.servicebus_connection_string = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING")
        self.input_queue_name = "resolution-to-communication"
        self.is_listening = False
        
    async def handle_incident_lifecycle(self, incident_data):
        """Handle communication throughout incident lifecycle"""
        
        # Detection phase
        if incident_data["phase"] == "detected":
            await self.notify_detection(incident_data)
        
        # Diagnosis phase
        elif incident_data["phase"] == "diagnosed":
            await self.notify_diagnosis(incident_data)
        
        # Resolution phase
        elif incident_data["phase"] == "resolved":
            await self.notify_resolution(incident_data)
            await self.generate_post_mortem(incident_data)
        
        # Resolution failed
        elif incident_data["phase"] == "failed":
            await self.escalate_to_oncall(incident_data)
    
    async def notify_detection(self, incident):
        """Send initial incident detection notification"""
        incident_id = incident.get('incident_id') or incident.get('id', 'Unknown')
        print(f"[Communication Agent] [INFO] Notifying detection: {incident_id}")
        
        message = self._format_detection_message(incident)
        
        # Send to Teams
        if self.teams_webhook:
            await self._send_teams_message(message)
        
        # Send to Slack
        if self.slack_webhook:
            await self._send_slack_message(message)
        
        print(f"[Communication Agent] [SUCCESS] Detection notification sent")
    
    async def notify_diagnosis(self, diagnosis):
        """Send diagnosis update"""
        incident_id = diagnosis.get('incident_id') or diagnosis.get('id', 'Unknown')
        print(f"[Communication Agent] [INFO] Notifying diagnosis: {incident_id}")
        
        message = self._format_diagnosis_message(diagnosis)
        
        if self.teams_webhook:
            await self._send_teams_message(message)
        
        if self.slack_webhook:
            await self._send_slack_message(message)
        
        print("[Communication Agent] [SUCCESS] Diagnosis notification sent")
    
    async def notify_resolution(self, resolution):
        """Send resolution notification"""
        incident_id = resolution.get('incident_id') or resolution.get('id', 'Unknown')
        print(f"[Communication Agent] [INFO] Notifying resolution: {incident_id}")
        
        message = self._format_resolution_message(resolution)
        
        if self.teams_webhook:
            await self._send_teams_message(message)
        
        if self.slack_webhook:
            await self._send_slack_message(message)
        
        print("[Communication Agent] [SUCCESS] Resolution notification sent")
    
    async def generate_post_mortem(self, full_incident_data):
        """Generate comprehensive post-mortem report"""
        print(f"[Communication Agent] [INFO] Generating post-mortem")
        
        incident_id = full_incident_data.get('incident_id') or full_incident_data.get('id', 'Unknown')
        # - Summarize timeline
        # - Analyze root cause
        # - Document lessons learned
        # - Create action items
        
        post_mortem = {
            "incident_id": incident_id,
            "title": full_incident_data.get("diagnosis", {}).get("root_cause", {}).get("description", "Unknown issue"),
            "timeline": self._build_timeline(full_incident_data),
            "root_cause": full_incident_data.get("diagnosis", {}).get("root_cause", {}),
            "impact": full_incident_data.get("diagnosis", {}).get("impact", {}),
            "resolution": full_incident_data.get("resolution", {}),
            "lessons_learned": self._generate_lessons_learned(full_incident_data),
            "action_items": self._generate_action_items(full_incident_data),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Save to incident database for future RAG queries
        await self._save_to_incident_database(post_mortem)
        
        # Send post-mortem to stakeholders
        await self._send_post_mortem(post_mortem)
        
        print("[Communication Agent] [SUCCESS] Post-mortem generated and distributed")
        return post_mortem
    
    async def escalate_to_oncall(self, incident):
        """Escalate to on-call engineer when automation fails"""
        incident_id = incident.get('incident_id') or incident.get('id', 'Unknown')
        print(f"[Communication Agent] [ERROR] Escalating to on-call: {incident_id}")
        
        # TODO: Implement PagerDuty/OpsGenie integration
        # - Create high-priority alert
        # - Include all incident context
        # - Add runbook links
        
        escalation_message = f"""
        ESCALATION REQUIRED
        
        Incident: {incident_id}
        Automated resolution failed - manual intervention needed
        
        Details:
        - Root Cause: {incident.get('diagnosis', {}).get('root_cause', {}).get('description', 'Unknown')}
        - Impact: {incident.get('diagnosis', {}).get('impact', {}).get('business_impact', 'Unknown')}
        - Automated Actions Attempted: {incident.get('resolution', {}).get('immediate_fix', {}).get('action', 'None')}
        
        Please investigate immediately.
        """
        
        if self.teams_webhook:
            await self._send_teams_message({"text": escalation_message, "priority": "high"})
        
        print("[Communication Agent] [SUCCESS] Escalation sent")
    
    def _format_detection_message(self, incident):
        """Format detection notification message"""
        incident_id = incident.get('incident_id') or incident.get('id', 'Unknown')
        return {
            "title": f"[WARNING] Incident Detected: {incident_id}",
            "text": f"""
            New incident detected by Azure Incident Resolver
            
            Severity: {incident.get('severity', 'unknown').upper()}
            Resource: {incident.get('resource', {}).get('type', 'Unknown')}
            Anomalies Detected: {len(incident.get('anomalies', []))}
            
            Automated diagnosis in progress...
            """,
            "color": "warning"
        }
    
    def _format_diagnosis_message(self, diagnosis):
        """Format diagnosis notification message"""
        incident_id = diagnosis.get('incident_id') or diagnosis.get('id', 'Unknown')
        return {
            "title": f"[INFO] Diagnosis Complete: {incident_id}",
            "text": f"""
            Root Cause Identified
            
            Issue: {diagnosis.get('root_cause', {}).get('description', 'Unknown')}
            Confidence: {diagnosis.get('confidence', 0)}%
            Affected Services: {', '.join(diagnosis.get('impact', {}).get('affected_services', []))}
            
            Automated resolution in progress...
            """,
            "color": "info"
        }
    
    def _format_resolution_message(self, resolution):
        """Format resolution notification message"""
        incident_id = resolution.get('incident_id') or resolution.get('id', 'Unknown')
        status = resolution.get('status', 'unknown')
        color = "good" if status == "resolved" else "danger"
        
        return {
            "title": f"[SUCCESS] Resolution {'Complete' if status == 'resolved' else 'Failed'}: {incident_id}",
            "text": f"""
            Status: {status.upper()}
            
            Immediate Fix: {resolution.get('immediate_fix', {}).get('action', 'None')}
            Permanent Fix PR: {resolution.get('pr_url', 'Not created')}
            
            Post-mortem will be generated shortly.
            """,
            "color": color
        }
    
    def _build_timeline(self, incident_data):
        """Build incident timeline"""
        timeline = []
        
        if "detected_at" in incident_data:
            timeline.append({
                "time": incident_data["detected_at"],
                "event": "Incident detected",
                "agent": "Detection Agent"
            })
        
        if "diagnosis" in incident_data and "diagnosed_at" in incident_data["diagnosis"]:
            timeline.append({
                "time": incident_data["diagnosis"]["diagnosed_at"],
                "event": "Root cause identified",
                "agent": "Diagnosis Agent"
            })
        
        if "resolution" in incident_data and "resolved_at" in incident_data["resolution"]:
            timeline.append({
                "time": incident_data["resolution"]["resolved_at"],
                "event": "Incident resolved",
                "agent": "Resolution Agent"
            })
        
        return timeline
    
    def _generate_lessons_learned(self, incident_data):
        """Generate lessons learned from incident"""
        # TODO: Use AI to generate insights
        
        return [
            "Connection pool limits were too low for peak traffic",
            "Monitoring alerts should trigger earlier",
            "Similar incident occurred 2 weeks ago - pattern emerging"
        ]
    
    def _generate_action_items(self, incident_data):
        """Generate action items to prevent future incidents"""
        # TODO: Use AI to generate actionable items
        
        return [
            {
                "action": "Review and increase connection pool limits",
                "owner": "Backend Team",
                "priority": "high"
            },
            {
                "action": "Implement connection pool monitoring dashboard",
                "owner": "SRE Team",
                "priority": "medium"
            }
        ]
    
    async def _save_to_incident_database(self, post_mortem):
        """Save post-mortem to database for future RAG queries"""
        # TODO: Save to vector database for Microsoft Foundry
        print(f"[Communication Agent] Saving to incident database: {post_mortem['incident_id']}")
    
    async def _send_post_mortem(self, post_mortem):
        """Send post-mortem to stakeholders"""
        # TODO: Format and send comprehensive post-mortem
        print(f"[Communication Agent] Sending post-mortem: {post_mortem['incident_id']}")
    
    async def _send_teams_message(self, message):
        """Send message to Microsoft Teams"""
        # TODO: Implement Teams webhook integration
        print(f"[Communication Agent] Sending Teams message: {message.get('title', 'Notification')}")
        await asyncio.sleep(0.5)  # Simulate API call
    
    async def _send_slack_message(self, message):
        """Send message to Slack"""
        # TODO: Implement Slack webhook integration
        print(f"[Communication Agent] Sending Slack message: {message.get('title', 'Notification')}")
        await asyncio.sleep(0.5)  # Simulate API call
    
    async def start_listening(self):
        """Start listening for resolution messages from resolution agent"""
        if not self.servicebus_connection_string:
            print("[Communication Agent] ⚠️  AZURE_SERVICEBUS_CONNECTION_STRING not set")
            return
        
        self.is_listening = True
        print(f"[Communication Agent] [INFO] Starting to listen for messages on queue: {self.input_queue_name}")
        
        try:
            async with AsyncServiceBusClient.from_connection_string(
                self.servicebus_connection_string
            ) as client:
                async with client.get_queue_receiver(self.input_queue_name) as receiver:
                    while self.is_listening:
                        try:
                            messages = await receiver.receive_messages(max_message_count=1, max_wait_time=5)
                            
                            for message in messages:
                                # Parse resolution data
                                resolution_data = json.loads(str(message))
                                print(f"[Communication Agent] [INFO] Received resolution: {resolution_data['incident_id']}")
                                
                                # Build full incident data for notification
                                incident_data = {
                                    "incident_id": resolution_data['incident_id'],
                                    "resolution": resolution_data,
                                    "phase": "resolved" if resolution_data.get('status') == "resolved" else "failed"
                                }
                                
                                # Handle lifecycle notifications
                                await self.handle_incident_lifecycle(incident_data)
                                
                                # Generate post-mortem if resolved
                                if resolution_data.get('status') == "resolved":
                                    await self.generate_post_mortem(incident_data)
                                
                                # Complete the message
                                await receiver.complete_message(message)
                                
                        except asyncio.TimeoutError:
                            continue
                        except json.JSONDecodeError as e:
                    print(f"[Communication Agent] [ERROR] Failed to parse message: {e}")
                            
        except Exception as e:
            print(f"[Communication Agent] [ERROR] Error listening for messages: {e}")


# Main execution for testing
if __name__ == "__main__":
    agent = CommunicationAgent()
    
    # Option 1: Listen for messages from resolution agent
    try:
        asyncio.run(agent.start_listening())
    except KeyboardInterrupt:
        print("\n[Communication Agent] Shutting down gracefully...")
        agent.is_listening = False
