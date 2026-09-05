# Roadmap

The current implementation is intentionally narrow: resolve an individual Spotify track shared from Android into the best matching YouTube Music link. The items below are possible extensions, not promises or current functionality.

## Matching quality

- Add stronger preference controls for official audio versus official music videos.
- Preserve explicit/clean version intent when source metadata makes that distinction available.
- Make match confidence easier to explain when multiple candidate uploads score closely.
- Add an explicit user-feedback path for reporting a bad match without silently changing future behavior.

## Deployment and privacy

- Package a documented remote-backend deployment option.
- Evaluate an optional local-only resolver mode.
- Keep conversion-history storage opt-in if history is ever added.
- Keep source-URL logging minimal and documented if hosted operation is introduced.

## Product expansion

- Album and playlist conversion.
- Better Android presentation and result feedback.
- Optional cache behavior for repeated resolutions.
- iOS or browser-based clients if the Android workflow proves useful enough to justify another client surface.

## Non-goals unless the project scope changes

- Modifying Spotify or YouTube Music clients.
- Bypassing either service's authentication or platform controls.
- Downloading or redistributing audio.
- Automatically publishing or sharing a match without an explicit user action.
