"""
Test Incident Injector
─────────────────────
Sends a synthetic incident directly to the 'detection-to-diagnosis' Service Bus
queue so you can test the Diagnosis → Resolution → Communication pipeline without
needing real Azure Monitor data.

Usage:
    python scripts/inject_test_incident.py                  # database spike
    python scripts/inject_test_incident.py memory           # memory leak
    python scripts/inject_test_incident.py cpu              # CPU spike
    python scripts/inject_test_incident.py rate             # rate limit
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from azure.servicebus.aio import ServiceBusClient as AsyncServiceBusClient
from azure.servicebus import ServiceBusMessage

load_dotenv()

QUEUE_NAME = "detection-to-diagnosis"

SCENARIOS = {
    "database": {
        "resource": {"type": "Database", "id": "db-prod-001", "name": "Production SQL Database"},
        "anomalies": [
            {"metric": "CONNECTION_COUNT", "value": 500, "threshold": 100, "severity": "high"},
            {"metric": "RESPONSE_TIME",    "value": 5000, "threshold": 1000, "severity": "high"},
        ],
        "severity": "high",
    },
    "memory": {
        "resource": {"type": "WebApp", "id": "webapp-prod-001", "name": "Production Web App"},
        "anomalies": [
            {"metric": "MEMORY_USAGE", "value": 92, "threshold": 85, "severity": "critical"},
        ],
        "severity": "critical",
    },
    "cpu": {
        "resource": {"type": "WebApp", "id": "webapp-prod-001", "name": "Production Web App"},
        "anomalies": [
            {"metric": "CPU_PERCENTAGE", "value": 96, "threshold": 80, "severity": "critical"},
        ],
        "severity": "critical",
    },
    "rate": {
        "resource": {"type": "WebApp", "id": "webapp-prod-001", "name": "Production Web App"},
        "anomalies": [
            {"metric": "RATE_LIMIT_ERRORS", "value": 450, "threshold": 50, "severity": "high"},
        ],
        "severity": "high",
    },
}

# Aliases
SCENARIOS["memory-leak"] = SCENARIOS["memory"]
SCENARIOS["cpu-spike"] = SCENARIOS["cpu"]
SCENARIOS["rate-limit"] = SCENARIOS["rate"]
SCENARIOS["db"] = SCENARIOS["database"]


async def inject(scenario_key: str = "database"):
    connection_string = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING")
    if not connection_string:
        print("❌  AZURE_SERVICEBUS_CONNECTION_STRING is not set in .env")
        sys.exit(1)

    scenario = SCENARIOS.get(scenario_key)
    if not scenario:
        print(f"❌  Unknown scenario '{scenario_key}'. Choose from: {', '.join(SCENARIOS)}")
        sys.exit(1)

    incident = {
        "id": f"INC-TEST-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "detected_at": datetime.utcnow().isoformat(),
        **scenario,
    }

    print(f"\n📤 Sending test incident to queue: {QUEUE_NAME}")
    print(f"   Scenario : {scenario_key}")
    print(f"   ID       : {incident['id']}")
    print(f"   Severity : {incident['severity']}")
    print(f"   Anomalies: {len(incident['anomalies'])}")
    print()

    async with AsyncServiceBusClient.from_connection_string(connection_string) as client:
        async with client.get_queue_sender(QUEUE_NAME) as sender:
            message = ServiceBusMessage(
                body=json.dumps(incident),
                subject="incident_detected",
                content_type="application/json",
            )
            await sender.send_messages(message)

    print(f"✅  Incident {incident['id']} sent successfully.")
    print(f"\n   The Diagnosis Agent should receive and process it momentarily.")
    print(f"   Make sure 'python src/agents/diagnosis/agent.py' is running.\n")


if __name__ == "__main__":
    scenario = sys.argv[1] if len(sys.argv) > 1 else "database"
    asyncio.run(inject(scenario))
