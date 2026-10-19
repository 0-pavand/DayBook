"""Daybook FastAPI application.

Milestone 1: GET /health -- no Ring call, works with just the config loader.
Milestone 2: account linking (redirect + token exchange) -- needs a customer
             to grant access through Ring's one-way account linking.
Milestone 3: GET /devices -- returns Ring devices for the linked account.

Run from the project root:
    cd backend && uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from . import ring_client

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="Daybook")


@app.get("/health")
async def health() -> dict:
    """Service health check. No Ring call; needs only the config loader."""
    return {"status": "ok"}


@app.get("/devices")
async def devices(
    access_token: str | None = Query(
        default=None,
        description="Optional pre-obtained Ring access token. If omitted, "
        "the server attempts to fetch one via the configured grant type.",
    ),
) -> dict:
    """List Ring devices for the currently linked account.

    Requires a customer-granted access token from Ring's account-linking
    flow. A client-credentials-only token authenticates the app but returns
    no devices.
    """
    try:
        return await ring_client.list_devices(access_token=access_token)
    except ring_client.RingAPIError as exc:
        log.warning("devices request failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Upstream Ring API error; check server logs for the raw body.",
        ) from exc


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):  # type: ignore[no-untyped-def]
    log.exception("unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )