# Daybook

A Ring-integrated caretaking check-in app: a lightweight way to confirm that
an elderly relative living alone is doing okay, using their Ring devices as
the sensing layer.

**This is a prototype, not medical monitoring.** It reads presence/device
status from Ring and surfaces a simple check-in signal. It does not provide
medical alerts, diagnosis, or emergency response, and it should not be relied
on as a safety net. The prototype runs against Ring sandbox / test data while
the account-linking flow is being built out.

## Structure

```
daybook/
├── backend/            # Python FastAPI service
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── config.py      # loads Ring credentials from .env
│       ├── main.py        # FastAPI: /health, /devices
│       └── ring_client.py # httpx calls to the Ring Partner API
├── frontend/           # reserved for React (empty for now)
├── .env.example        # copy to .env and fill in
├── .gitignore
├── FRICTION_LOG.md
└── README.md
```

## Setup

1. Create a virtual environment and install dependencies (run from the
   `daybook/` root):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Linux/macOS: .venv/Scripts/activate on Windows
   pip install -r backend/requirements.txt
   ```

2. Copy the example env file and fill in your Ring Public App credentials:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set `RING_CLIENT_ID`, `RING_CLIENT_SECRET`, and
   `RING_HMAC_KEY` to the values from your Ring Developer Console. `.env` is
   git-ignored and never committed.

3. Run the server (from the `daybook/` root):

   ```bash
   cd backend && uvicorn app.main:app --reload
   ```

   The server starts at `http://localhost:8000`. See "Testing" below.

## Endpoints

| Method | Path        | Description                                             |
|--------|-------------|---------------------------------------------------------|
| GET    | `/health`   | Service health check. No Ring call.                     |
| GET    | `/devices`  | Lists Ring devices for the linked account. Requires a customer-granted access token from the account-linking flow. |

## Account linking (required for `/devices`)

Ring's OAuth server only supports `authorization_code` and `refresh_token`
grant types -- there is no `client_credentials` grant. A token obtained with
only the client secret authenticates *your app* but is not scoped to any Ring
customer, so the device endpoint will not return anyone's devices.

Under Ring's one-way account linking, `/devices` needs an access token that a
real Ring customer granted through account linking. The flow is:

1. Ring POSTs an authorization code to your **Token Exchange URL**
   (server-to-server). Exchange it within 60 seconds.
2. Ring redirects the user to your **Account Link URL** with an HMAC-SHA256
   nonce (valid 600 seconds). Verify the nonce, then call
   `POST /v1/accounts/me/app-integrations` with the nonce and an
   `account_identifier`, followed by
   `PATCH /v1/accounts/me/app-integrations` with `{"status": "completed"}`.
   The PATCH is mandatory -- without it the integration stays in `awaiting`
   state.
3. Once linked, exchange the authorization code for a Bearer token and pass it
   to `/devices`.

Account linking is a separate milestone from device listing; see
`FRICTION_LOG.md`.

## Testing

```bash
# Health check (works with just the config loader, no Ring call)
curl http://localhost:8000/health
# -> {"status":"ok"}

# Devices (only works after account linking provides a customer token)
curl "http://localhost:8000/devices?access_token=<TOKEN>"
```

## License

MIT -- see `LICENSE` (add via GitHub's "Add license" button so it shows in the
About section).