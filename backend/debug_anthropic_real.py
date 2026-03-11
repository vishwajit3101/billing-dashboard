
import os
import requests
from dotenv import load_dotenv
from app.anthropic import get_anthropic_remaining_credits

load_dotenv()

def debug_anthropic():
    print("--- Debugging Anthropic Credits ---")
    print(f"ANTHROPIC_ORG_ID: {os.getenv('ANTHROPIC_ORG_ID')}")
    # Don't print key for security, but check if set
    print(f"ANTHROPIC_ADMIN_KEY set: {bool(os.getenv('ANTHROPIC_ADMIN_KEY'))}")
    
    credits, total = get_anthropic_remaining_credits()
    print(f"\nFinal Result: {credits} / {total}")
    
    if credits == 42350.0:
        print("\nWARNING: Still seeing the mock fallback value (42350)!")
    else:
        print("\nSUCCESS: Fetched a real value!")

if __name__ == "__main__":
    debug_anthropic()
