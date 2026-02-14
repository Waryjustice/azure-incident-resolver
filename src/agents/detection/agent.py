"""
Detection Agent - Monitors Azure resources and detects anomalies

This agent:
- Connects to Azure Monitor and Application Insights
- Analyzes metrics and logs in real-time
- Uses AI to identify anomalies and potential incidents
- Triggers the diagnosis agent when issues are detected
- Includes connection verification and metrics discovery
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from azure.monitor.query import LogsQueryClient
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient
from azure.servicebus.aio import ServiceBusClient as AsyncServiceBusClient
from azure.core.exceptions import HttpResponseError, ClientAuthenticationError, ResourceNotFoundError
import asyncio

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] [%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DetectionAgent:
    def __init__(self):
        logger.info("Initializing Detection Agent")
        
        try:
            self.credential = DefaultAzureCredential()
            logger.debug("Azure credentials initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Azure credentials: {e}")
            raise
        
        try:
            self.logs_client = LogsQueryClient(self.credential)
            logger.debug("Azure Monitor clients initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Monitor clients: {e}")
            raise
        
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
        
        logger.info(f"Detection Agent configured (interval: {self.monitoring_interval}s)")
        logger.info(f"  Workspace ID: {self.workspace_id[:20]}..." if self.workspace_id else "  Workspace ID: NOT SET")
        logger.info(f"  Monitored Web App: {self.monitored_webapp_id[:20]}..." if self.monitored_webapp_id else "  Monitored Web App: NOT SET")
        
    async def start_monitoring(self):
        """Start continuous monitoring of Azure resources"""
        logger.info(f"Starting continuous monitoring (interval: {self.monitoring_interval}s)")
        
        # Verify Azure Monitor connection before starting
        connection_status = await self.verify_azure_monitor_connection()
        if not connection_status["connected"]:
            logger.error(f"Cannot start monitoring: Azure Monitor connection failed")
            logger.error(f"  Details: {connection_status.get('error', 'Unknown error')}")
            return
        
        logger.info("✓ Azure Monitor connection verified")
        
        while True:
            try:
                await self.check_all_resources()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.monitoring_interval)
    
    async def check_all_resources(self):
        """Check all monitored resources for anomalies"""
        if not self.monitored_webapp_id:
            logger.warning("MONITORED_WEBAPP_ID not set in environment variables")
            return
        
        logger.debug(f"Checking all monitored resources")
        
        # Monitor the Azure web app
        resource = {
            "type": "WebApp",
            "id": self.monitored_webapp_id,
            "name": "Azure Web App"
        }
        
        anomalies = await self.detect_anomalies(resource)
        if anomalies:
            logger.warning(f"Anomalies detected for {resource['name']}: {len(anomalies)} anomalies")
            await self.trigger_incident(resource, anomalies)
        else:
            logger.debug(f"No anomalies detected for {resource['name']}")
    
    async def detect_anomalies(self, resource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in resource metrics (CPU and Memory)"""
        logger.debug(f"Detecting anomalies for resource: {resource['id']}")
        
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
            
            # Execute queries with error handling
            try:
                logger.debug("Querying CPU metrics from Azure Monitor")
                cpu_response = self._query_azure_monitor(
                    self.workspace_id,
                    cpu_query,
                    timespan=(datetime.utcnow() - timedelta(minutes=5), datetime.utcnow())
                )
                
                logger.debug("Querying Memory metrics from Azure Monitor")
                memory_response = self._query_azure_monitor(
                    self.workspace_id,
                    memory_query,
                    timespan=(datetime.utcnow() - timedelta(minutes=5), datetime.utcnow())
                )
                
                # Check CPU metrics
                if cpu_response and cpu_response.tables:
                    logger.debug(f"Processing {len(cpu_response.tables[0].rows)} CPU metric rows")
                    for row in cpu_response.tables[0].rows:
                        if len(row) >= 2:
                            try:
                                avg_cpu = float(row[0]) if row[0] is not None else 0
                                max_cpu = float(row[1]) if row[1] is not None else 0
                                
                                if max_cpu > self.cpu_threshold:
                                    anomaly = {
                                        "metric": "CPU_PERCENTAGE",
                                        "value": max_cpu,
                                        "threshold": self.cpu_threshold,
                                        "severity": "critical" if max_cpu > 95 else "high"
                                    }
                                    anomalies.append(anomaly)
                                    logger.warning(f"CPU anomaly detected: {max_cpu}% (threshold: {self.cpu_threshold}%)")
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Could not parse CPU metric row: {e}")
                else:
                    logger.warning("No CPU metrics returned from Azure Monitor")
                
                # Check Memory metrics
                if memory_response and memory_response.tables:
                    logger.debug(f"Processing {len(memory_response.tables[0].rows)} Memory metric rows")
                    for row in memory_response.tables[0].rows:
                        if len(row) >= 2:
                            try:
                                avg_memory = float(row[0]) if row[0] is not None else 0
                                max_memory = float(row[1]) if row[1] is not None else 0
                                
                                if max_memory > self.memory_threshold:
                                    anomaly = {
                                        "metric": "MEMORY_PERCENTAGE",
                                        "value": max_memory,
                                        "threshold": self.memory_threshold,
                                        "severity": "critical" if max_memory > 95 else "high"
                                    }
                                    anomalies.append(anomaly)
                                    logger.warning(f"Memory anomaly detected: {max_memory}% (threshold: {self.memory_threshold}%)")
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Could not parse memory metric row: {e}")
                else:
                    logger.warning("No memory metrics returned from Azure Monitor")
                
            except HttpResponseError as e:
                logger.error(f"HTTP error querying Azure Monitor: {e.status_code} - {e.message}")
            except ClientAuthenticationError as e:
                logger.error(f"Authentication error with Azure Monitor: {e}")
            except ResourceNotFoundError as e:
                logger.error(f"Resource not found in Azure Monitor: {e}")
            except Exception as e:
                logger.error(f"Unexpected error querying Azure Monitor: {e}", exc_info=True)
            
            logger.debug(f"Anomaly detection complete: found {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies for {resource['id']}: {e}", exc_info=True)
            return []
    
    def _query_azure_monitor(self, workspace_id: str, query: str, timespan: Tuple) -> Any:
        """Execute a query against Azure Monitor with error handling"""
        try:
            if not workspace_id:
                logger.error("Workspace ID is not set")
                raise ValueError("AZURE_MONITOR_WORKSPACE_ID not configured")
            
            logger.debug(f"Executing query against workspace: {workspace_id[:20]}...")
            response = self.logs_client.query_workspace(
                workspace_id,
                query,
                timespan=timespan
            )
            logger.debug(f"Query executed successfully, received response")
            return response
            
        except ClientAuthenticationError as e:
            logger.error(f"Authentication failed for workspace {workspace_id}: {e}")
            raise
        except ResourceNotFoundError as e:
            logger.error(f"Workspace not found: {workspace_id}: {e}")
            raise
        except HttpResponseError as e:
            logger.error(f"HTTP error from Azure Monitor: {e.status_code} - {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}", exc_info=True)
            raise
    
    async def trigger_incident(self, resource: Dict[str, Any], anomalies: List[Dict[str, Any]]):
        """Trigger incident workflow when anomalies detected"""
        incident = {
            "id": f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "resource": resource,
            "anomalies": anomalies,
            "detected_at": datetime.utcnow().isoformat(),
            "severity": self._calculate_severity(anomalies)
        }
        
        logger.warning(f"INCIDENT DETECTED: {incident['id']}")
        logger.warning(f"  Resource: {resource['type']} ({resource['id']})")
        logger.warning(f"  Anomalies: {len(anomalies)}")
        logger.warning(f"  Severity: {incident['severity']}")
        
        # Send incident to Diagnosis Agent via Azure Service Bus
        await self.send_to_diagnosis_agent(incident)
    
    async def send_to_diagnosis_agent(self, incident: Dict[str, Any]):
        """Send incident data to diagnosis agent via Service Bus queue"""
        if not self.servicebus_connection_string:
            logger.error("AZURE_SERVICEBUS_CONNECTION_STRING not set")
            return
        
        try:
            logger.debug("Connecting to Azure Service Bus")
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
                    
                    logger.debug(f"Sending incident {incident['id']} to diagnosis agent via Service Bus")
                    await sender.send_messages(message)
                    logger.info(f"✓ Incident {incident['id']} sent to diagnosis agent successfully")
                    
        except ClientAuthenticationError as e:
            logger.error(f"Authentication failed with Service Bus: {e}")
        except HttpResponseError as e:
            logger.error(f"HTTP error connecting to Service Bus: {e.status_code} - {e.message}")
        except Exception as e:
            logger.error(f"Failed to send incident to diagnosis agent: {e}", exc_info=True)
    
    async def verify_azure_monitor_connection(self) -> Dict[str, Any]:
        """Verify Azure Monitor connection and return connection status"""
        logger.info("Verifying Azure Monitor connection...")
        
        if not self.workspace_id:
            error_msg = "AZURE_MONITOR_WORKSPACE_ID not configured"
            logger.error(f"✗ Connection verification failed: {error_msg}")
            return {
                "connected": False,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not self.monitored_webapp_id:
            error_msg = "MONITORED_WEBAPP_ID not configured"
            logger.error(f"✗ Connection verification failed: {error_msg}")
            return {
                "connected": False,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            # Test connection by running a simple test query
            test_query = """
            AzureMetrics
            | take 1
            """
            
            logger.debug("Running test query to verify connection...")
            response = self._query_azure_monitor(
                self.workspace_id,
                test_query,
                timespan=(datetime.utcnow() - timedelta(hours=1), datetime.utcnow())
            )
            
            logger.info("✓ Azure Monitor connection verified successfully")
            return {
                "connected": True,
                "workspace_id": self.workspace_id[:20] + "...",
                "webapp_id": self.monitored_webapp_id[:20] + "...",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except ClientAuthenticationError as e:
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(f"✗ Connection verification failed: {error_msg}")
            return {
                "connected": False,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        except ResourceNotFoundError as e:
            error_msg = f"Workspace not found: {self.workspace_id}"
            logger.error(f"✗ Connection verification failed: {error_msg}")
            return {
                "connected": False,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        except HttpResponseError as e:
            error_msg = f"HTTP error: {e.status_code} - {e.message}"
            logger.error(f"✗ Connection verification failed: {error_msg}")
            return {
                "connected": False,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"✗ Connection verification failed: {error_msg}")
            return {
                "connected": False,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def display_available_metrics(self) -> Dict[str, Any]:
        """Display available metrics for the monitored web app"""
        logger.info("Querying available metrics for monitored web app...")
        
        if not self.workspace_id or not self.monitored_webapp_id:
            error_msg = "Workspace ID or Web App ID not configured"
            logger.error(f"Cannot display metrics: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        
        try:
            # Query available metrics in the last 24 hours
            metrics_query = f"""
            AzureMetrics
            | where ResourceId == '{self.monitored_webapp_id}'
            | where TimeGenerated > ago(24h)
            | distinct MetricName
            | sort by MetricName asc
            """
            
            logger.debug("Executing metrics discovery query...")
            response = self._query_azure_monitor(
                self.workspace_id,
                metrics_query,
                timespan=(datetime.utcnow() - timedelta(hours=24), datetime.utcnow())
            )
            
            metrics = []
            if response and response.tables:
                for row in response.tables[0].rows:
                    if row:
                        metrics.append(row[0])
            
            result = {
                "success": True,
                "webapp_id": self.monitored_webapp_id,
                "metrics_count": len(metrics),
                "metrics": metrics,
                "query_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✓ Found {len(metrics)} available metrics")
            for metric in metrics:
                logger.info(f"  - {metric}")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to query metrics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _calculate_severity(self, anomalies: List[Dict[str, Any]]) -> str:
        """Calculate incident severity based on anomalies"""
        if not anomalies:
            return "low"
        
        # Count critical anomalies
        critical_count = sum(1 for a in anomalies if a.get("severity") == "critical")
        high_count = sum(1 for a in anomalies if a.get("severity") == "high")
        
        logger.debug(f"Severity calculation: {critical_count} critical, {high_count} high anomalies")
        
        if critical_count >= 1:
            return "critical"
        elif critical_count + high_count >= 2:
            return "high"
        elif critical_count + high_count >= 1:
            return "medium"
        return "low"


# Main execution
if __name__ == "__main__":
    logger.info("Detection Agent starting...")
    
    try:
        agent = DetectionAgent()
        
        # Run verification before starting monitoring
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == "--verify":
            logger.info("Running connection verification...")
            status = asyncio.run(agent.verify_azure_monitor_connection())
            logger.info(f"Connection Status: {status}")
            
            logger.info("Querying available metrics...")
            metrics = asyncio.run(agent.display_available_metrics())
            logger.info(f"Available Metrics: {metrics}")
        else:
            asyncio.run(agent.start_monitoring())
    except KeyboardInterrupt:
        logger.info("Detection Agent interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in Detection Agent: {e}", exc_info=True)
