# Spotify to YouTube Music Linker

An Android share-target utility that turns a shared Spotify track into a matched YouTube Music link.

The project is a working prototype: the Android client receives Spotify track shares, sends the track to a FastAPI resolver, and lets the user share the selected YouTube Music URL. The backend fetches Spotify metadata, searches YouTube Music candidates, scores them, and returns the highest-scoring result.

## How it works

```text
Spotify track
  -> Android share sheet
  -> Spotify to YouTube Music Linker
  -> FastAPI /resolve
  -> Spotify track metadata
  -> YouTube Music candidate search
  -> confidence scoring
  -> best YouTube Music URL
  -> Android share sheet
```

## What works now

- Android `ACTION_SEND` / `text/plain` share target.
- Spotify track URL parsing.
- FastAPI `/health` and `/resolve` endpoints.
- Spotify Web API metadata lookup using client-credentials authentication.
- Configurable YouTube candidate providers: `ytmusicapi`, YouTube Data API, or both.
- Candidate scoring using title similarity, artist evidence, duration, provider signal, and penalties for likely non-target variants such as covers or remixes.
- Explicit no-match behavior when no YouTube Music candidates are available; the resolver does not fabricate a successful URL.
- Android retry for transient transport failures.
- Backend and Android unit/integration tests.

## Repository layout

```text
app/                  Kotlin Android client
backend/app/          FastAPI resolver and matching implementation
backend/tests/        Backend API/provider/scoring tests
docs/                 Architecture and design notes
```

## Backend quick start

Requirements: Python with `venv` support and Spotify API client credentials.

From the repository root on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements-dev.txt

$env:SPOTIFY_CLIENT_ID="<your-client-id>"
$env:SPOTIFY_CLIENT_SECRET="<your-client-secret>"
$env:YOUTUBE_CANDIDATE_PROVIDER="ytmusicapi"

python -m uvicorn backend.app.main:app --reload
```

Verify the service:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

`ytmusicapi` is the default provider and does not require a YouTube API key. Set `YOUTUBE_API_KEY` only when using the `youtube_api` or `both` provider modes.

## Android build

Requirements: JDK 17 and an Android SDK with API 35 available.

Configure the resolver URL in the untracked root `local.properties` file:

```properties
resolverBaseUrl=http://<reachable-backend-host>:8000
```

Then run:

```powershell
.\gradlew.bat test
.\gradlew.bat assembleDebug
```

The backend must be reachable from the Android device. Do not commit a personal LAN address to `local.properties`.

## Tests

Backend:

```powershell
python -m pytest backend\tests
```

Android JVM tests:

```powershell
.\gradlew.bat test
```

The backend suite includes a deterministic resolver test that starts from a Spotify URL, supplies synthetic Spotify metadata and multiple YouTube candidates, runs the real scoring path, and verifies that the highest-scoring YouTube Music candidate is returned.

## Configuration

`.env.example` lists credential variable names only; it does not contain credentials and is not automatically loaded by the application.

Supported backend variables:

- `SPOTIFY_CLIENT_ID` — required.
- `SPOTIFY_CLIENT_SECRET` — required.
- `YOUTUBE_CANDIDATE_PROVIDER` — optional; `ytmusicapi`, `youtube_api`, or `both`.
- `YOUTUBE_API_KEY` — required only for `youtube_api` and `both`.

## Current limitations

- Track links only; albums and playlists are not supported.
- The backend must be run separately and is not hosted by this repository.
- Matching is heuristic and can select the wrong upload when metadata is ambiguous.
- The Android UI is functional rather than polished.
- There is no iOS client.

## Documentation

- [Project scope](docs/01_PROJECT_SCOPE.md)
- [Architecture](docs/02_ARCHITECTURE.md)
- [Android app scope](docs/03_ANDROID_APP_SCOPE.md)
- [Backend scope](docs/04_BACKEND_SCOPE.md)
- [Matching and confidence scoring](docs/05_MATCHING_LOGIC.md)
- [Build phases](docs/06_BUILD_PHASES.md)
- [Open questions](docs/07_OPEN_QUESTIONS.md)

## MVP non-goals

- Modifying Spotify itself.
- Browser extension support.
- iOS support.
- Playlist conversion.
- Fully automatic sharing without a confirmation step.
