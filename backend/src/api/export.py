"""
API Gateway: GET /api/export
Query: range=7d|30d, format=csv|json
Returns file download (FR10).
"""
def handler(event: dict, context: object) -> dict:
    params = event.get("queryStringParameters") or {}
    range_param = params.get("range", "30d")
    fmt = params.get("format", "csv")
    # TODO: build report from DB, return CSV or JSON with Content-Disposition attachment
    body = "tool,date,credits_remaining,credits_used\n"  # stub
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/csv" if fmt == "csv" else "application/json",
            "Content-Disposition": f'attachment; filename="billing-report-{range_param}.{fmt}"',
            "Access-Control-Allow-Origin": "*",
        },
        "body": body,
    }
