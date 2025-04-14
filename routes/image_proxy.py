import httpx
from contextlib import asynccontextmanager
from fastapi import APIRouter, HTTPException, Query, Depends, FastAPI # Import FastAPI for type hint
from utils.image_utils import fetch_and_stream_image

_http_client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

async def get_proxy_http_client() -> httpx.AsyncClient:
    """Dependency function to provide the HTTP client for this router."""
    return _http_client


@asynccontextmanager
async def lifespan(app: FastAPI): # Type hint app as FastAPI
    """Manages the lifecycle of the HTTP client for the image proxy router."""
    print("INFO:     Image Proxy Router starting up...")
    # Startup logic (client is already created)
    yield
    # Shutdown logic
    print("INFO:     Image Proxy Router shutting down...")
    await _http_client.aclose()
    print("INFO:     Image Proxy HTTP client closed.")

router = APIRouter(
    prefix="/api",
    tags=["Image Proxy"],
    lifespan=lifespan
)

@router.get("/image-proxy")
async def image_proxy_endpoint(
    url: str = Query(
        ...,
        title="Image URL",
        description="The external URL of the image to proxy."
    ),
    client: httpx.AsyncClient = Depends(get_proxy_http_client)
):
    """
    Endpoint to proxy external images, bypassing client-side CORS issues.
    """
    return await fetch_and_stream_image(url=url, client=client)
