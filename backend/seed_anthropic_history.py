
import psycopg2
import os
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

def seed_anthropic_history():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cur = conn.cursor()
        
        tool_name = "Anthropic"
        today = date.today()
        
        print(f"Seeding 90 days of baseline history for {tool_name}...")
        
        # Avoid duplicates by deleting first
        cur.execute("DELETE FROM usage_history WHERE tool_name = %s", (tool_name,))
        
        for i in range(90):
            d = today - timedelta(days=i)
            # We seed with 0.0 to represent "real" but zero usage
            cur.execute("""
                INSERT INTO usage_history (tool_name, date, credits_consumed, events_count)
                VALUES (%s, %s, %s, %s)
            """, (tool_name, d, 0.0, 0))
            
        conn.commit()
        print("Seeding complete!")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    seed_anthropic_history()
