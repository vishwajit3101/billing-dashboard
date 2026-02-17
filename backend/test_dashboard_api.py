import sys
import os
import json

# Add lambda function to path
sys.path.insert(0, 'lambda_functions/dashboard_api')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print("="*60)
print("TESTING DASHBOARD API")
print("="*60)

# Import the handler
try:
    from handler import handler as lambda_handler
    print("✓ Handler imported successfully")
except Exception as e:
    print(f"✗ Failed to import handler: {e}")
    sys.exit(1)

# Test 1: GET /api/tools
print("\n" + "-"*60)
print("TEST 1: GET /api/tools")
print("-"*60)

event = {
    'httpMethod': 'GET',
    'path': '/api/tools',
    'queryStringParameters': None
}

try:
    response = lambda_handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    
    if response['statusCode'] == 200:
        print("✓ Success!")
        body = json.loads(response['body'])
        print(f"\nFound {len(body.get('tools', []))} tools:")
        for tool in body.get('tools', []):
            print(f"  - {tool.get('display_name', 'Unknown')}")
    else:
        print(f"✗ Error: {response['body']}")
        
except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: GET /api/aws/spend
print("\n" + "-"*60)
print("TEST 2: GET /api/aws/spend")
print("-"*60)

event = {
    'httpMethod': 'GET',
    'path': '/api/aws/spend',
    'queryStringParameters': None
}

try:
    response = lambda_handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    
    if response['statusCode'] == 200:
        print("✓ Success!")
        body = json.loads(response['body'])
        print(f"Total Spend: ${body.get('total_spend', 0)}")
        print(f"Budget: ${body.get('budget', 0)}")
    else:
        print(f"Response: {response['body']}")
        
except Exception as e:
    print(f"✗ Test failed: {e}")

# Test 3: GET /api/alerts
print("\n" + "-"*60)
print("TEST 3: GET /api/alerts")
print("-"*60)

event = {
    'httpMethod': 'GET',
    'path': '/api/alerts',
    'queryStringParameters': None
}

try:
    response = lambda_handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    
    if response['statusCode'] == 200:
        print("✓ Success!")
        body = json.loads(response['body'])
        print(f"Active alerts: {len(body.get('alerts', []))}")
    else:
        print(f"Response: {response['body']}")
        
except Exception as e:
    print(f"✗ Test failed: {e}")

print("\n" + "="*60)
print("TESTS COMPLETE")
print("="*60)