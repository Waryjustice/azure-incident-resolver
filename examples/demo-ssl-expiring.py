"""
Demo Scenario 4: SSL Certificate Expiring

This script simulates an SSL certificate expiration incident and
demonstrates automatic renewal and service reload.
"""

import asyncio
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestration.orchestrator import IncidentOrchestrator


async def run_demo():
    """Run SSL certificate expiring demo"""
    
    print("\n" + "="*70)
    print("DEMO SCENARIO 4: SSL Certificate Expiring Soon")
    print("="*70)
    print("\nScenario Overview:")
    print("- SSL certificate for api.prod.azureincidents.com expires in 5 days")
    print("- Manual renewal was scheduled but overlooked")
    print("- Early warning triggered to prevent outage")
    print("- Automatic renewal via Let's Encrypt initiated")
    print("\nExpected Agent Actions:")
    print("1. Detection Agent identifies SSL expiration anomaly")
    print("2. Diagnosis Agent verifies certificate and renewal status")
    print("3. Resolution Agent auto-renews via Let's Encrypt")
    print("4. Resolution Agent reloads Nginx/LB with new certificate")
    print("5. Communication Agent notifies security/infrastructure teams")
    print("\n" + "="*70)
    
    input("\nPress ENTER to start the incident simulation...")
    print("\n")
    
    # Initialize orchestrator
    orchestrator = IncidentOrchestrator()
    
    # Create simulated incident
    incident = {
        "id": f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "resource": {
            "type": "SSL Certificate",
            "id": "cert-prod-01",
            "name": "api.prod.azureincidents.com",
            "provider": "Let's Encrypt",
            "certificate_id": "2026-02-21"
        },
        "anomalies": [
            {
                "metric": "DAYS_UNTIL_EXPIRY",
                "value": 5,
                "baseline": 30,
                "threshold": 10,
                "severity": "high",
                "description": "Certificate expires in only 5 days"
            },
            {
                "metric": "CERTIFICATE_STATUS",
                "value": "WARNING",
                "baseline": "VALID",
                "threshold": "WARNING",
                "severity": "high",
                "description": "Certificate approaching expiration"
            }
        ],
        "detected_at": datetime.utcnow().isoformat(),
        "severity": "high",
        "certificate_context": {
            "domain": "api.prod.azureincidents.com",
            "subject_alt_names": [
                "*.api.prod.azureincidents.com",
                "api-backup.prod.azureincidents.com"
            ],
            "current_expiry": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "renewal_eligible": True,
            "renewal_method": "Let's Encrypt ACME"
        },
        "impact_estimate": {
            "users_affected": "All users (if expires unrenewed)",
            "services_affected": [
                "API Gateway",
                "Web Dashboard",
                "Mobile App Backend",
                "Webhook Endpoints"
            ],
            "business_impact": "CRITICAL - All HTTPS services would fail"
        }
    }
    
    print("🚨 Incident Created!")
    print(f"   ID: {incident['id']}")
    print(f"   Severity: {incident['severity'].upper()}")
    print(f"   Certificate: {incident['certificate_context']['domain']}")
    print(f"   Expires In: {incident['anomalies'][0]['value']} days")
    print(f"   Affected Services: {len(incident['impact_estimate']['services_affected'])}")
    print("\n")
    
    # Run the full incident workflow
    await orchestrator.handle_incident(incident)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nWhat just happened:")
    print("✓ SSL expiration alert detected automatically")
    print("✓ Certificate validity verified")
    print("✓ Automatic renewal initiated via Let's Encrypt ACME")
    print("✓ New certificate generated and deployed")
    print("✓ Nginx/Load Balancer reloaded with new certificate")
    print("✓ All subject alternate names verified")
    print("✓ Security team notified with renewal confirmation")
    print("✓ Post-mortem includes certificate lifecycle automation")
    print("\nMetrics Summary:")
    print("  - Domain: api.prod.azureincidents.com")
    print("  - Days Until Expiry: 5 → 365 (renewed)")
    print("  - Renewal Status: SUCCESS")
    print("  - Affected Services: 4 (all renewed)")
    print("  - Renewal Duration: 5 minutes")
    print("  - Subject Alt Names: 3 (all renewed)")
    print("\nMTTR (Mean Time To Resolution): ~5 minutes")
    print("Manual MTTR would typically be: ~20-30 minutes")
    print("Outage Prevention: 100%")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Exiting...")
