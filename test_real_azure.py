from azure.identity import DefaultAzureCredential
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.web import WebSiteManagementClient
from dotenv import load_dotenv
import os
import time

load_dotenv()

print("🧪 Testing REAL Azure SDK Backend Connection...")
print("=" * 60)

credential = DefaultAzureCredential()
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

# Test 1: Real SQL Database Query
print("\n📊 Test 1: Querying REAL Azure SQL Database...")
start = time.time()

sql_client = SqlManagementClient(credential, subscription_id)
database = sql_client.databases.get(
    resource_group_name="azure-incident-resolver-rg",
    server_name="incident-reolver-sql",
    database_name="incident-demo-db"
)

end = time.time()

print(f"✅ API Call Duration: {end - start:.2f} seconds")
print(f"✅ Database Name: {database.name}")
print(f"✅ Current Tier: {database.sku.tier}")
print(f"✅ Current SKU: {database.sku.name}")
print(f"✅ Status: {database.status}")
print(f"✅ Location: {database.location}")

# Test 2: Real App Service Query
print("\n🌐 Test 2: Querying REAL Azure App Service...")
start = time.time()

web_client = WebSiteManagementClient(credential, subscription_id)
app = web_client.web_apps.get(
    resource_group_name="azure-incident-resolver-rg",
    name="incident-demo-app-ss2026"
)

end = time.time()

print(f"✅ API Call Duration: {end - start:.2f} seconds")
print(f"✅ App Name: {app.name}")
print(f"✅ State: {app.state}")
print(f"✅ Default Hostname: {app.default_host_name}")
print(f"✅ Location: {app.location}")

print("\n" + "=" * 60)
print("🎯 PROOF: These were REAL Azure API calls!")
print("   - Each took real time (1-3 seconds)")
print("   - Data comes from actual Azure resources")
print("   - Try visiting: https://" + app.default_host_name)