# Architecture

## Recommended architecture

```text
Android app
  - Share intent receiver
  - Result/confirmation UI
  - Local cache
  - Output share intent

Backend service, optional but recommended
  - Spotify metadata lookup
  - YouTube search
  - Match scoring
  - Shared cache
```

## Data flow

```text
1. User taps Share in Spotify.
2. Android sends ACTION_SEND text to the app.
3. App parses Spotify URL.
4. App calls resolver.
5. Resolver returns candidates.
6. App shows best match and alternatives.
7. User confirms.
8. App opens Android share sheet with YouTube Music URL.
```

## All-on-device option

Pros:

- No server to run.
- Simpler deployment.
- More private.

Cons:

- API secrets are harder to protect.
- Matching improvements require app updates.
- Shared cache is limited to one device.

## App + backend option

Pros:

- Keeps API keys off-device.
- Easier to improve matching without app releases.
- Cache can be reused by future clients.
- Cleaner path to browser extension or web tool later.

Cons:

- Requires hosting or a local service.
- More moving parts.

## Recommended MVP choice

Use Kotlin for Android and Python/FastAPI for the backend.

```text
Kotlin Android app -> FastAPI resolver -> Spotify API + YouTube API -> candidates
```
