import httpx
import pytest

from backend.app.spotify import SpotifyTrackMetadata
from backend.app.youtube import (
    YOUTUBE_SEARCH_URL,
    YOUTUBE_VIDEOS_URL,
    YTMusicClient,
    YouTubeClient,
    YouTubeConfigError,
    YouTubeProviderConfigError,
    create_candidate_provider,
    normalize_ytmusic_candidates,
    normalize_video_candidates,
    parse_youtube_duration_ms,
)


def spotify_track():
    return SpotifyTrackMetadata(
        spotify_id="123abc",
        title="Example Song",
        artists=["First Artist", "Second Artist"],
        album="Example Album",
        duration_ms=123456,
        isrc="USRC17607839",
        external_url="https://open.spotify.com/track/123abc",
    )


def search_payload():
    return {
        "items": [
            {"id": {"videoId": "video-one"}},
            {"id": {"videoId": "video-two"}},
        ],
    }


def videos_payload():
    return {
        "items": [
            {
                "id": "video-one",
                "snippet": {
                    "title": "Example Song",
                    "channelTitle": "First Artist",
                    "description": "Official audio",
                },
                "contentDetails": {"duration": "PT3M45S"},
            },
            {
                "id": "video-two",
                "snippet": {
                    "title": "Example Song Alternate",
                    "channelTitle": "First Artist - Topic",
                    "description": "Provided to YouTube",
                },
                "contentDetails": {"duration": "PT4M"},
            },
        ],
    }


def test_youtube_search_request_includes_expected_params():
    calls = []

    def get(url, params, timeout):
        calls.append({"url": url, "params": params, "timeout": timeout})
        if url == YOUTUBE_SEARCH_URL:
            return httpx.Response(200, json=search_payload())
        return httpx.Response(200, json=videos_payload())

    YouTubeClient("youtube-key", get=get).search_candidates(spotify_track())

    search_call = calls[0]
    assert search_call["url"] == YOUTUBE_SEARCH_URL
    assert search_call["params"]["q"] == "First Artist Example Song official audio"
    assert search_call["params"]["type"] == "video"
    assert search_call["params"]["part"] == "snippet"
    assert search_call["params"]["maxResults"] == 5
    assert search_call["params"]["key"] == "youtube-key"


def test_videos_request_includes_snippet_and_content_details():
    calls = []

    def get(url, params, timeout):
        calls.append({"url": url, "params": params, "timeout": timeout})
        if url == YOUTUBE_SEARCH_URL:
            return httpx.Response(200, json=search_payload())
        return httpx.Response(200, json=videos_payload())

    YouTubeClient("youtube-key", get=get).search_candidates(spotify_track())

    videos_call = calls[1]
    assert videos_call["url"] == YOUTUBE_VIDEOS_URL
    assert videos_call["params"]["part"] == "snippet,contentDetails"
    assert videos_call["params"]["id"] == "video-one,video-two"
    assert videos_call["params"]["key"] == "youtube-key"


def test_iso_8601_duration_strings_convert_to_milliseconds():
    assert parse_youtube_duration_ms("PT3M45S") == 225000
    assert parse_youtube_duration_ms("PT1H2M3S") == 3723000
    assert parse_youtube_duration_ms("PT4M") == 240000
    assert parse_youtube_duration_ms("PT45S") == 45000


def test_successful_youtube_api_responses_normalize_candidates():
    candidates = normalize_video_candidates(videos_payload())

    assert candidates[0].youtube_video_id == "video-one"
    assert candidates[0].music_url == "https://music.youtube.com/watch?v=video-one"
    assert candidates[0].title == "Example Song"
    assert candidates[0].channel == "First Artist"
    assert candidates[0].description == "Official audio"
    assert candidates[0].duration_ms == 225000
    assert candidates[0].source == "youtube_api"


def test_missing_youtube_api_key_is_clear():
    with pytest.raises(YouTubeConfigError) as exc:
        YouTubeClient("").search_candidates(spotify_track())

    assert "YOUTUBE_API_KEY" in str(exc.value)


def test_default_provider_is_ytmusicapi():
    provider = create_candidate_provider(provider_mode=None, youtube_api_key=None)

    assert isinstance(provider, YTMusicClient)


def test_ytmusicapi_search_uses_songs_filter_and_limit():
    class FakeYTMusic:
        def __init__(self):
            self.calls = []

        def search(self, query, filter, limit):
            self.calls.append({"query": query, "filter": filter, "limit": limit})
            return []

    fake_ytmusic = FakeYTMusic()

    YTMusicClient(ytmusic=fake_ytmusic).search_candidates(spotify_track())

    assert fake_ytmusic.calls == [
        {
            "query": "First Artist Example Song",
            "filter": "songs",
            "limit": 5,
        },
    ]


def test_ytmusicapi_song_results_normalize_correctly():
    candidates = normalize_ytmusic_candidates(
        [
            {
                "videoId": "ytmusic-one",
                "title": "Example Song",
                "artists": [{"name": "First Artist"}, {"name": "Second Artist"}],
                "duration_seconds": 225,
            },
        ],
    )

    assert candidates[0].youtube_video_id == "ytmusic-one"
    assert candidates[0].music_url == "https://music.youtube.com/watch?v=ytmusic-one"
    assert candidates[0].title == "Example Song"
    assert candidates[0].channel == "First Artist, Second Artist"
    assert candidates[0].description == ""
    assert candidates[0].duration_ms == 225000
    assert candidates[0].source == "ytmusicapi"


def test_missing_youtube_api_key_does_not_break_ytmusicapi_mode():
    provider = create_candidate_provider(
        provider_mode="ytmusicapi",
        youtube_api_key=None,
    )

    assert isinstance(provider, YTMusicClient)


def test_missing_youtube_api_key_still_fails_youtube_api_mode():
    provider = create_candidate_provider(
        provider_mode="youtube_api",
        youtube_api_key=None,
    )

    with pytest.raises(YouTubeConfigError):
        provider.search_candidates(spotify_track())


def test_invalid_provider_mode_is_clear():
    with pytest.raises(YouTubeProviderConfigError):
        create_candidate_provider(provider_mode="unsupported", youtube_api_key=None)
