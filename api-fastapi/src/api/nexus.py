from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, Response
import httpx
import json
from config import settings

router = APIRouter()

@router.api_route('/tfnexus/{path:path}', methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy_tfnexus(request: Request, path: str):
    """
    Proxy all requests to the TF Nexus API.
    This endpoint forwards all requests to the configured TF Nexus URL.
    """
    async with httpx.AsyncClient(base_url=f"{settings.url_tfnexus}/api") as client:
        # Get the request body
        body = await request.body()
        
        # Get the request headers
        headers = dict(request.headers)
        # Remove headers that should not be forwarded
        headers.pop("host", None)
        
        # Get the request query parameters
        url = httpx.URL(path=path, query=request.url.query.encode("utf-8"))
        
        # Make the request to the upstream service
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            timeout=60000
        )
        # Create a new response with the content from the upstream service
        content = await response.aread()
        
        # Try to parse and print JSON content if possible
        try:
            if response.headers.get("content-type", "").startswith("application/json"):
                json_data = json.loads(content)
                return json_data
        except Exception as e:
            return e
