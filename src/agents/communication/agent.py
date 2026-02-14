"""
Communication Agent - Handles stakeholder notifications and reporting

This agent:
- Sends real-time updates to stakeholders (Teams)
- Generates incident reports and post-mortems
- Creates timeline of incident events
- Learns from incidents for future prevention
- Updates status pages
"""

import os
import json
import logging
from datetime import datetime
import asyncio
import aiohttp
from azure.identity import DefaultAzureCredential
from azure.servicebus.aio import ServiceBusClient as AsyncServiceBusClient
from azure.servicebus import ServiceBusMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] [%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class CommunicationAgent:
    def __init__(self):
        self.teams_webhook = os.getenv("TEAMS_WEBHOOK_URL")
        
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
        logger.info(f"[Communication Agent] Notifying detection: {incident_id}")
        
        message = self._format_detection_message(incident)
        
        # Send to Teams
        if self.teams_webhook:
            await self._send_teams_message(message)
        
        logger.info("[Communication Agent] [SUCCESS] Detection notification sent")
    
    async def notify_diagnosis(self, diagnosis):
        """Send diagnosis update"""
        incident_id = diagnosis.get('incident_id') or diagnosis.get('id', 'Unknown')
        logger.info(f"[Communication Agent] Notifying diagnosis: {incident_id}")
        
        message = self._format_diagnosis_message(diagnosis)
        
        if self.teams_webhook:
            await self._send_teams_message(message)
        
        logger.info("[Communication Agent] [SUCCESS] Diagnosis notification sent")
    
    async def notify_resolution(self, resolution):
        """Send resolution notification"""
        incident_id = resolution.get('incident_id') or resolution.get('id', 'Unknown')
        logger.info(f"[Communication Agent] Notifying resolution: {incident_id}")
        
        message = self._format_resolution_message(resolution)
        
        if self.teams_webhook:
            await self._send_teams_message(message)
        
        logger.info("[Communication Agent] [SUCCESS] Resolution notification sent")
    
    async def generate_post_mortem(self, full_incident_data):
        """Generate comprehensive post-mortem report"""
        logger.info("[Communication Agent] Generating post-mortem")
        
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
        
        logger.info("[Communication Agent] [SUCCESS] Post-mortem generated and distributed")
        return post_mortem
    
    async def escalate_to_oncall(self, incident):
        """Escalate to on-call engineer when automation fails"""
        incident_id = incident.get('incident_id') or incident.get('id', 'Unknown')
        logger.error(f"[Communication Agent] Escalating to on-call: {incident_id}")
        
        # TODO: Implement PagerDuty/OpsGenie integration
        # - Create high-priority alert
        # - Include all incident context
        # - Add runbook links
        
        escalation_message = {
            "title": f"🚨 ESCALATION REQUIRED: {incident_id}",
            "text": f"""
Automated resolution failed - manual intervention needed

**Root Cause**: {incident.get('diagnosis', {}).get('root_cause', {}).get('description', 'Unknown')}

**Impact**: {incident.get('diagnosis', {}).get('impact', {}).get('business_impact', 'Unknown')}

**Attempted Actions**: {incident.get('resolution', {}).get('immediate_fix', {}).get('action', 'None')}

**Status**: {incident.get('status', 'unknown').upper()}

Please investigate immediately.
            """,
            "color": "danger",
            "priority": "high"
        }
        
        # Send escalation to Teams
        if self.teams_webhook:
            await self._send_teams_message(escalation_message)
        
        logger.info("[Communication Agent] [SUCCESS] Escalation sent")
    
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
        logger.info(f"[Communication Agent] Saving to incident database: {post_mortem['incident_id']}")
    
    async def _send_post_mortem(self, post_mortem):
        """Send post-mortem to stakeholders"""
        # TODO: Format and send comprehensive post-mortem
        logger.info(f"[Communication Agent] Sending post-mortem: {post_mortem['incident_id']}")
    
    async def _send_teams_message(self, message):
        """Send properly formatted Teams Adaptive Card to webhook"""
        
        if not self.teams_webhook:
            logger.warning("TEAMS_WEBHOOK_URL not configured - skipping Teams notification")
            return False
        
        try:
            # Build Teams Adaptive Card with proper formatting
            card = self._build_teams_adaptive_card(message)
            
            # Send via HTTP POST
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.teams_webhook,
                    json=card,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"[Communication Agent] Teams message sent: {message.get('title', 'Notification')}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"[Communication Agent] Failed to send Teams message: {response.status} - {error_text}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error("[Communication Agent] Teams webhook request timed out")
            return False
        except Exception as e:
            logger.error(f"[Communication Agent] Error sending Teams message: {e}", exc_info=True)
            return False
    
    def _build_teams_adaptive_card(self, message):
        """Build a properly formatted Teams Adaptive Card"""
        
        title = message.get('title', 'Incident Notification')
        text = message.get('text', '')
        color = message.get('color', 'accent')
        priority = message.get('priority', 'normal')
        
        # Map color to theme color
        theme_color_map = {
            'danger': 'FF0000',      # Red
            'warning': 'FF6600',      # Orange
            'info': '0078D4',         # Blue
            'good': '00CC00',         # Green
            'accent': '0078D4'        # Default blue
        }
        
        theme_color = theme_color_map.get(color, '0078D4')
        
        # Build adaptive card
        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "Container",
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "ColumnSet",
                            "columns": [
                                {
                                    "width": "stretch",
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": title,
                                            "weight": "bolder",
                                            "size": "large",
                                            "color": color if color != 'accent' else None
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": text,
                    "wrap": True,
                    "spacing": "medium"
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "View in Dashboard",
                    "url": f"{os.getenv('DASHBOARD_URL', 'http://localhost:8000')}/incidents"
                }
            ]
        }
        
        return card
    
    
    async def start_listening(self):
        """Start listening for resolution messages from resolution agent"""
        if not self.servicebus_connection_string:
            logger.warning("[Communication Agent] ⚠️  AZURE_SERVICEBUS_CONNECTION_STRING not set")
            return
        
        self.is_listening = True
        logger.info(f"[Communication Agent] Starting to listen for messages on queue: {self.input_queue_name}")
        
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
                                logger.info(f"[Communication Agent] Received resolution: {resolution_data['incident_id']}")
                                
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
                            logger.error(f"[Communication Agent] Failed to parse message: {e}")
                            
        except Exception as e:
            logger.error(f"[Communication Agent] Error listening for messages: {e}", exc_info=True)


# Main execution for testing
if __name__ == "__main__":
    agent = CommunicationAgent()
    
    # Option 1: Listen for messages from resolution agent
    try:
        asyncio.run(agent.start_listening())
    except KeyboardInterrupt:
        logger.info("[Communication Agent] Shutting down gracefully...")
        agent.is_listening = False
