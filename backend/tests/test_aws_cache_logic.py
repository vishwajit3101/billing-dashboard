import sys
from pathlib import Path
import time

# Add app directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.aws_cost import get_aws_data, CACHE_FILE

def test_cache():
    print("--- AWS Cache Verification ---")
    
    # 1. Clear cache for fresh start
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        print("Cleared existing cache.")

    # 2. First call (should be fresh)
    start_time = time.time()
    data1 = get_aws_data(30)
    duration1 = time.time() - start_time
    print(f"First call duration: {duration1:.2f}s")
    assert CACHE_FILE.exists(), "Cache file should be created"

    # 3. Second call (should be cached)
    start_time = time.time()
    data2 = get_aws_data(30)
    duration2 = time.time() - start_time
    print(f"Second call duration: {duration2:.2f}s")
    
    assert duration2 < duration1, "Cached call should be significantly faster"
    assert data1 == data2, "Cached data should match fresh data"
    print("--- Verification Successful! ---")

if __name__ == "__main__":
    test_cache()
