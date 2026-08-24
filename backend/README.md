# Backend

FastAPI resolver for converting Spotify track metadata into a matched YouTube Music URL.

## Current behavior

- `GET /health` returns service status.
- `POST /resolve` accepts either a Spotify track ID or Spotify track URL.
- Spotify metadata is fetched with client-credentials authentication.
- YouTube Music candidates are collected through the configured provider.
- Candidates are scored and the highest-scoring result is returned as `best_match`.
- If no candidates are available, `/resolve` returns HTTP 404 instead of fabricating a successful match.
- No credentials are committed.

## Environment

Set Spotify API credentials in the backend process environment:

```powershell
$env:SPOTIFY_CLIENT_ID="<your-client-id>"
$env:SPOTIFY_CLIENT_SECRET="<your-client-secret>"
```

Candidate provider mode is optional. If `YOUTUBE_CANDIDATE_PROVIDER` is unset, the backend uses unauthenticated `ytmusicapi`.

```powershell
$env:YOUTUBE_CANDIDATE_PROVIDER="ytmusicapi"
```

Supported values:

- `ytmusicapi`: default; no YouTube API key required.
- `youtube_api`: uses YouTube Data API and requires `YOUTUBE_API_KEY`.
- `both`: queries both providers and requires `YOUTUBE_API_KEY`.

Only set a YouTube Data API key when using `youtube_api` or `both`:

```powershell
$env:YOUTUBE_API_KEY="<your-youtube-api-key>"
```

`.env.example` is a reference containing empty placeholders. The backend does not automatically load `.env` files.

## Setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements-dev.txt
```

## Run locally

```powershell
python -m uvicorn backend.app.main:app --reload
```

For testing from a phone on a reachable network:

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Resolve a real Spotify track after credentials are configured:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/resolve `
  -ContentType "application/json" `
  -Body '{"source_url":"https://open.spotify.com/track/<track-id>"}'
```

## Test

```powershell
python -m pytest backend\tests
```

The test suite uses deterministic fakes for external services, so tests do not require live Spotify or YouTube credentials.
