# Project Scope

## Problem

The user listens on Spotify, but some recipients prefer YouTube Music. Spotify's share button emits Spotify URLs. The desired workflow is to share from Spotify and send a YouTube Music URL instead.

## Target workflow

```text
Spotify -> Share -> Spotify to YouTube Music Linker -> Share YouTube Music link
```

## MVP outcome

Given a Spotify track link, the app should:

1. Receive the link from Android's share sheet.
2. Detect that the link is a Spotify track URL.
3. Resolve track metadata: title, artist, album, duration.
4. Search for a likely YouTube/YouTube Music match.
5. Show a confirmation screen with confidence score.
6. Share `https://music.youtube.com/watch?v=<videoId>` through Android's share sheet.

## MVP constraints

- Android only.
- Tracks only.
- Confirmation required before sharing.
- No background monitoring.
- No scraping-heavy approach as the first design.
- API keys should not be hardcoded into the Android APK if a backend is used.

## Success criteria

- A Spotify track link can be shared into the app.
- The app returns a valid YouTube Music link for common songs.
- The user can reject a bad match and choose another candidate.
- Repeated conversions use a cache.
