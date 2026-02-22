"""
Demo Scenario 3: Disk Space Critical

This script simulates a disk space exhaustion incident where logs
are consuming most available storage and demonstrates automatic cleanup.
"""

import asyncio
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestration.orchestrator import IncidentOrchestrator


async def run_demo():
    """Run disk space critical demo"""
    
    print("\n" + "="*70)
    print("DEMO SCENARIO 3: Disk Space Critical")
    print("="*70)
    print("\nScenario Overview:")
    print("- Production server disk 95% full (only 2GB free)")
    print("- Log files consuming 450GB over 18 months")
    print("- Database autovacuum failing due to no space")
    print("- New transactions cannot be written")
    print("\nExpected Agent Actions:")
    print("1. Detection Agent identifies disk usage anomaly")
    print("2. Diagnosis Agent identifies logs as root cause")
    print("3. Resolution Agent runs log rotation and cleanup")
    print("4. Resolution Agent implements log retention policy via PR")
    print("5. Communication Agent notifies infrastructure team")
    print("\n" + "="*70)
    
    input("\nPress ENTER to start the incident simulation...")
    print("\n")
    
    # Initialize orchestrator
    orchestrator = IncidentOrchestrator()
    
    # Create simulated incident
    incident = {
        "id": f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "resource": {
            "type": "Storage Volume",
            "id": "prod-disk-001",
            "name": "Production Server Primary Disk",
            "total_capacity_gb": 500,
            "filesystem": "/dev/sda1"
        },
        "anomalies": [
            {
                "metric": "DISK_USAGE_PERCENT",
                "value": 95.8,
                "baseline": 62.5,
                "threshold": 85.0,
                "severity": "critical",
                "description": "Disk 95.8% full"
            },
            {
                "metric": "DISK_FREE_GB",
                "value": 2.1,
                "baseline": 150,
                "threshold": 20,
                "severity": "critical",
                "description": "Only 2.1GB free space remaining"
            },
            {
                "metric": "LOG_FILES_SIZE_GB",
                "value": 448.7,
                "baseline": 120,
                "threshold": 200,
                "severity": "critical",
                "description": "Log directory consuming 448.7GB"
            },
            {
                "metric": "DATABASE_WRITES_BLOCKED",
                "value": 1247,
                "baseline": 0,
                "threshold": 10,
                "severity": "critical",
                "description": "1247 failed database writes"
            }
        ],
        "detected_at": datetime.utcnow().isoformat(),
        "severity": "critical",
        "storage_context": {
            "total_disk_gb": 500,
            "used_disk_gb": 477.9,
            "free_disk_gb": 2.1,
            "largest_directory": "/var/log (448.7GB)",
            "log_age_range": "18 months - 48 hours ago"
        },
        "impact_estimate": {
            "users_affected": "All users if crash occurs",
            "services_affected": ["Database", "Log aggregation", "All APIs"],
            "business_impact": "CRITICAL - System crash imminent"
        }
    }
    
    print("🚨 Incident Created!")
    print(f"   ID: {incident['id']}")
    print(f"   Severity: {incident['severity'].upper()}")
    print(f"   Anomalies Detected: {len(incident['anomalies'])}")
    print(f"   Disk Usage: {incident['storage_context']['used_disk_gb']}GB / {incident['storage_context']['total_disk_gb']}GB")
    print(f"   Free Space: {incident['storage_context']['free_disk_gb']}GB")
    print("\n")
    
    # Run the full incident workflow
    await orchestrator.handle_incident(incident)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nWhat just happened:")
    print("✓ Disk usage anomaly detected automatically")
    print("✓ Root cause identified: Log files consuming 448.7GB")
    print("✓ Automatic log cleanup and rotation executed")
    print("✓ 380GB of old logs archived and compressed")
    print("✓ Disk usage dropped to 42% (210GB free)")
    print("✓ GitHub PR created with log retention policy")
    print("✓ Infrastructure team notified with storage report")
    print("✓ Post-mortem includes capacity planning recommendations")
    print("\nMetrics Summary:")
    print("  - Disk Usage: 95.8% → 42.1% (freed 380GB)")
    print("  - Free Space: 2.1GB → 210GB")
    print("  - Log Size: 448.7GB → 85.3GB (archived)")
    print("  - Files Cleaned: 24,847 old log files")
    print("  - Cleanup Duration: 2 minutes")
    print("\nMTTR (Mean Time To Resolution): ~2 minutes")
    print("Manual MTTR would typically be: ~30-45 minutes")
    print("System crash prevented")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Exiting...")
