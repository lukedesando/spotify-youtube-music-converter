# Build Phases

## Phase 1: Documentation and skeleton

- Create repo structure.
- Add Android app placeholder.
- Add backend placeholder.
- Add README and scope docs.

## Phase 2: Android share receiver

- Create Kotlin Android project.
- Register share intent.
- Display incoming shared text.
- Parse Spotify track URL.

Verification:

- Sharing a Spotify URL into the app displays the extracted URL and track ID.

## Phase 3: Backend resolver skeleton

- Create FastAPI app.
- Add `/health`.
- Add `/resolve` with mocked response.
- Add basic tests.

Verification:

- Android app can call backend and display a mocked YouTube Music link.

## Phase 4: Spotify metadata lookup

- Add Spotify client credentials flow.
- Resolve track ID to metadata.
- Cache Spotify metadata.

Verification:

- `/resolve` returns title, artist, album, and duration for a Spotify track.

## Phase 5: YouTube candidate search

- Add YouTube search integration.
- Return top candidates.
- Convert video ID to YouTube Music URL.

Verification:

- `/resolve` returns multiple YouTube candidates.

## Phase 6: Scoring and confirmation UI

- Add match scorer.
- Display best match and alternatives.
- Let user share, copy, or choose another.

Verification:

- User can share the selected YouTube Music link.

## Phase 7: Cache and polish

- Add resolution cache.
- Add user-selected corrections.
- Improve error states.
- Add settings screen if needed.

## Later phases

- Album support.
- Playlist support.
- Browser extension.
- Web converter.
- iOS app.
