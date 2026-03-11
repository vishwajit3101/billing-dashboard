
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cur = conn.cursor()
        
        print("--- Tools ---")
        cur.execute("SELECT name, credits_remaining, last_updated FROM tools WHERE name = 'Anthropic'")
        print(cur.fetchone())
        
        print("\n--- Usage History (Anthropic) ---")
        cur.execute("SELECT date, credits_consumed FROM usage_history WHERE tool_name = 'Anthropic' ORDER BY date DESC LIMIT 5")
        for row in cur.fetchall():
            print(row)
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
