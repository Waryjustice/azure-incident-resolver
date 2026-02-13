"""
Multi-Agent Orchestrator - Coordinates all agents in the system

This orchestrator:
- Manages agent lifecycle and communication
- Routes incidents between agents
- Implements Azure MCP for agent-to-agent communication
- Maintains incident state
- Provides monitoring and observability
"""

import asyncio
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.detection.agent import DetectionAgent
from agents.diagnosis.agent import DiagnosisAgent
from agents.resolution.agent import ResolutionAgent
from agents.communication.agent import CommunicationAgent


class IncidentOrchestrator:
    def __init__(self):
        # Initialize all agents
        self.detection_agent = DetectionAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.resolution_agent = ResolutionAgent()
        self.communication_agent = CommunicationAgent()
        
        # Incident state management
        self.active_incidents = {}
        self.incident_history = []
        
        print("[Orchestrator] 🚀 Azure Incident Resolver initialized")
        print("[Orchestrator] All agents ready")
    
    async def start(self):
        """Start the orchestration system"""
        print("[Orchestrator] Starting incident monitoring...")
        
        # Start detection agent monitoring in background
        detection_task = asyncio.create_task(self._run_detection_loop())
        
        # Keep the system running
        await detection_task
    
    async def _run_detection_loop(self):
        """Run continuous detection monitoring"""
        while True:
            try:
                # Check for new incidents
                await self.detection_agent.check_all_resources()
                
                # Wait before next check
                await asyncio.sleep(self.detection_agent.monitoring_interval)
                
            except Exception as e:
                print(f"[Orchestrator] Error in detection loop: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def handle_incident(self, incident):
        """
        Main incident handling workflow
        Coordinates all agents to detect → diagnose → resolve → communicate
        """
        incident_id = incident["id"]
        self.active_incidents[incident_id] = incident
        
        print(f"\n{'='*60}")
        print(f"[Orchestrator] 🚨 INCIDENT WORKFLOW STARTED: {incident_id}")
        print(f"{'='*60}\n")
        
        try:
            # Phase 1: Detection (already done, notify stakeholders)
            print("[Orchestrator] Phase 1/4: Detection")
            incident["phase"] = "detected"
            await self.communication_agent.handle_incident_lifecycle(incident)
            
            # Phase 2: Diagnosis
            print("\n[Orchestrator] Phase 2/4: Diagnosis")
            diagnosis = await self.diagnosis_agent.diagnose_incident(incident)
            
            if not diagnosis:
                print("[Orchestrator] ❌ Diagnosis failed - escalating")
                await self._handle_failure(incident, "diagnosis_failed")
                return
            
            incident["diagnosis"] = diagnosis
            diagnosis["phase"] = "diagnosed"
            await self.communication_agent.handle_incident_lifecycle(diagnosis)
            
            # Phase 3: Resolution
            print("\n[Orchestrator] Phase 3/4: Resolution")
            resolution = await self.resolution_agent.resolve_incident(diagnosis)
            
            if not resolution or resolution["status"] != "resolved":
                print("[Orchestrator] ❌ Resolution failed - escalating")
                await self._handle_failure(incident, "resolution_failed")
                return
            
            incident["resolution"] = resolution
            resolution["phase"] = "resolved"
            await self.communication_agent.handle_incident_lifecycle(resolution)
            
            # Phase 4: Post-incident communication
            print("\n[Orchestrator] Phase 4/4: Post-Incident Communication")
            await self.communication_agent.generate_post_mortem(incident)
            
            # Move to history
            incident["completed_at"] = datetime.utcnow().isoformat()
            incident["status"] = "resolved"
            self.incident_history.append(incident)
            del self.active_incidents[incident_id]
            
            print(f"\n{'='*60}")
            print(f"[Orchestrator] ✅ INCIDENT WORKFLOW COMPLETED: {incident_id}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"[Orchestrator] ❌ Unexpected error: {e}")
            await self._handle_failure(incident, f"unexpected_error: {e}")
    
    async def _handle_failure(self, incident, reason):
        """Handle workflow failures"""
        incident["status"] = "failed"
        incident["failure_reason"] = reason
        incident["phase"] = "failed"
        
        # Escalate to on-call
        await self.communication_agent.escalate_to_oncall(incident)
        
        # Move to history
        self.incident_history.append(incident)
        if incident["id"] in self.active_incidents:
            del self.active_incidents[incident["id"]]
    
    def get_active_incidents(self):
        """Get list of currently active incidents"""
        return list(self.active_incidents.values())
    
    def get_incident_history(self, limit=10):
        """Get recent incident history"""
        return self.incident_history[-limit:]
    
    def get_system_stats(self):
        """Get system statistics"""
        total_incidents = len(self.incident_history) + len(self.active_incidents)
        resolved_incidents = len([i for i in self.incident_history if i.get("status") == "resolved"])
        
        return {
            "active_incidents": len(self.active_incidents),
            "total_incidents": total_incidents,
            "resolved_incidents": resolved_incidents,
            "resolution_rate": (resolved_incidents / total_incidents * 100) if total_incidents > 0 else 0,
            "uptime": "Running"
        }


# Main execution
async def main():
    """Main entry point"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║           Azure Incident Resolver                          ║
    ║           Multi-Agent SRE System                           ║
    ║                                                            ║
    ║   Built for Microsoft AI Dev Days Hackathon 2026          ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    orchestrator = IncidentOrchestrator()
    
    # For testing: simulate an incident
    # In production, this would be triggered by the detection agent
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    
    if test_mode:
        print("\n[TEST MODE] Simulating incident in 5 seconds...\n")
        await asyncio.sleep(5)
        
        test_incident = {
            "id": f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "resource": {
                "type": "Database",
                "id": "db-prod-001",
                "name": "Production Database"
            },
            "anomalies": [
                {
                    "metric": "CONNECTION_COUNT",
                    "value": 500,
                    "threshold": 100,
                    "severity": "high"
                }
            ],
            "detected_at": datetime.utcnow().isoformat(),
            "severity": "high"
        }
        
        await orchestrator.handle_incident(test_incident)
        
        # Show stats
        stats = orchestrator.get_system_stats()
        print(f"\n\nSystem Statistics:")
        print(f"  Active Incidents: {stats['active_incidents']}")
        print(f"  Total Incidents: {stats['total_incidents']}")
        print(f"  Resolved: {stats['resolved_incidents']}")
        print(f"  Resolution Rate: {stats['resolution_rate']:.1f}%")
    else:
        # Start continuous monitoring
        await orchestrator.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[Orchestrator] Shutting down gracefully...")
        print("[Orchestrator] Goodbye! 👋")
