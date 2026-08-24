from backend.app.scoring import score_candidate, score_candidates
from backend.app.spotify import SpotifyTrackMetadata
from backend.app.youtube import YouTubeCandidate


def spotify_track():
    return SpotifyTrackMetadata(
        spotify_id="123abc",
        title="Example Song",
        artists=["First Artist"],
        album="Example Album",
        duration_ms=225000,
        isrc=None,
        external_url=None,
    )


def candidate(
    title="Example Song",
    channel="First Artist",
    duration_ms=225000,
    source="ytmusicapi",
    video_id="video-one",
):
    return YouTubeCandidate(
        youtube_video_id=video_id,
        music_url=f"https://music.youtube.com/watch?v={video_id}",
        title=title,
        channel=channel,
        description="",
        duration_ms=duration_ms,
        source=source,
    )


def test_exactish_title_artist_duration_candidate_wins():
    candidates = [
        candidate(
            title="Example Song Live Cover",
            channel="Other Artist",
            duration_ms=310000,
            source="youtube_api",
            video_id="bad",
        ),
        candidate(video_id="good"),
    ]

    scored = score_candidates(spotify_track(), candidates)

    assert scored[0].candidate.youtube_video_id == "good"


def test_live_remix_cover_karaoke_candidates_are_penalized():
    clean = candidate(title="Example Song", video_id="clean")
    live = candidate(title="Example Song Live Remix Cover Karaoke", video_id="bad")

    assert score_candidate(spotify_track(), clean) > score_candidate(
        spotify_track(),
        live,
    )


def test_missing_duration_does_not_crash_scoring():
    scored = score_candidate(spotify_track(), candidate(duration_ms=None))

    assert 0.0 <= scored <= 1.0


def test_ytmusicapi_song_results_are_preferred_when_other_signals_match():
    yt_music = candidate(source="ytmusicapi", video_id="ytmusic")
    youtube_api = candidate(source="youtube_api", video_id="youtube")

    scored = score_candidates(spotify_track(), [youtube_api, yt_music])

    assert scored[0].candidate.youtube_video_id == "ytmusic"
