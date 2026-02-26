import time
from app.database import get_db_connection
from app.posthog import get_real_daily_credit_usage
from app.tavily import get_tavily_remaining_credits
from app.fullenrich import get_fullenrich_remaining_credits
from app.anthropic import get_anthropic_remaining_credits
from app.buyercaddy import get_buyercaddy_remaining_credits
from app.main import fetch_real_aws_spend

def test_component(name, func, *args, **kwargs):
    print(f"Testing {name}...")
    start = time.time()
    try:
        result = func(*args, **kwargs)
        print(f"  {name} success in {time.time() - start:.2f}s")
        return result
    except Exception as e:
        print(f"  {name} failed in {time.time() - start:.2f}s: {e}")
        return None

if __name__ == "__main__":
    print("Starting backend hang debug...")
    
    # Test DB
    conn = test_component("DB Connection", get_db_connection)
    if conn:
        conn.close()
    
    # Test PostHog
    test_component("PostHog", get_real_daily_credit_usage, days=7)
    
    # Test Tavily
    test_component("Tavily", get_tavily_remaining_credits)
    
    # Test FullEnrich
    test_component("FullEnrich", get_fullenrich_remaining_credits)
    
    # Test Anthropic
    test_component("Anthropic", get_anthropic_remaining_credits)
    
    # Test BuyerCaddy
    test_component("BuyerCaddy", get_buyercaddy_remaining_credits)
    
    # Test AWS
    test_component("AWS", fetch_real_aws_spend, days=30)
    
    print("Debug complete.")
