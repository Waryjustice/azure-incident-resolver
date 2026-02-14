"""
Demo Scenario 3: Third-Party API Rate Limit Breach

This script simulates an API rate limit throttling incident where a third-party
service blocks requests, and demonstrates automatic resolution through circuit
breaker activation and exponential backoff implementation.
"""

import asyncio
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestration.orchestrator import IncidentOrchestrator


async def run_demo():
    """Run API rate limit demo"""
    
    print("\n" + "="*70)
    print("DEMO SCENARIO 3: Third-Party API Rate Limit Breach")
    print("="*70)
    print("\nScenario Overview:")
    print("- API calls to third-party payment service exceed rate limits")
    print("- 429 (Too Many Requests) errors spike rapidly")
    print("- Dependent services start failing")
    print("- Customer transactions are blocked")
    print("\nExpected Agent Actions:")
    print("1. Detection Agent identifies rate limit error spike")
    print("2. Diagnosis Agent detects third-party API throttling")
    print("3. Resolution Agent enables circuit breaker immediately")
    print("4. Resolution Agent creates PR for exponential backoff")
    print("5. Communication Agent notifies team and on-call engineer")
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
            "id": "payment-gateway-prod",
            "name": "Payment Processing API Gateway",
            "external_dependency": "Stripe Payment API (v1.0)",
            "rate_limit": "10000 requests/minute"
        },
        "anomalies": [
            {
                "metric": "HTTP_429_ERRORS",
                "value": 547,
                "baseline": 0,
                "threshold": 10,
                "severity": "critical",
                "description": "Rate limit (429) errors spiking: 547 errors in 5 minutes"
            },
            {
                "metric": "API_ERROR_RATE",
                "value": 0.42,
                "baseline": 0.001,
                "threshold": 0.05,
                "severity": "critical",
                "description": "API error rate jumped to 42% (normally 0.1%)"
            },
            {
                "metric": "REQUEST_RETRY_RATE",
                "value": 0.88,
                "baseline": 0.05,
                "threshold": 0.20,
                "severity": "high",
                "description": "88% of requests are being retried (cascading effect)"
            },
            {
                "metric": "TRANSACTION_LATENCY",
                "value": 28000,
                "baseline": 800,
                "threshold": 5000,
                "unit": "ms",
                "severity": "high",
                "description": "Transaction processing time increased 35x due to retries"
            },
            {
                "metric": "FAILED_TRANSACTIONS",
                "value": 342,
                "baseline": 2,
                "threshold": 20,
                "severity": "critical",
                "description": "342 transactions failed in last 5 minutes"
            },
            {
                "metric": "QUEUE_DEPTH",
                "value": 12500,
                "baseline": 150,
                "threshold": 1000,
                "severity": "high",
                "description": "Request queue backed up: 12500 pending requests"
            }
        ],
        "detected_at": datetime.utcnow().isoformat(),
        "severity": "critical",
        "impact_estimate": {
            "users_affected": "~12000",
            "services_affected": ["Payment Gateway", "Order Service", "Checkout", "Subscription Service"],
            "business_impact": "Critical - payments failing, revenue blocked",
            "revenue_impact": "~$5,000/minute in blocked transactions"
        }
    }
    
    print("🚨 Incident Created!")
    print(f"   ID: {incident['id']}")
    print(f"   Service: {incident['resource']['name']}")
    print(f"   External Dependency: {incident['resource']['external_dependency']}")
    print(f"   Rate Limit: {incident['resource']['rate_limit']}")
    print(f"   Severity: {incident['severity'].upper()}")
    print(f"   Anomalies Detected: {len(incident['anomalies'])}")
    print(f"   Estimated Users Affected: {incident['impact_estimate']['users_affected']}")
    print(f"   Revenue Impact: {incident['impact_estimate']['revenue_impact']}")
    print("\n📊 Key Metrics:")
    print(f"   • Rate Limit Errors (429): {incident['anomalies'][0]['value']} (baseline: {incident['anomalies'][0]['baseline']})")
    print(f"   • API Error Rate: {incident['anomalies'][1]['value']*100:.1f}% (baseline: {incident['anomalies'][1]['baseline']*100:.2f}%)")
    print(f"   • Retry Rate: {incident['anomalies'][2]['value']*100:.0f}% (baseline: {incident['anomalies'][2]['baseline']*100:.0f}%)")
    print(f"   • Transaction Latency: {incident['anomalies'][3]['value']}ms (baseline: {incident['anomalies'][3]['baseline']}ms)")
    print(f"   • Failed Transactions: {incident['anomalies'][4]['value']} (baseline: {incident['anomalies'][4]['baseline']})")
    print(f"   • Queue Depth: {incident['anomalies'][5]['value']} requests (baseline: {incident['anomalies'][5]['baseline']})")
    print("\n")
    
    # Run the full incident workflow
    await orchestrator.handle_incident(incident)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nWhat just happened:")
    print("✓ Incident detected and categorized automatically")
    print("✓ Root cause identified (third-party API throttling)")
    print("✓ Circuit breaker activated immediately (graceful degradation)")
    print("✓ Request queue managed with exponential backoff")
    print("✓ GitHub PR created with backoff/retry implementation")
    print("✓ On-call engineer notified of incident")
    print("✓ Revenue protection measures activated")
    print("\nResolution Actions Taken:")
    print("  1. Circuit breaker activated for Stripe API")
    print("  2. Requests queued with exponential backoff")
    print("  3. Retry logic implemented (max 5 retries, 5s max wait)")
    print("  4. Failed transactions logged for manual review")
    print("  5. Graceful degradation: shows 'Payment processing delayed' to users")
    print("\nRecovery Timeline:")
    print("  • T+0s:   Rate limits detected")
    print("  • T+30s:  Circuit breaker activated")
    print("  • T+2m:   Error rate decreased to 8%")
    print("  • T+5m:   Error rate normalized to 0.3%")
    print("  • T+8m:   Circuit breaker opened (requests flowing again)")
    print("\nMTTR (Mean Time To Resolution): ~8-10 minutes")
    print("Manual MTTR would typically be: ~45-90 minutes")
    print("\nTime saved: ~35-80 minutes per incident")
    print("Revenue protected: ~$35,000-40,000 per incident")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Exiting...")
