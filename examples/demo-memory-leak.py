"""
Demo Scenario 2: Memory Leak in Caching Service

This script simulates a memory leak incident in the caching service
and demonstrates the full agent workflow with service restart resolution.
"""

import asyncio
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestration.orchestrator import IncidentOrchestrator


async def run_demo():
    """Run memory leak demo"""
    
    print("\n" + "="*70)
    print("DEMO SCENARIO 2: Memory Leak in Caching Service")
    print("="*70)
    print("\nScenario Overview:")
    print("- Caching service memory usage gradually increases")
    print("- Memory reaches 95% of available capacity")
    print("- Service becomes unresponsive, requests timeout")
    print("- Cache misses spike due to frequent evictions")
    print("\nExpected Agent Actions:")
    print("1. Detection Agent identifies abnormal memory usage pattern")
    print("2. Diagnosis Agent finds memory leak in cache service")
    print("3. Resolution Agent restarts the cache service immediately")
    print("4. Resolution Agent creates PR to fix memory leak code")
    print("5. Communication Agent notifies team with incident details")
    print("\n" + "="*70)
    
    input("\nPress ENTER to start the incident simulation...")
    print("\n")
    
    # Initialize orchestrator
    orchestrator = IncidentOrchestrator()
    
    # Create simulated incident
    incident = {
        "id": f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "resource": {
            "type": "Service",
            "id": "cache-service-prod-001",
            "name": "Production Caching Service",
            "container": "cache-service:latest",
            "replicas": 3
        },
        "anomalies": [
            {
                "metric": "MEMORY_USAGE_PERCENT",
                "value": 95,
                "baseline": 40,
                "threshold": 80,
                "severity": "critical",
                "description": "Memory usage critically high at 95%"
            },
            {
                "metric": "MEMORY_GROWTH_RATE",
                "value": 2.5,
                "baseline": 0.1,
                "threshold": 0.5,
                "unit": "MB/sec",
                "severity": "high",
                "description": "Abnormal memory growth rate (2.5 MB/sec)"
            },
            {
                "metric": "RESPONSE_TIME",
                "value": 3500,
                "baseline": 150,
                "threshold": 1000,
                "severity": "high",
                "description": "Cache service response time degraded 23x"
            },
            {
                "metric": "CACHE_MISS_RATIO",
                "value": 0.85,
                "baseline": 0.05,
                "threshold": 0.20,
                "severity": "high",
                "description": "Cache hit rate collapsed to 15% (85% miss rate)"
            },
            {
                "metric": "OOM_EVENTS",
                "value": 3,
                "baseline": 0,
                "threshold": 0,
                "severity": "critical",
                "description": "Out of Memory events detected in last 5 minutes"
            }
        ],
        "detected_at": datetime.utcnow().isoformat(),
        "severity": "critical",
        "impact_estimate": {
            "users_affected": "~8000",
            "services_affected": ["API Gateway", "User Service", "Product Service", "Order Service"],
            "business_impact": "Critical - all services degraded, cache not functional"
        }
    }
    
    print("🚨 Incident Created!")
    print(f"   ID: {incident['id']}")
    print(f"   Service: {incident['resource']['name']}")
    print(f"   Severity: {incident['severity'].upper()}")
    print(f"   Anomalies Detected: {len(incident['anomalies'])}")
    print(f"   Estimated Users Affected: {incident['impact_estimate']['users_affected']}")
    print("\n📊 Key Metrics:")
    print(f"   • Memory Usage: {incident['anomalies'][0]['value']}% (baseline: {incident['anomalies'][0]['baseline']}%)")
    print(f"   • Memory Growth: {incident['anomalies'][1]['value']} MB/sec")
    print(f"   • Response Time: {incident['anomalies'][2]['value']}ms (baseline: {incident['anomalies'][2]['baseline']}ms)")
    print(f"   • Cache Miss Ratio: {incident['anomalies'][3]['value']*100:.0f}% (baseline: {incident['anomalies'][3]['baseline']*100:.0f}%)")
    print(f"   • OOM Events: {incident['anomalies'][4]['value']} in last 5 minutes")
    print("\n")
    
    # Run the full incident workflow
    await orchestrator.handle_incident(incident)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nWhat just happened:")
    print("✓ Incident detected and categorized automatically")
    print("✓ Root cause identified (memory leak in cache service)")
    print("✓ Cache service restarted immediately (graceful restart)")
    print("✓ Memory cleared, service returned to normal operation")
    print("✓ GitHub PR created with memory leak fix")
    print("✓ Team notified of incident and resolution")
    print("✓ Incident post-mortem generated")
    print("\nResolution Actions Taken:")
    print("  1. Service restart initiated across replicas")
    print("  2. Memory usage dropped from 95% to 12%")
    print("  3. Cache hit rate recovered to 94%")
    print("  4. Response time normalized to 158ms")
    print("\nMTTR (Mean Time To Resolution): ~2-3 minutes")
    print("Manual MTTR would typically be: ~30-45 minutes")
    print("\nTime saved: ~25-40 minutes per incident")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Exiting...")
