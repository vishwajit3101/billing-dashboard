
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_all_history():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cur = conn.cursor()
        
        print("--- Usage History Summary ---")
        cur.execute("SELECT tool_name, count(*) FROM usage_history GROUP BY tool_name")
        for row in cur.fetchall():
            print(f"Tool: {row[0]}, Entries: {row[1]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_all_history()
