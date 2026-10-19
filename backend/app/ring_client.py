"""Thin httpx client for the Ring Partner API.

Endpoints are read from `config` so they can move without touching code:

  Token exchange: POST https://oauth.ring.com/oauth/token
  Device list:    GET  https://api.amazonvision.com/v1/devices

Both are confirmed in the Ring Partner API docs:
  https://developer.amazon.com/docs/ring/api-documentation.html

Important caveat on the token flow
---------------------------------
Ring's OAuth server only supports `authorization_code` and `refresh_token`
grant types -- there is no `client_credentials` grant. That means a token
obtained with only the client secret authenticates *your app* but is not
scoped to any Ring customer, and the device endpoint will not return anyone's
devices. Under Ring's one-way account linking, a device call needs an access
token a real Ring customer granted through account linking. See README.md
"Account linking (required for /devices)".

All requests must be made server-to-server from this backend; Ring blocks
browser-initiated requests (CORS).
"""

from __future__ import annotations

import logging

import httpx

from .config import config

log = logging.getLogger(__name__)

# Ring returns a 4-hour token lifetime; refresh a bit early to avoid edge cases.
_TOKEN_EXPIRY_MARGIN_SECONDS = 60


class RingAPIError(RuntimeError):
    """Raised when the Ring API returns an error response."""


async def get_access_token(
    grant_type: str,
    *,
    code: str | None = None,
    refresh_token: str | None = None,
) -> str:
    """Exchange Ring credentials for a Bearer access token.

    grant_type must be one of the flows Ring actually supports:
      - "authorization_code" -- needs `code` (and the call must happen within
        the code's lifetime, 60s for one-way linking, 10m for partner-initiated)
      - "refresh_token"     -- needs `refresh_token`

    Returns the raw access token string. Raises RingAPIError on a non-2xx
    response; the raw Ring body is logged so failures are diagnosable.
    """
    data = {
        "grant_type": grant_type,
        "client_id": config.ring_client_id,
        "client_secret": config.ring_client_secret,
    }
    if code is not None:
        data["code"] = code
    if refresh_token is not None:
        data["refresh_token"] = refresh_token

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(config.token_url, data=data)

    if response.status_code >= 400:
        # Log the raw body (no secrets beyond what the user already holds)
        # so a failure is diagnosable without dumping to the client.
        log.error(
            "Ring token request failed: status=%s body=%s",
            response.status_code,
            response.text,
        )
        raise RingAPIError(
            f"Ring token request failed with status {response.status_code}"
        )

    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise RingAPIError("Ring token response had no access_token field")

    return token


async def list_devices(access_token: str | None = None) -> dict:
    """List the Ring devices accessible with the given access token.

    Returns the parsed JSON:API response from GET /v1/devices. Pass
    `access_token` explicitly, or omit it to fetch a fresh token via the
    configured grant type (see get_access_token).

    Raises RingAPIError on a non-2xx response; the raw Ring body is logged.
    """
    if access_token is None:
        # NOTE: this default path needs a customer-granted token to return
        # real devices -- see the caveat at the top of this module.
        access_token = await get_access_token(grant_type="refresh_token")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    params = {"include": "status,capabilities,location,configurations"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            config.devices_url, headers=headers, params=params
        )

    if response.status_code >= 400:
        log.error(
            "Ring device request failed: status=%s body=%s",
            response.status_code,
            response.text,
        )
        raise RingAPIError(
            f"Ring device request failed with status {response.status_code}"
        )

    return response.json()