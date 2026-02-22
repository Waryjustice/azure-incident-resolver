"""
Demo Scenario 8: Slow Query - Missing Index

This script simulates a database performance degradation due to missing
indexes and demonstrates automatic index creation.
"""

import asyncio
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestration.orchestrator import IncidentOrchestrator


async def run_demo():
    """Run slow query demo"""
    
    print("\n" + "="*70)
    print("DEMO SCENARIO 8: Slow Database Query - Missing Index")
    print("="*70)
    print("\nScenario Overview:")
    print("- Critical query now taking 35 seconds (normally 0.8 seconds)")
    print("- Query is full table scan on 50M row table")
    print("- Missing index causing 44x performance degradation")
    print("- Database CPU spiking to 85% due to scan queries")
    print("- 8,000+ queries queued waiting for completion")
    print("\nExpected Agent Actions:")
    print("1. Detection Agent identifies query slowness")
    print("2. Diagnosis Agent analyzes execution plan and finds missing index")
    print("3. Resolution Agent creates required index automatically")
    print("4. Resolution Agent creates PR documenting index changes")
    print("5. Communication Agent notifies database team")
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
            "id": "db-prod-analytics",
            "name": "Production Analytics Database",
            "engine": "SQL Server 2019",
            "edition": "Standard"
        },
        "anomalies": [
            {
                "metric": "QUERY_DURATION_SECONDS",
                "value": 35.2,
                "baseline": 0.8,
                "threshold": 5.0,
                "severity": "critical",
                "description": "Query taking 35.2s (normally 0.8s)"
            },
            {
                "metric": "TABLE_ROWS",
                "value": 50000000,
                "baseline": 50000000,
                "threshold": 50000000,
                "severity": "info",
                "description": "50M row table being scanned"
            },
            {
                "metric": "DATABASE_CPU_PERCENT",
                "value": 85.4,
                "baseline": 42.1,
                "threshold": 70.0,
                "severity": "critical",
                "description": "Database CPU at 85% due to full scans"
            },
            {
                "metric": "QUERIES_BLOCKED",
                "value": 8247,
                "baseline": 5,
                "threshold": 100,
                "severity": "critical",
                "description": "8247 queries queued behind slow query"
            }
        ],
        "detected_at": datetime.utcnow().isoformat(),
        "severity": "critical",
        "query_context": {
            "slow_query": "SELECT * FROM CustomerActivity WHERE DateCreated >= @startDate AND UserId IN (SELECT UserId FROM ActiveSessions)",
            "execution_plan": "Table Scan (CustomerActivity)",
            "current_indexes": ["PK_CustomerActivity_Id"],
            "missing_indexes": [
                {
                    "name": "IX_CustomerActivity_DateCreated",
                    "columns": ["DateCreated", "UserId"],
                    "expected_improvement": "98.7%"
                }
            ],
            "query_execution_count": 847,
            "queries_blocked_count": 8247
        },
        "impact_estimate": {
            "users_affected": "Indirect - analytics and reporting users",
            "services_affected": ["Analytics Dashboard", "Reports API", "Data Export"],
            "business_impact": "HIGH - Report generation stalled, business intelligence delayed"
        }
    }
    
    print("🚨 Incident Created!")
    print(f"   ID: {incident['id']}")
    print(f"   Severity: {incident['severity'].upper()}")
    print(f"   Anomalies Detected: {len(incident['anomalies'])}")
    print(f"   Slow Query Duration: {incident['anomalies'][0]['value']}s (baseline: 0.8s)")
    print(f"   Table Size: {incident['anomalies'][1]['value'] / 1000000}M rows")
    print(f"   Database CPU: {incident['anomalies'][2]['value']}%")
    print(f"   Queries Blocked: {incident['anomalies'][3]['value']}")
    print("\n")
    
    # Run the full incident workflow
    await orchestrator.handle_incident(incident)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nWhat just happened:")
    print("✓ Slow query detected via monitoring")
    print("✓ Query execution plan analyzed")
    print("✓ Root cause identified: Missing index on DateCreated + UserId")
    print("✓ Index automatically created on CustomerActivity table")
    print("✓ Query recompiled and reexecuted")
    print("✓ Query duration reduced to 0.6 seconds (98.3% improvement)")
    print("✓ Database CPU returned to 42%")
    print("✓ GitHub PR created with index creation script")
    print("✓ Database team notified with query analysis")
    print("✓ Post-mortem includes index strategy analysis")
    print("\nMetrics Summary:")
    print("  - Query Duration: 35.2s → 0.6s (98.3% improvement)")
    print("  - Table Rows: 50,000,000 (unchanged)")
    print("  - Database CPU: 85.4% → 42.1%")
    print("  - Queries Blocked: 8,247 → 5")
    print("  - Index Created: IX_CustomerActivity_DateCreated")
    print("  - Execution Plan: Table Scan → Index Seek")
    print("  - Resolution Duration: 6 minutes")
    print("\nMTTR (Mean Time To Resolution): ~6 minutes")
    print("Manual MTTR would typically be: ~45-90 minutes")
    print("(includes DBA analysis, testing, deployment approval)")
    print("\nTime saved: ~39-84 minutes per incident")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Exiting...")
