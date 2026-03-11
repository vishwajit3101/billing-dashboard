import os
import requests
import boto3
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

def print_result(service_name, status, details=""):
    color = "\033[92m" if status == "OK" else "\033[91m"
    reset = "\033[0m"
    print(f"{color}[{status}] {service_name}{reset} {details}")

def check_all_apis():
    print("\n--- Verifying All API Connections ---\n")

    # 1. AWS Cost Explorer
    try:
        ce = boto3.client("ce",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "ap-south-1")
        )
        # Just a quick call to check auth
        ce.get_cost_and_usage(
            TimePeriod={
                "Start": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "End": datetime.now().strftime("%Y-%m-%d")
            },
            Granularity="MONTHLY",
            Metrics=["AmortizedCost"]
        )
        print_result("AWS", "OK", "(Cost Explorer Accessible)")
    except Exception as e:
        print_result("AWS", "ERROR", str(e))

    # 2. PostHog
    try:
        ph_key = os.getenv("POSTHOG_PERSONAL_API_KEY")
        ph_proj = os.getenv("POSTHOG_PROJECT_ID")
        ph_host = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
        
        url = f"{ph_host}/api/projects/{ph_proj}/query/"
        headers = {"Authorization": f"Bearer {ph_key}", "Content-Type": "application/json"}
        # Simple ping query
        payload = {"query": {"kind": "HogQLQuery", "query": "SELECT count() FROM events LIMIT 1"}}
        
        resp = requests.post(url, headers=headers, json=payload, timeout=5)
        if resp.status_code == 200:
            print_result("PostHog", "OK", "(Status 200)")
        else:
            print_result("PostHog", "ERROR", f"(Status {resp.status_code})")
    except Exception as e:
        print_result("PostHog", "ERROR", str(e))

    # 3. Tavily
    try:
        tavily_key = os.getenv("TAVILY_API_KEY")
        resp = requests.get("https://api.tavily.com/usage", headers={"Authorization": f"Bearer {tavily_key}"}, timeout=5)
        if resp.status_code == 200:
            print_result("Tavily", "OK", "(Status 200)")
        else:
             print_result("Tavily", "ERROR", f"(Status {resp.status_code})")
    except Exception as e:
        print_result("Tavily", "ERROR", str(e))

    # 4. FullEnrich
    try:
        fe_key = os.getenv("FULLENRICH_API_KEY")
        fe_url = os.getenv("FULLENRICH_USAGE_URL", "https://app.fullenrich.com/api/v1/account/credits")
        resp = requests.get(fe_url, headers={"Authorization": f"Bearer {fe_key}"}, timeout=5)
        if resp.status_code == 200:
            print_result("FullEnrich", "OK", "(Status 200)")
        else:
            print_result("FullEnrich", "ERROR", f"(Status {resp.status_code})")
    except Exception as e:
        print_result("FullEnrich", "ERROR", str(e))

    # 5. Anthropic
    try:
        ant_key = os.getenv("ANTHROPIC_ADMIN_KEY")
        # We test the usage endpoint since we know billing 404s for this account
        url = "https://api.anthropic.com/v1/organizations/usage_report/messages"
        headers = {
            "x-api-key": ant_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=1)
        url_with_params = f"{url}?starting_at={start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}&ending_at={end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        
        resp = requests.get(url_with_params, headers=headers, timeout=5)
        if resp.status_code == 200:
            print_result("Anthropic", "OK", "(Status 200)")
        else:
            print_result("Anthropic", "ERROR", f"(Status {resp.status_code} - {resp.text[:50]})")
    except Exception as e:
        print_result("Anthropic", "ERROR", str(e))
        
    print("\n-----------------------------------\n")

if __name__ == "__main__":
    check_all_apis()
