"""
API Gateway: GET /api/tools, GET /api/tools/{slug}, GET /api/tools/{slug}/risk
"""
import json

def handler(event: dict, context: object) -> dict:
    path = event.get("path", "") or event.get("rawPath", "")
    path_params = event.get("pathParameters") or {}
    slug = path_params.get("slug") or path_params.get("proxy", "").split("/")[0] if path_params.get("proxy") else None
    # GET /api/tools -> list
    # GET /api/tools/{slug} -> full detail
    # GET /api/tools/{slug}/risk -> risk panel payload
    body = {"slug": slug or "list", "message": "TODO: implement from DB"}
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }
