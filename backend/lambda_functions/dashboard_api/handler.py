"""
API Gateway Lambda: single handler for dashboard REST API.
Routes: GET /api/tools, GET /api/tools/{tool_id}/trend, GET /api/aws/spend, GET /api/alerts, GET /api/export.
Adds CORS headers and central error handling.
"""
import json

from endpoints import (
    get_tools,
    get_tool_trend,
    get_aws_spend,
    get_alerts,
    get_export,
)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
}


def _merge_headers(response: dict) -> dict:
    """Ensure CORS headers are on every response."""
    headers = response.get("headers") or {}
    for k, v in CORS_HEADERS.items():
        headers.setdefault(k, v)
    response["headers"] = headers
    return response


def _error(status: int, code: str, message: str) -> dict:
    return _merge_headers({
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": code, "message": message}),
    })


def _route(event: dict) -> dict:
    """Dispatch by path and method."""
    path = (event.get("path") or event.get("rawPath") or "").rstrip("/")
    method = (event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method") or "GET").upper()
    params = event.get("pathParameters") or {}
    query = event.get("queryStringParameters") or {}

    # OPTIONS for CORS preflight
    if method == "OPTIONS":
        return _merge_headers({"statusCode": 204, "headers": {}, "body": ""})

    if method != "GET":
        return _error(405, "method_not_allowed", "Only GET and OPTIONS are allowed")

    # GET /api/tools
    if path == "/api/tools" or path == "/api/tools/":
        return _merge_headers(get_tools())

    # GET /api/tools/{tool_id}/trend
    if path.startswith("/api/tools/") and path.endswith("/trend"):
        tool_id = params.get("tool_id") or params.get("proxy")
        if isinstance(tool_id, str) and "/" in tool_id:
            tool_id = tool_id.split("/")[0]
        days = 7
        if query.get("days"):
            try:
                days = max(1, min(90, int(query["days"])))
            except ValueError:
                pass
        return _merge_headers(get_tool_trend(tool_id or "", days))

    # GET /api/aws/spend
    if path == "/api/aws/spend" or path == "/api/aws/spend/":
        return _merge_headers(get_aws_spend())

    # GET /api/alerts
    if path == "/api/alerts" or path == "/api/alerts/":
        return _merge_headers(get_alerts())

    # GET /api/export
    if path == "/api/export" or path == "/api/export/":
        range_param = query.get("range", "30d")
        if range_param not in ("7d", "30d"):
            range_param = "30d"
        fmt = query.get("format", "csv").lower()
        if fmt not in ("csv", "json"):
            fmt = "csv"
        return _merge_headers(get_export(range_param=range_param, fmt=fmt))

    return _error(404, "not_found", f"No handler for {method} {path}")


def handler(event: dict, context: object) -> dict:
    """API Gateway Lambda entrypoint."""
    try:
        return _route(event)
    except Exception as e:
        return _merge_headers({
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "internal_error", "message": str(e)}),
        })