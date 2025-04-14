import httpx
import io
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

async def fetch_and_stream_image(
    url: str,
    client: httpx.AsyncClient
) -> StreamingResponse:
    """
    Fetches an image from an external URL and prepares a StreamingResponse.

    Args:
        url: The external URL of the image.
        client: An httpx.AsyncClient instance.

    Returns:
        A StreamingResponse containing the image data.

    Raises:
        HTTPException: If the URL is invalid, fetching fails, or the
                       content type is not an image.
    """
    if not url:
        raise HTTPException(status_code=400, detail="Missing image URL.")

    if not url.startswith(('http://', 'https://')):
         raise HTTPException(status_code=400, detail="Invalid URL scheme provided for image.")

    try:
        print(f"Fetching image from external source: {url}")
        response = await client.get(url)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        if not content_type.startswith("image/"):
            print(f"Warning: Content-Type '{content_type}' doesn't look like an image for URL: {url}")

        image_bytes = await response.aread()
        return StreamingResponse(io.BytesIO(image_bytes), media_type=content_type)

    except httpx.RequestError as exc:
        print(f"Error fetching image from {url}: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch image from external URL: {exc}"
        )
    except httpx.HTTPStatusError as exc:
        print(f"HTTP error {exc.response.status_code} fetching image from {url}")
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Remote server returned error: {exc.response.status_code}"
        )
    except Exception as exc:
        print(f"Unexpected error processing image from {url}: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error while processing image.")
