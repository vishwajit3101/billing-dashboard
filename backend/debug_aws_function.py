import sys
import os
from datetime import datetime, date, timedelta
import boto3

# Add app directory to path
sys.path.append(os.getcwd())

from app.main import fetch_real_aws_spend

try:
    print("Calling fetch_real_aws_spend()...")
    data = fetch_real_aws_spend()
    print("Data fetched successfully:")
    # Check if it's the mock data
    if data.get("monthly_spend") == 14100.0:
        print("WARNING: Function returned MOCK data.")
    else:
        print("SUCCESS: Function returned REAL data.")
    print(data)
except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
