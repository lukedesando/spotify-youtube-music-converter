# Spotify → YouTube Music Linker

[![CI](https://github.com/lukedesando/spotify-youtube-music-converter/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/lukedesando/spotify-youtube-music-converter/actions/workflows/ci.yml)

A working Android utility that turns a shared Spotify track into a matched YouTube Music link.

The Android client appears in the system share sheet, sends the shared Spotify track to a FastAPI resolver, and returns the best YouTube Music match. The resolver combines Spotify metadata with YouTube Music candidate search and deterministic confidence scoring instead of relying on a simple title lookup.

<!--
PORTFOLIO_MEDIA_SLOT
When screenshots are available, insert them immediately below this comment.
Suggested set:
1. Spotify share sheet with the Linker target visible.
2. Match/result screen with the selected YouTube Music link.
3. Optional short GIF: Spotify -> Share -> Linker -> YouTube Music result.
Keep this comment so future screenshots can be replaced without restructuring the README.
-->

## Why this project exists

Sharing a song across music services is unnecessarily manual. A Spotify link is useful to another Spotify user, but not to someone listening in YouTube Music. This project reduces that handoff to the normal Android share flow while still handling the difficult part: deciding which YouTube Music result actually represents the same recording.

## How it works

```text
Spotify track
  -> Android share sheet
  -> Spotify → YouTube Music Linker
  -> FastAPI /resolve
  -> Spotify track metadata
  -> YouTube Music candidate search
  -> confidence scoring
  -> best matching YouTube Music URL
  -> Android share sheet
```

## Engineering highlights

- **Native Android share integration** — receives Spotify track URLs through `ACTION_SEND` / `text/plain`.
- **Kotlin Android client** — validates incoming Spotify track URLs, calls the resolver, handles transient transport failures, and returns the selected URL to the share flow.
- **FastAPI resolver** — exposes `/health` and `/resolve` endpoints with explicit configuration and error behavior.
- **Spotify metadata lookup** — uses Spotify client-credentials authentication to resolve canonical track metadata.
- **Multiple YouTube candidate sources** — supports `ytmusicapi`, the YouTube Data API, or both.
- **Deterministic confidence scoring** — combines title similarity, artist evidence, duration, provider signal, and penalties for likely covers/remixes/non-target variants.
- **Fail-closed matching** — returns an explicit no-match result when there are no viable candidates rather than fabricating a successful URL.
- **Automated tests** — backend API/provider/scoring tests plus Android JVM tests exercise parsing, resolver behavior, retries, and candidate selection.

## Repository layout

```text
app/                  Kotlin Android client
backend/app/          FastAPI resolver and matching implementation
backend/tests/        Backend API/provider/scoring tests
docs/                 Architecture, scope, matching, and roadmap notes
```

## Backend quick start

Requirements: Python 3.10+ with `venv` support and Spotify API client credentials.

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

`ytmusicapi` is the default candidate provider and does not require a YouTube API key. Set `YOUTUBE_API_KEY` only when using the `youtube_api` or `both` provider modes.

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

Android JVM tests and debug build:

```powershell
.\gradlew.bat test assembleDebug
```

The backend suite includes a deterministic end-to-end resolver test that starts from a Spotify URL, supplies synthetic Spotify metadata and multiple YouTube candidates, runs the real scoring path, and verifies that the highest-scoring candidate is returned.

GitHub Actions runs both the backend suite and the Android JVM/build checks for pull requests and changes to `main`.

## Configuration

`.env.example` lists credential variable names only; it does not contain credentials and is not automatically loaded by the application.

Supported backend variables:

- `SPOTIFY_CLIENT_ID` — required.
- `SPOTIFY_CLIENT_SECRET` — required.
- `YOUTUBE_CANDIDATE_PROVIDER` — optional; `ytmusicapi`, `youtube_api`, or `both`.
- `YOUTUBE_API_KEY` — required only for `youtube_api` and `both`.

Local/private files such as `.env`, `local.properties`, keystores, certificates, APK/AAB outputs, and IDE state are excluded by `.gitignore`.

## Current scope

The project currently supports **individual Spotify track links**. Albums and playlists are intentionally outside the current implementation.

Known limitations:

- The backend must be run separately; this repository does not provide a hosted instance.
- Matching is heuristic and can select the wrong upload when source metadata is ambiguous.
- The Android UI prioritizes the share workflow over visual polish.
- There is no iOS client.

See the [roadmap](docs/07_ROADMAP.md) for possible future expansion without treating those ideas as current functionality.

## Documentation

- [Project scope](docs/01_PROJECT_SCOPE.md)
- [Architecture](docs/02_ARCHITECTURE.md)
- [Android app scope](docs/03_ANDROID_APP_SCOPE.md)
- [Backend scope](docs/04_BACKEND_SCOPE.md)
- [Matching and confidence scoring](docs/05_MATCHING_LOGIC.md)
- [Build phases](docs/06_BUILD_PHASES.md)
- [Roadmap](docs/07_ROADMAP.md)

## License

Released under the [MIT License](LICENSE).
