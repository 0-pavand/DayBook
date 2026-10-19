"""Configuration for Daybook.

Loads the Ring credentials from a local `.env` file (never committed) and
derives the Ring API endpoint URLs from them, so the endpoints live in
configuration rather than hard-coded in code.

Required environment variables (copy `.env.example` to `.env` and fill in):
  RING_CLIENT_ID     - Daybook's Ring Public App client id
  RING_CLIENT_SECRET - Daybook's Ring Public App client secret
  RING_HMAC_KEY      - Daybook's Ring Public App webhook HMAC key
  RING_API_BASE_URL  - Ring Partner API base URL (default: https://api.amazonvision.com)

The Ring OAuth token endpoint and device discovery endpoint are derived from
the base URL per the Ring Partner API docs:
  https://developer.amazon.com/docs/ring/api-documentation.html
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file).
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# Ring Partner API base URL. The OAuth server is a separate host
# (https://oauth.ring.com); the device API lives under the base URL.
DEFAULT_API_BASE_URL = "https://api.amazonvision.com"

# Ring OAuth token endpoint (separate host from the API base URL).
# Confirmed in the Ring Partner API docs:
#   https://developer.amazon.com/docs/ring/api-documentation.html
# POST, form-encoded body: grant_type, client_id, client_secret (+ code or
# refresh_token depending on the flow).
DEFAULT_TOKEN_URL = "https://oauth.ring.com/oauth/token"

# Ring device discovery endpoint (JSON:API format, Bearer token).
# Confirmed in the Ring Partner API docs:
#   https://developer.amazon.com/docs/ring/api-documentation.html
# GET /v1/devices?include=status,capabilities,location,configurations
DEFAULT_DEVICES_PATH = "/v1/devices"


REQUIRED_KEYS = ("RING_CLIENT_ID", "RING_CLIENT_SECRET", "RING_HMAC_KEY", "RING_API_BASE_URL")


def _missing() -> list[str]:
    return [key for key in REQUIRED_KEYS if not os.environ.get(key)]


if _missing():
    missing = ", ".join(_missing())
    raise RuntimeError(
        "Missing required environment variables: "
        f"{missing}. Copy .env.example to .env at the project root and fill "
        "in your Ring Public App credentials before running the server."
    )


@dataclass(frozen=True)
class Config:
    ring_client_id: str = os.environ["RING_CLIENT_ID"]
    ring_client_secret: str = os.environ["RING_CLIENT_SECRET"]
    ring_hmac_key: str = os.environ["RING_HMAC_KEY"]
    ring_api_base_url: str = os.environ["RING_API_BASE_URL"]

    @property
    def token_url(self) -> str:
        # OAuth server is a separate host from the API base URL.
        return DEFAULT_TOKEN_URL

    @property
    def devices_url(self) -> str:
        return f"{self.ring_api_base_url.rstrip('/')}{DEFAULT_DEVICES_PATH}"


config = Config()