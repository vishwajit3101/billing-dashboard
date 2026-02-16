"""
API Gateway: GET /api/health
"""
from src.shared.db import get_connection

def handler(event: dict, context: object) -> dict:
    try:
        conn = get_connection()
        conn.close()
        db_status = "ok"
    except Exception as e:
        db_status = str(e)
    status_code = 200 if db_status == "ok" else 503
    body = {"status": "ok" if status_code == 200 else "error", "db": db_status}
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": __import__("json").dumps(body),
    }
