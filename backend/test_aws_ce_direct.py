import boto3
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def test_aws_ce():
    print("Testing AWS Cost Explorer...")
    try:
        client = boto3.client('ce', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
        
        end = datetime.utcnow().date()
        start = end - timedelta(days=7)
        
        response = client.get_cost_and_usage(
            TimePeriod={'Start': start.isoformat(), 'End': end.isoformat()},
            Granularity='DAILY',
            Metrics=['AmortizedCost']
        )
        print("Success! AWS Cost Explorer response received.")
        print(f"Total results: {len(response['ResultsByTime'])}")
    except Exception as e:
        print(f"AWS Error: {e}")

if __name__ == "__main__":
    test_aws_ce()
