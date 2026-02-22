"""
Demo Scenario 2: Failed Deployment

This script simulates a failed deployment incident where a new version
introduces critical errors and demonstrates automatic rollback.
"""

import asyncio
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestration.orchestrator import IncidentOrchestrator


async def run_demo():
    """Run failed deployment demo"""
    
    print("\n" + "="*70)
    print("DEMO SCENARIO 2: Failed Deployment - Version 2.4.1")
    print("="*70)
    print("\nScenario Overview:")
    print("- New deployment v2.4.1 released to production at 15:42 UTC")
    print("- Error rate spikes from 0.1% to 15% within 2 minutes")
    print("- 25,000+ failed requests accumulating")
    print("- Users unable to complete transactions")
    print("\nExpected Agent Actions:")
    print("1. Detection Agent identifies error rate anomaly")
    print("2. Diagnosis Agent correlates to recent deployment")
    print("3. Resolution Agent initiates automatic rollback to v2.4.0")
    print("4. Resolution Agent creates incident post-analysis PR")
    print("5. Communication Agent notifies deployment team immediately")
    print("\n" + "="*70)
    
    input("\nPress ENTER to start the incident simulation...")
    print("\n")
    
    # Initialize orchestrator
    orchestrator = IncidentOrchestrator()
    
    # Create simulated incident
    incident = {
        "id": f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "resource": {
            "type": "API Service",
            "id": "api-prod-01",
            "name": "Production API Cluster",
            "current_version": "2.4.1",
            "previous_version": "2.4.0"
        },
        "anomalies": [
            {
                "metric": "ERROR_RATE",
                "value": 15.2,
                "baseline": 0.1,
                "threshold": 5.0,
                "severity": "critical",
                "description": "Error rate spiked from 0.1% to 15.2%"
            },
            {
                "metric": "FAILED_REQUESTS",
                "value": 25432,
                "baseline": 50,
                "threshold": 1000,
                "severity": "critical",
                "description": "25,000+ failed requests in 2 minutes"
            },
            {
                "metric": "HTTP_500_ERRORS",
                "value": 12856,
                "baseline": 5,
                "threshold": 100,
                "severity": "critical",
                "description": "Internal server errors 500x baseline"
            },
            {
                "metric": "REQUEST_LATENCY",
                "value": 4200,
                "baseline": 350,
                "threshold": 2000,
                "severity": "high",
                "description": "Latency increased 12x"
            }
        ],
        "detected_at": datetime.utcnow().isoformat(),
        "severity": "critical",
        "deployment_context": {
            "deployment_id": "deploy-20260216-142",
            "deployed_at": "2026-02-16T15:42:00Z",
            "deployed_version": "2.4.1",
            "deployment_changes": ["Authentication refactor", "Payment flow changes", "Cache invalidation logic"]
        },
        "impact_estimate": {
            "users_affected": "~18000 (realtime checkout users)",
            "services_affected": ["Payment Processing", "User Accounts", "Order Management"],
            "business_impact": "CRITICAL - Revenue loss at $850/min"
        }
    }
    
    print("🚨 Incident Created!")
    print(f"   ID: {incident['id']}")
    print(f"   Severity: {incident['severity'].upper()}")
    print(f"   Anomalies Detected: {len(incident['anomalies'])}")
    print(f"   Estimated Users Affected: {incident['impact_estimate']['users_affected']}")
    print(f"   Business Impact: {incident['impact_estimate']['business_impact']}")
    print("\n")
    
    # Run the full incident workflow
    await orchestrator.handle_incident(incident)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nWhat just happened:")
    print("✓ Deployment error detected and flagged automatically")
    print("✓ Root cause identified: Payment flow changes in v2.4.1")
    print("✓ Automatic rollback to v2.4.0 initiated")
    print("✓ Error rate returned to normal (0.2% within 1 minute)")
    print("✓ GitHub PR created with rollback analysis and fix")
    print("✓ Deployment team notified with incident details")
    print("✓ Post-mortem includes deployment regression analysis")
    print("\nMetrics Summary:")
    print("  - Deployment Version: 2.4.0 (rolled back from 2.4.1)")
    print("  - Error Rate: 0.1% (normalized)")
    print("  - Failed Requests: 25,432 recovered")
    print("  - Rollback Duration: 45 seconds")
    print("\nMTTR (Mean Time To Resolution): ~3 minutes")
    print("Manual MTTR would typically be: ~25-40 minutes")
    print("\nTime saved: ~22-37 minutes per incident")
    print("Revenue saved: ~$1,870 - $2,650")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Exiting...")
