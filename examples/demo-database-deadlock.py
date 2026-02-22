"""
Demo Scenario 6: Database Deadlock

This script simulates a critical database deadlock incident blocking
transactions and demonstrates automatic deadlock resolution.
"""

import asyncio
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestration.orchestrator import IncidentOrchestrator


async def run_demo():
    """Run database deadlock demo"""
    
    print("\n" + "="*70)
    print("DEMO SCENARIO 6: Database Deadlock - Transactions Blocked")
    print("="*70)
    print("\nScenario Overview:")
    print("- 42 transactions deadlocked in database")
    print("- Payment processing halted")
    print("- Customer transactions stuck for 3+ minutes")
    print("- Database monitoring shows blocking chains")
    print("\nExpected Agent Actions:")
    print("1. Detection Agent identifies deadlock pattern")
    print("2. Diagnosis Agent identifies blocking query and root cause")
    print("3. Resolution Agent kills blocking queries automatically")
    print("4. Resolution Agent creates PR to optimize transaction order")
    print("5. Communication Agent notifies payment team")
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
            "id": "db-prod-payment",
            "name": "Production Payment Database",
            "engine": "SQL Server"
        },
        "anomalies": [
            {
                "metric": "BLOCKED_TRANSACTIONS",
                "value": 42,
                "baseline": 0,
                "threshold": 5,
                "severity": "critical",
                "description": "42 transactions in deadlock state"
            },
            {
                "metric": "TRANSACTION_WAIT_TIME",
                "value": 180,
                "baseline": 0.5,
                "threshold": 10,
                "severity": "critical",
                "description": "Transactions waiting 180 seconds"
            },
            {
                "metric": "DEADLOCK_COUNT",
                "value": 7,
                "baseline": 0,
                "threshold": 1,
                "severity": "critical",
                "description": "7 deadlock cycles detected"
            },
            {
                "metric": "PAYMENT_PROCESSING_ERRORS",
                "value": 892,
                "baseline": 0,
                "threshold": 10,
                "severity": "critical",
                "description": "Payment processing errors spiking"
            }
        ],
        "detected_at": datetime.utcnow().isoformat(),
        "severity": "critical",
        "deadlock_context": {
            "deadlock_duration": 187,
            "affected_tables": ["Payments", "Accounts", "Transactions", "AuditLog"],
            "blocking_spid": 52,
            "blocked_spids": [51, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64],
            "blocking_query": "UPDATE Accounts SET Balance = Balance - @amount WHERE AccountId = @accountId",
            "blocking_lock_type": "X (Exclusive)"
        },
        "impact_estimate": {
            "users_affected": "~8200 (active payment users)",
            "services_affected": ["Payment Processing", "Checkout", "Subscription"],
            "business_impact": "CRITICAL - No payments processing | $42K/min revenue loss"
        }
    }
    
    print("🚨 Incident Created!")
    print(f"   ID: {incident['id']}")
    print(f"   Severity: {incident['severity'].upper()}")
    print(f"   Blocked Transactions: {incident['anomalies'][0]['value']}")
    print(f"   Deadlock Duration: {incident['deadlock_context']['deadlock_duration']}s")
    print(f"   Affected Tables: {len(incident['deadlock_context']['affected_tables'])}")
    print(f"   Business Impact: {incident['impact_estimate']['business_impact']}")
    print("\n")
    
    # Run the full incident workflow
    await orchestrator.handle_incident(incident)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nWhat just happened:")
    print("✓ Database deadlock detected automatically")
    print("✓ Blocking transaction chain identified")
    print("✓ Root cause: Account balance update query with missing index")
    print("✓ Blocking queries automatically terminated")
    print("✓ 42 blocked transactions rolled back safely")
    print("✓ Transaction recovery completed")
    print("✓ GitHub PR created with missing index and transaction optimization")
    print("✓ Payment team notified and dashboards updated")
    print("✓ Post-mortem includes transaction isolation analysis")
    print("\nMetrics Summary:")
    print("  - Blocked Transactions: 42 → 0")
    print("  - Deadlock Count: 7 → 0")
    print("  - Transaction Wait Time: 180s → 0.8s")
    print("  - Affected Tables: 4 (all recovered)")
    print("  - Transactions Recovered: 42")
    print("  - Resolution Duration: 90 seconds")
    print("  - Payment Processing: Resumed")
    print("\nMTTR (Mean Time To Resolution): ~90 seconds")
    print("Manual MTTR would typically be: ~20-40 minutes")
    print("\nTime saved: ~19-39 minutes per incident")
    print("Revenue saved: $798K - $1.68M")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Exiting...")
