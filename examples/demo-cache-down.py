"""
Demo Scenario 7: Redis Cache Down

This script simulates a Redis cache server failure and demonstrates
automatic restart, recovery, and scaling.
"""

import asyncio
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestration.orchestrator import IncidentOrchestrator


async def run_demo():
    """Run Redis cache down demo"""
    
    print("\n" + "="*70)
    print("DEMO SCENARIO 7: Redis Cache Failure - 100% Cache Miss")
    print("="*70)
    print("\nScenario Overview:")
    print("- Redis cache service crashes at 14:35 UTC")
    print("- Cache hit rate drops to 0% (100% cache miss)")
    print("- API latency spikes from 45ms to 3500ms")
    print("- 12,000+ concurrent users affected")
    print("- Database CPU explodes due to cache bypass queries")
    print("\nExpected Agent Actions:")
    print("1. Detection Agent identifies cache failure")
    print("2. Diagnosis Agent detects Redis service down")
    print("3. Resolution Agent restarts Redis service")
    print("4. Resolution Agent scales cache tier for burst traffic")
    print("5. Communication Agent notifies platform team")
    print("\n" + "="*70)
    
    input("\nPress ENTER to start the incident simulation...")
    print("\n")
    
    # Initialize orchestrator
    orchestrator = IncidentOrchestrator()
    
    # Create simulated incident
    incident = {
        "id": f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "resource": {
            "type": "Cache Service",
            "id": "redis-prod-01",
            "name": "Production Redis Cache",
            "tier": "Standard",
            "memory_gb": 16
        },
        "anomalies": [
            {
                "metric": "CACHE_HIT_RATE",
                "value": 0.0,
                "baseline": 87.5,
                "threshold": 50.0,
                "severity": "critical",
                "description": "Cache hit rate 0% (service down)"
            },
            {
                "metric": "CACHE_MISS_RATE",
                "value": 100.0,
                "baseline": 12.5,
                "threshold": 40.0,
                "severity": "critical",
                "description": "100% cache misses"
            },
            {
                "metric": "API_LATENCY_MS",
                "value": 3500,
                "baseline": 45,
                "threshold": 500,
                "severity": "critical",
                "description": "Latency spiked 78x without cache"
            },
            {
                "metric": "REDIS_MEMORY_MB",
                "value": 0,
                "baseline": 14200,
                "threshold": 1000,
                "severity": "critical",
                "description": "Redis memory dropped to 0 (service offline)"
            }
        ],
        "detected_at": datetime.utcnow().isoformat(),
        "severity": "critical",
        "cache_context": {
            "service_status": "DOWN",
            "service_uptime": 0,
            "crash_timestamp": "2026-02-16T14:35:22Z",
            "error_log": "Redis server terminated unexpectedly: OOM killer process",
            "memory_pressure": "Host memory at 98%"
        },
        "impact_estimate": {
            "users_affected": "~12000 (active users)",
            "services_affected": ["Session Cache", "Data Cache", "Rate Limit Store", "Analytics"],
            "business_impact": "CRITICAL - Performance degraded 78x | $15K/min revenue loss"
        }
    }
    
    print("🚨 Incident Created!")
    print(f"   ID: {incident['id']}")
    print(f"   Severity: {incident['severity'].upper()}")
    print(f"   Cache Hit Rate: {incident['anomalies'][0]['value']}% (baseline: 87.5%)")
    print(f"   API Latency: {incident['anomalies'][2]['value']}ms (baseline: 45ms)")
    print(f"   Users Affected: {incident['impact_estimate']['users_affected']}")
    print(f"   Business Impact: {incident['impact_estimate']['business_impact']}")
    print("\n")
    
    # Run the full incident workflow
    await orchestrator.handle_incident(incident)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nWhat just happened:")
    print("✓ Cache service failure detected immediately")
    print("✓ Root cause identified: OOM (Out of Memory) killer")
    print("✓ Redis service restarted automatically")
    print("✓ Cache tier scaled from Standard to Premium (64GB)")
    print("✓ Cache warmed up with hot keys")
    print("✓ Cache hit rate recovered to 85%")
    print("✓ API latency normalized to 52ms")
    print("✓ GitHub PR created with memory optimization")
    print("✓ Platform team notified with incident metrics")
    print("✓ Post-mortem includes cache policy and memory tuning")
    print("\nMetrics Summary:")
    print("  - Cache Hit Rate: 0% → 85%")
    print("  - Cache Miss Rate: 100% → 15%")
    print("  - API Latency: 3500ms → 52ms")
    print("  - Redis Memory: 0MB → 42100MB (recovered)")
    print("  - Users Affected: 12000 → 0")
    print("  - Cache Tier: Standard (16GB) → Premium (64GB)")
    print("  - Recovery Duration: 2 minutes")
    print("\nMTTR (Mean Time To Resolution): ~2 minutes")
    print("Manual MTTR would typically be: ~35-50 minutes")
    print("\nTime saved: ~33-48 minutes per incident")
    print("Revenue saved: $495K - $720K")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Exiting...")
