"""
Detection Agent - Monitors Azure resources and detects anomalies

This agent:
- Connects to Azure Monitor and Application Insights
- Analyzes metrics and logs in real-time
- Uses AI to identify anomalies and potential incidents
- Triggers the diagnosis agent when issues are detected
"""

import os
import json
from datetime import datetime, timedelta
from azure.monitor.query import LogsQueryClient
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient
from azure.servicebus.aio import ServiceBusClient as AsyncServiceBusClient
import asyncio


class DetectionAgent:
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.logs_client = LogsQueryClient(self.credential)
        # self.metrics_client = MetricsQueryClient(self.credential)
        self.workspace_id = os.getenv("AZURE_MONITOR_WORKSPACE_ID")
        self.monitored_webapp_id = os.getenv("MONITORED_WEBAPP_ID")
        
        # Service Bus configuration
        self.servicebus_connection_string = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING")
        self.servicebus_queue_name = "detection-to-diagnosis"
        self.servicebus_client = None
        
        # Configuration
        self.monitoring_interval = int(os.getenv("DETECTION_AGENT_INTERVAL_SECONDS", 60))
        self.anomaly_threshold = 2.0  # Standard deviations from baseline
        self.cpu_threshold = 80.0  # CPU percentage threshold
        self.memory_threshold = 85.0  # Memory percentage threshold
        
    async def start_monitoring(self):
        """Start continuous monitoring of Azure resources"""
        print(f"[Detection Agent] Starting monitoring (interval: {self.monitoring_interval}s)")
        
        while True:
            try:
                await self.check_all_resources()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                print(f"[Detection Agent] Error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def check_all_resources(self):
        """Check all monitored resources for anomalies"""
        if not self.monitored_webapp_id:
            print("[Detection Agent] ⚠️  MONITORED_WEBAPP_ID not set in environment variables")
            return
        
        # Monitor the Azure web app
        resource = {
            "type": "WebApp",
            "id": self.monitored_webapp_id,
            "name": "Azure Web App"
        }
        
        anomalies = await self.detect_anomalies(resource)
        if anomalies:
            await self.trigger_incident(resource, anomalies)
    
    async def detect_anomalies(self, resource):
        """Detect anomalies in resource metrics (CPU and Memory)"""
        try:
            anomalies = []
            
            # Query CPU metrics from Azure Monitor
            cpu_query = f"""
            AzureMetrics
            | where ResourceId == '{resource['id']}'
            | where MetricName == 'CpuPercentage'
            | where TimeGenerated > ago(5m)
            | summarize avg_cpu = avg(Average), max_cpu = max(Maximum) by bin(TimeGenerated, 1m)
            | order by TimeGenerated desc
            """
            
            # Query Memory metrics from Azure Monitor
            memory_query = f"""
            AzureMetrics
            | where ResourceId == '{resource['id']}'
            | where MetricName == 'MemoryPercentage'
            | where TimeGenerated > ago(5m)
            | summarize avg_memory = avg(Average), max_memory = max(Maximum) by bin(TimeGenerated, 1m)
            | order by TimeGenerated desc
            """
            
            # Execute queries
            try:
                cpu_response = await self.logs_client.query_workspace(
                    self.workspace_id,
                    cpu_query,
                    timespan=(datetime.utcnow() - timedelta(minutes=5), datetime.utcnow())
                )
                
                memory_response = await self.logs_client.query_workspace(
                    self.workspace_id,
                    memory_query,
                    timespan=(datetime.utcnow() - timedelta(minutes=5), datetime.utcnow())
                )
                
                # Check CPU metrics
                if cpu_response.tables:
                    for row in cpu_response.tables[0].rows:
                        if len(row) >= 2:
                            avg_cpu = float(row[0]) if row[0] is not None else 0
                            max_cpu = float(row[1]) if row[1] is not None else 0
                            
                            if max_cpu > self.cpu_threshold:
                                anomalies.append({
                                    "metric": "CPU_PERCENTAGE",
                                    "value": max_cpu,
                                    "threshold": self.cpu_threshold,
                                    "severity": "high" if max_cpu > 95 else "medium"
                                })
                
                # Check Memory metrics
                if memory_response.tables:
                    for row in memory_response.tables[0].rows:
                        if len(row) >= 2:
                            avg_memory = float(row[0]) if row[0] is not None else 0
                            max_memory = float(row[1]) if row[1] is not None else 0
                            
                            if max_memory > self.memory_threshold:
                                anomalies.append({
                                    "metric": "MEMORY_PERCENTAGE",
                                    "value": max_memory,
                                    "threshold": self.memory_threshold,
                                    "severity": "high" if max_memory > 95 else "medium"
                                })
            except Exception as e:
                print(f"[Detection Agent] Warning: Could not query Azure Monitor: {e}")
            
            return anomalies
            
        except Exception as e:
            print(f"[Detection Agent] Failed to detect anomalies for {resource['id']}: {e}")
            return []
    
    async def trigger_incident(self, resource, anomalies):
        """Trigger incident workflow when anomalies detected"""
        incident = {
            "id": f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "resource": resource,
            "anomalies": anomalies,
            "detected_at": datetime.utcnow().isoformat(),
            "severity": self._calculate_severity(anomalies)
        }
        
        print(f"[Detection Agent] [WARNING] Incident detected: {incident['id']}")
        print(f"  Resource: {resource['type']} ({resource['id']})")
        print(f"  Anomalies: {len(anomalies)}")
        print(f"  Severity: {incident['severity']}")
        
        # Send incident to Diagnosis Agent via Azure Service Bus
        await self.send_to_diagnosis_agent(incident)
    
    async def send_to_diagnosis_agent(self, incident):
        """Send incident data to diagnosis agent via Service Bus queue"""
        if not self.servicebus_connection_string:
            print("[Detection Agent] ⚠️  AZURE_SERVICEBUS_CONNECTION_STRING not set")
            return
        
        try:
            async with AsyncServiceBusClient.from_connection_string(
                self.servicebus_connection_string
            ) as client:
                async with client.get_queue_sender(self.servicebus_queue_name) as sender:
                    # Serialize incident to JSON
                    incident_json = json.dumps(incident)
                    
                    # Create and send message
                    from azure.servicebus import ServiceBusMessage
                    message = ServiceBusMessage(
                        body=incident_json,
                        subject="incident_detected",
                        content_type="application/json"
                    )
                    
                    await sender.send_messages(message)
                    print(f"[Detection Agent] [SUCCESS] Incident {incident['id']} sent to diagnosis agent")
                    
        except Exception as e:
            print(f"[Detection Agent] [ERROR] Failed to send incident to diagnosis agent: {e}")
    
    def _calculate_severity(self, anomalies):
        """Calculate incident severity based on anomalies"""
        # Simple severity calculation - can be enhanced
        if len(anomalies) >= 3:
            return "critical"
        elif len(anomalies) >= 2:
            return "high"
        elif len(anomalies) >= 1:
            return "medium"
        return "low"


# Main execution
if __name__ == "__main__":
    agent = DetectionAgent()
    asyncio.run(agent.start_monitoring())
