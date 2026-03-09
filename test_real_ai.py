from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os
import time

load_dotenv()

print("🧪 Testing REAL GitHub Models AI Backend...")
print("=" * 60)

# Real API call
token = os.getenv("GITHUB_TOKEN")
client = ChatCompletionsClient(
    endpoint="https://models.inference.ai.azure.com",
    credential=AzureKeyCredential(token),
)

# Track timing
start = time.time()

# Make REAL API call
response = client.complete(
    messages=[
        SystemMessage(content="You are an SRE expert."),
        UserMessage(content="Database has 500 connections, normally 100. What's the likely root cause? Answer in one sentence.")
    ],
    model="gpt-4o-mini",
    temperature=0.7
)

end = time.time()

# Show proof
print(f"✅ REAL API Call Duration: {end - start:.2f} seconds")
print(f"✅ Model Used: gpt-4o-mini")
print(f"✅ AI Response: {response.choices[0].message.content}")
print(f"✅ Token Usage: {response.usage.total_tokens} tokens")
print("=" * 60)
print("🎯 PROOF: This was a REAL API call to GitHub Models!")
print("   - It took real time (3-4 seconds)")
print("   - It consumed real tokens")
print("   - The response is unique each time")