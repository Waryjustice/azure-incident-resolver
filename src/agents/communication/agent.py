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
from datetime import datetime
import asyncio


class CommunicationAgent:
    def __init__(self):
        self.teams_webhook = os.getenv("TEAMS_WEBHOOK_URL")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        
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
        print(f"[Communication Agent] 📢 Notifying detection: {incident['id']}")
        
        message = self._format_detection_message(incident)
        
        # Send to Teams
        if self.teams_webhook:
            await self._send_teams_message(message)
        
        # Send to Slack
        if self.slack_webhook:
            await self._send_slack_message(message)
        
        print("[Communication Agent] ✅ Detection notification sent")
    
    async def notify_diagnosis(self, diagnosis):
        """Send diagnosis update"""
        print(f"[Communication Agent] 📢 Notifying diagnosis: {diagnosis['incident_id']}")
        
        message = self._format_diagnosis_message(diagnosis)
        
        if self.teams_webhook:
            await self._send_teams_message(message)
        
        if self.slack_webhook:
            await self._send_slack_message(message)
        
        print("[Communication Agent] ✅ Diagnosis notification sent")
    
    async def notify_resolution(self, resolution):
        """Send resolution notification"""
        print(f"[Communication Agent] 📢 Notifying resolution: {resolution['incident_id']}")
        
        message = self._format_resolution_message(resolution)
        
        if self.teams_webhook:
            await self._send_teams_message(message)
        
        if self.slack_webhook:
            await self._send_slack_message(message)
        
        print("[Communication Agent] ✅ Resolution notification sent")
    
    async def generate_post_mortem(self, full_incident_data):
        """Generate comprehensive post-mortem report"""
        print(f"[Communication Agent] 📝 Generating post-mortem")
        
        # TODO: Use Azure OpenAI to generate comprehensive post-mortem
        # - Summarize timeline
        # - Analyze root cause
        # - Document lessons learned
        # - Create action items
        
        post_mortem = {
            "incident_id": full_incident_data["incident_id"],
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
        
        print("[Communication Agent] ✅ Post-mortem generated and distributed")
        return post_mortem
    
    async def escalate_to_oncall(self, incident):
        """Escalate to on-call engineer when automation fails"""
        print(f"[Communication Agent] 🚨 Escalating to on-call: {incident['incident_id']}")
        
        # TODO: Implement PagerDuty/OpsGenie integration
        # - Create high-priority alert
        # - Include all incident context
        # - Add runbook links
        
        escalation_message = f"""
        🚨 ESCALATION REQUIRED 🚨
        
        Incident: {incident['incident_id']}
        Automated resolution failed - manual intervention needed
        
        Details:
        - Root Cause: {incident.get('diagnosis', {}).get('root_cause', {}).get('description', 'Unknown')}
        - Impact: {incident.get('diagnosis', {}).get('impact', {}).get('business_impact', 'Unknown')}
        - Automated Actions Attempted: {incident.get('resolution', {}).get('immediate_fix', {}).get('action', 'None')}
        
        Please investigate immediately.
        """
        
        if self.teams_webhook:
            await self._send_teams_message({"text": escalation_message, "priority": "high"})
        
        print("[Communication Agent] ✅ Escalation sent")
    
    def _format_detection_message(self, incident):
        """Format detection notification message"""
        return {
            "title": f"🚨 Incident Detected: {incident['id']}",
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
        return {
            "title": f"🔍 Diagnosis Complete: {diagnosis['incident_id']}",
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
        status = resolution.get('status', 'unknown')
        color = "good" if status == "resolved" else "danger"
        
        return {
            "title": f"✅ Resolution {'Complete' if status == 'resolved' else 'Failed'}: {resolution['incident_id']}",
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


# Main execution for testing
if __name__ == "__main__":
    agent = CommunicationAgent()
    
    # Test incident data
    test_incident = {
        "incident_id": "INC-20260213120000",
        "detected_at": "2026-02-13T12:00:00Z",
        "diagnosis": {
            "root_cause": {"description": "Database connection pool exhausted"},
            "diagnosed_at": "2026-02-13T12:02:30Z",
            "confidence": 85,
            "impact": {"affected_services": ["API Gateway", "User Service"]}
        },
        "resolution": {
            "resolved_at": "2026-02-13T12:05:00Z",
            "status": "resolved",
            "immediate_fix": {"action": "scaled_database"},
            "pr_url": "https://github.com/example/repo/pull/123"
        }
    }
    
    asyncio.run(agent.generate_post_mortem(test_incident))
