# Backend Scope

## Stack

- Python
- FastAPI
- SQLite for cache
- HTTP client such as httpx

## API endpoints

### POST /resolve

Input:

```json
{
  "source_url": "https://open.spotify.com/track/..."
}
```

Output:

```json
{
  "source": {
    "type": "track",
    "spotify_id": "...",
    "title": "...",
    "artists": ["..."],
    "album": "...",
    "duration_ms": 123000
  },
  "best_match": {
    "youtube_video_id": "...",
    "music_url": "https://music.youtube.com/watch?v=...",
    "title": "...",
    "channel": "...",
    "duration_ms": 123000,
    "confidence": 0.94
  },
  "candidates": []
}
```

### GET /health

Returns service status.

## Cache tables

### spotify_tracks

- spotify_id
- title
- artists_json
- album
- duration_ms
- fetched_at

### resolutions

- spotify_id
- youtube_video_id
- confidence
- selected_by_user
- created_at
- updated_at

### youtube_candidates

- query_hash
- video_id
- title
- channel
- duration_ms
- raw_json
- fetched_at

## Secret handling

Keep Spotify and YouTube API credentials in backend environment variables, not in the Android app.

Example variables:

```text
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
YOUTUBE_API_KEY=
```
