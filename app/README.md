# Android App

Kotlin Android share-target client for turning a shared Spotify track into a YouTube Music link through the backend resolver.

## Current behavior

- Registers as a `text/plain` `ACTION_SEND` share target.
- Extracts Spotify track IDs from `open.spotify.com/track/...` URLs.
- Posts extracted track IDs to the configured backend `/resolve` endpoint.
- Retries once after transient transport failures such as socket timeouts or temporary host-resolution failures.
- Displays the returned YouTube Music URL and confidence score.
- Opens Android's share sheet with the matched YouTube Music URL.
- Leaves sharing disabled when the input is invalid, the backend is not configured, or resolution fails.
- Does not contain API credentials.

## Backend URL configuration

Set a backend URL in the untracked root `local.properties` file:

```properties
resolverBaseUrl=http://<reachable-backend-host>:8000
```

The host can be a development machine or server as long as the Android device can reach it. Do not commit personal LAN or private-network addresses. If `resolverBaseUrl` is missing, the app shows a configuration message and keeps the share button disabled.

## Build and test

Requirements: JDK 17 and an Android SDK with API 35 available.

From the repository root on Windows PowerShell:

```powershell
.\gradlew.bat test
.\gradlew.bat assembleDebug
```

## Manual flow

1. Start the backend from the repository root:

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

2. Set `resolverBaseUrl=http://<reachable-backend-host>:8000` in `local.properties`.
3. Build and install the debug APK on an Android device.
4. In Spotify, share a track.
5. Select `Spotify to YouTube Music` from the Android share sheet.
6. Confirm the app displays the extracted track ID and then a matched YouTube Music URL and confidence score.
7. Tap `Share YouTube Music Link`.
8. Confirm Android opens the share sheet with the matched YouTube Music URL.

Expected URL extraction examples:

```text
https://open.spotify.com/track/123abc -> 123abc
https://open.spotify.com/track/123abc?si=test -> 123abc
```

If the backend has no candidates for a track, it returns a no-match error rather than a fabricated URL, and the Android client leaves the share action disabled.
