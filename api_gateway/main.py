from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

app = FastAPI(
    title="Investment System API Gateway",
    description="Routes requests to Portfolio Service (8001) and Trading Service (8002).",
    version="2.0.0"
)

import os

PORTFOLIO_SERVICE_URL = os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8001")
TRADING_SERVICE_URL = os.getenv("TRADING_SERVICE_URL", "http://localhost:8002")

ROUTES = {
    "/api/v1/investors": PORTFOLIO_SERVICE_URL,
    "/api/v1/portfolios": PORTFOLIO_SERVICE_URL,
    "/api/v1/risks": PORTFOLIO_SERVICE_URL,
    "/api/v1/reports": PORTFOLIO_SERVICE_URL,
    "/api/v1/assets": TRADING_SERVICE_URL,
    "/api/v1/transactions": TRADING_SERVICE_URL,
}

client = httpx.AsyncClient()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(request: Request, path: str):
    # Find matching service
    target_url = None
    for prefix, service_url in ROUTES.items():
        if f"/{path}".startswith(prefix):
            target_url = f"{service_url}/{path}"
            break

    if not target_url:
        return JSONResponse({"detail": "Route not found in Gateway API"}, status_code=404)

    # Proxy the request
    try:
        req = client.build_request(
            request.method,
            f"{target_url}?{request.url.query}",
            headers=request.headers.raw,
            content=await request.body()
        )
        response = await client.send(req)
        return JSONResponse(
            content=response.json() if response.content else None,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except httpx.RequestError as e:
        return JSONResponse({"detail": f"Service unavailable: {str(e)}"}, status_code=503)

