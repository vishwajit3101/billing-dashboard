import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def list_budgets():
    try:
        client = boto3.client('budgets', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
        # AccountId is required for budgets API
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity()['Account']
        
        response = client.describe_budgets(AccountId=account_id)
        print(f"Found {len(response['Budgets'])} budgets:")
        for budget in response['Budgets']:
            print(f"- {budget['BudgetName']}: {budget['BudgetLimit']['Amount']} {budget['BudgetLimit']['Unit']}")
            return float(budget['BudgetLimit']['Amount'])
    except Exception as e:
        print(f"Error fetching budgets: {e}")
    return None

if __name__ == "__main__":
    list_budgets()
