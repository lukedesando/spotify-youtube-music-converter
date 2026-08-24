# Matching and Confidence Scoring

## Inputs

From Spotify:

- Track title
- Primary artist
- Additional artists
- Album
- Duration

From YouTube search results:

- Video title
- Channel title
- Description, if available
- Duration, if available
- Video ID

## Search query strategy

Start simple:

```text
<artist> <track title> official audio
```

Fallback queries:

```text
<artist> <track title>
<artist> <track title> topic
<artist> <track title> lyrics
```

## Scoring signals

Positive signals:

- Strong title similarity
- Artist name appears in title or channel
- Duration within 3 seconds
- Channel contains `Topic`
- Title contains `Official Audio`
- Title contains album version indicators when Spotify metadata suggests it

Negative signals:

- Title contains `live`
- Title contains `cover`
- Title contains `remix` when Spotify title does not
- Title contains `karaoke`
- Title contains `instrumental` when Spotify title does not
- Duration differs by more than 10 seconds

## Suggested confidence bands

| Confidence | Behavior |
|---|---|
| 0.90+ | Show best match as default |
| 0.75-0.89 | Show warning and alternatives |
| Below 0.75 | Require user choice |

## User correction loop

When the user selects a non-default candidate, save that resolution. Future shares of the same Spotify track should use the selected match.
