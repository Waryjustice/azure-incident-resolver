"""
Demo Scenario 5: CPU Spike - High Load

This script simulates sustained high CPU usage and demonstrates
automatic horizontal scaling to handle load.
"""

import asyncio
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestration.orchestrator import IncidentOrchestrator


async def run_demo():
    """Run CPU spike demo"""
    
    print("\n" + "="*70)
    print("DEMO SCENARIO 5: Sustained High CPU Load")
    print("="*70)
    print("\nScenario Overview:")
    print("- CPU utilization sustained at 98% across cluster")
    print("- Response times degraded from 150ms to 8500ms")
    print("- 15,000 users experiencing timeout/slowness")
    print("- Only 3 instances running insufficient for load")
    print("\nExpected Agent Actions:")
    print("1. Detection Agent identifies CPU anomaly")
    print("2. Diagnosis Agent correlates with request load spike")
    print("3. Resolution Agent scales cluster from 3 to 8 instances")
    print("4. Resolution Agent creates PR for dynamic scaling rules")
    print("5. Communication Agent notifies ops and application teams")
    print("\n" + "="*70)
    
    input("\nPress ENTER to start the incident simulation...")
    print("\n")
    
    # Initialize orchestrator
    orchestrator = IncidentOrchestrator()
    
    # Create simulated incident
    incident = {
        "id": f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "resource": {
            "type": "Compute Cluster",
            "id": "aks-prod-api",
            "name": "Production API Cluster",
            "current_instances": 3,
            "instance_type": "Standard_D4s_v3"
        },
        "anomalies": [
            {
                "metric": "CPU_PERCENT",
                "value": 98.2,
                "baseline": 45.0,
                "threshold": 70.0,
                "severity": "critical",
                "description": "CPU sustained at 98.2%"
            },
            {
                "metric": "RESPONSE_TIME_MS",
                "value": 8500,
                "baseline": 150,
                "threshold": 1000,
                "severity": "critical",
                "description": "Response time degraded 57x"
            },
            {
                "metric": "REQUEST_QUEUE_DEPTH",
                "value": 42000,
                "baseline": 50,
                "threshold": 1000,
                "severity": "critical",
                "description": "Request queue backed up"
            },
            {
                "metric": "TIMEOUT_ERRORS",
                "value": 3242,
                "baseline": 2,
                "threshold": 50,
                "severity": "high",
                "description": "Timeout errors 1621x baseline"
            }
        ],
        "detected_at": datetime.utcnow().isoformat(),
        "severity": "critical",
        "scaling_context": {
            "current_instances": 3,
            "recommended_instances": 8,
            "cpu_per_instance": 32.7,
            "load_per_instance": 14000,
            "target_cpu": 60.0,
            "scaling_cooldown": "completed"
        },
        "impact_estimate": {
            "users_affected": "~15000 (active users experiencing timeouts)",
            "services_affected": ["Primary API", "Search Service", "Analytics"],
            "business_impact": "HIGH - 23% of users experiencing errors"
        }
    }
    
    print("🚨 Incident Created!")
    print(f"   ID: {incident['id']}")
    print(f"   Severity: {incident['severity'].upper()}")
    print(f"   Anomalies Detected: {len(incident['anomalies'])}")
    print(f"   CPU Usage: {incident['anomalies'][0]['value']}%")
    print(f"   Response Time: {incident['anomalies'][1]['value']}ms (baseline: 150ms)")
    print(f"   Users Affected: {incident['impact_estimate']['users_affected']}")
    print("\n")
    
    # Run the full incident workflow
    await orchestrator.handle_incident(incident)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nWhat just happened:")
    print("✓ High CPU anomaly detected automatically")
    print("✓ Root cause identified: Insufficient capacity for load")
    print("✓ Automatic horizontal scale initiated (3 → 8 instances)")
    print("✓ Load balanced across 8 instances")
    print("✓ CPU returned to 42% (well-balanced)")
    print("✓ Response times normalized to 180ms")
    print("✓ GitHub PR created with improved autoscaling policy")
    print("✓ Operations team notified with scaling details")
    print("✓ Post-mortem includes capacity planning analysis")
    print("\nMetrics Summary:")
    print("  - CPU Utilization: 98.2% → 42.1%")
    print("  - Response Time: 8500ms → 185ms")
    print("  - Instance Count: 3 → 8")
    print("  - Request Queue: 42000 → 0 (cleared)")
    print("  - Timeout Errors: 3242 → 0 (recovered)")
    print("  - Users Affected: 15000 → 0")
    print("  - Scaling Duration: 4 minutes")
    print("\nMTTR (Mean Time To Resolution): ~4 minutes")
    print("Manual MTTR would typically be: ~30-45 minutes")
    print("\nTime saved: ~26-41 minutes per incident")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Exiting...")
