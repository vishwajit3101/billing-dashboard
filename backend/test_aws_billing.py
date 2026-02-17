import sys
sys.path.insert(0, 'lambda_functions/billing_fetcher')

from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("TESTING AWS BILLING FETCHER")
print("="*70)

try:
    import handler
    
    handler_func = getattr(handler, 'handler', None) or getattr(handler, 'lambda_handler', None)
    
    if handler_func:
        print("✓ Handler loaded")
        print("\nFetching AWS billing data...")
        
        result = handler_func({}, None)
        
        print(f"\nStatus: {result.get('statusCode')}")
        
        if result.get('statusCode') == 200:
            print("\n✓✓✓ AWS BILLING INTEGRATION SUCCESSFUL! ✓✓✓")
            print(result.get('body'))
        else:
            print(f"Response: {result}")
            
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()