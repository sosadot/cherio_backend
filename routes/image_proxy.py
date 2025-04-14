import httpx
from contextlib import asynccontextmanager
from fastapi import APIRouter, Query, Depends, FastAPI
from utils.image_utils import fetch_and_stream_image

_http_client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

async def get_proxy_http_client() -> httpx.AsyncClient:
    """Dependency function to provide the HTTP client for this router."""
    return _http_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _http_client
    _http_client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)  # Initialize
    yield
    if _http_client:
        await _http_client.aclose()

router = APIRouter(lifespan=lifespan)

@router.get("")
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