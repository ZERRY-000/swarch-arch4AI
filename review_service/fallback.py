"""Task 1 (fallback prediction). Your code goes here.

The review service calls classify() for every new review. Right now it waits
for the inference service for as long as it takes. When the large model
hangs, every review hangs with it, and so does the user.
"""
import httpx

from common import settings

PENDING = {"label": None, "confidence": None, "model": "fallback", "status": "pending"}


async def classify(client: httpx.AsyncClient, text: str) -> dict:
    """Ask the inference service for a sentiment label.

    Return the inference service's JSON plus "status": "scored".
    If it does not answer within settings.INFERENCE_TIMEOUT_S seconds, or
    answers with an error, return a copy of PENDING instead: the review is
    saved, and a batch job can score it later.
    """
    try:
        # Timeout so a hung large-model call cannot hold this request for 20 s.
        r = await client.post(f"{settings.INFERENCE_URL}/predict", json={"text": text},
                              timeout=settings.INFERENCE_TIMEOUT_S)
        r.raise_for_status()  # HTTP 4xx/5xx -> HTTPStatusError -> fallback too
        return {**r.json(), "status": "scored"}
    except httpx.HTTPError:
        # HTTPError covers both TimeoutException and HTTPStatusError.
        # Return a copy: PENDING is shared, and callers may change the result.
        return dict(PENDING)
