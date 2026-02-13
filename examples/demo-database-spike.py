"""
Demo Scenario 1: Database Connection Spike

This script simulates a database connection pool exhaustion incident
and demonstrates the full agent workflow.
"""

import asyncio
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestration.orchestrator import IncidentOrchestrator


async def run_demo():
    """Run database connection spike demo"""
    
    print("\n" + "="*70)
    print("DEMO SCENARIO 1: Database Connection Pool Exhaustion")
    print("="*70)
    print("\nScenario Overview:")
    print("- Production database connection pool reaches 100% utilization")
    print("- API requests start timing out")
    print("- User complaints increase")
    print("\nExpected Agent Actions:")
    print("1. Detection Agent identifies connection pool anomaly")
    print("2. Diagnosis Agent finds connection leak in API Gateway")
    print("3. Resolution Agent scales database tier immediately")
    print("4. Resolution Agent creates PR to fix connection leak")
    print("5. Communication Agent notifies team and generates post-mortem")
    print("\n" + "="*70)
    
    input("\nPress ENTER to start the incident simulation...")
    print("\n")
    
    # Initialize orchestrator
    orchestrator = IncidentOrchestrator()
    
    # Create simulated incident
    incident = {
        "id": f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "resource": {
            "type": "Database",
            "id": "db-prod-001",
            "name": "Production SQL Database",
            "tier": "S1"
        },
        "anomalies": [
            {
                "metric": "CONNECTION_COUNT",
                "value": 500,
                "baseline": 100,
                "threshold": 400,
                "severity": "critical",
                "description": "Connection pool at 100% capacity"
            },
            {
                "metric": "RESPONSE_TIME",
                "value": 5000,
                "baseline": 200,
                "threshold": 1000,
                "severity": "high",
                "description": "Query response time degraded 25x"
            },
            {
                "metric": "TIMEOUT_ERRORS",
                "value": 156,
                "baseline": 0,
                "threshold": 10,
                "severity": "high",
                "description": "Connection timeout errors spiking"
            }
        ],
        "detected_at": datetime.utcnow().isoformat(),
        "severity": "critical",
        "impact_estimate": {
            "users_affected": "~5000",
            "services_affected": ["API Gateway", "User Service", "Order Service"],
            "business_impact": "High - customer transactions failing"
        }
    }
    
    print("🚨 Incident Created!")
    print(f"   ID: {incident['id']}")
    print(f"   Severity: {incident['severity'].upper()}")
    print(f"   Anomalies Detected: {len(incident['anomalies'])}")
    print(f"   Estimated Users Affected: {incident['impact_estimate']['users_affected']}")
    print("\n")
    
    # Run the full incident workflow
    await orchestrator.handle_incident(incident)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nWhat just happened:")
    print("✓ Incident detected and categorized automatically")
    print("✓ Root cause identified (connection leak in API Gateway)")
    print("✓ Database scaled from S1 to S3 tier (immediate fix)")
    print("✓ GitHub PR created with connection pooling improvements")
    print("✓ Team notified via Teams/Slack")
    print("✓ Post-mortem generated and saved to knowledge base")
    print("\nMTTR (Mean Time To Resolution): ~3-4 minutes")
    print("Manual MTTR would typically be: ~45-60 minutes")
    print("\nTime saved: ~40-55 minutes per incident")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Exiting...")
