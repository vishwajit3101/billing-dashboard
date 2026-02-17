import sys
import os
sys.path.insert(0, 'lambda_functions/posthog_processor')

from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("TESTING POSTHOG PROCESSOR")
print("="*70)
print(f"✓ API Key: {os.getenv('POSTHOG_API_KEY')[:25]}...")
print(f"✓ Project ID: {os.getenv('POSTHOG_PROJECT_ID')}")
print(f"✓ Host: {os.getenv('POSTHOG_HOST')}")
print("="*70)

try:
    print("\n[1/3] Importing handler...")
    import handler
    
    # Find the handler function
    handler_func = None
    if hasattr(handler, 'handler'):
        handler_func = handler.handler
        print("✓ Found handler.handler()")
    elif hasattr(handler, 'lambda_handler'):
        handler_func = handler.lambda_handler
        print("✓ Found handler.lambda_handler()")
    else:
        available = [x for x in dir(handler) if not x.startswith('_')]
        print(f"Available functions: {available}")
    
    if handler_func:
        print("\n[2/3] Calling PostHog API...")
        result = handler_func({}, None)
        
        print(f"\n[3/3] Response received!")
        print(f"Status Code: {result.get('statusCode')}")
        
        if result.get('statusCode') == 200:
            print("\n" + "="*70)
            print("✓✓✓ POSTHOG INTEGRATION SUCCESSFUL! ✓✓✓")
            print("="*70)
            
            import json
            body = json.loads(result.get('body', '{}'))
            print(f"\nEvents processed: {body.get('events_processed', 'N/A')}")
            print(f"Credits calculated: {body.get('credits_calculated', 'N/A')}")
        else:
            print(f"\n⚠ Response: {result.get('body')}")
    else:
        print("✗ No handler function found!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)