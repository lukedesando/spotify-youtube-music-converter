from fastapi.testclient import TestClient

import backend.app.main as main
from backend.app.main import app
from backend.app.spotify import SpotifyConfigError, SpotifyNotFoundError, SpotifyTrackMetadata
from backend.app.youtube import YouTubeCandidate, YouTubeConfigError


client = TestClient(app)


def fake_spotify_track_client():
    class FakeSpotifyTrackClient:
        def get_track(self, spotify_track_id):
            return SpotifyTrackMetadata(
                spotify_id=spotify_track_id,
                title="Example Song",
                artists=["First Artist", "Second Artist"],
                album="Example Album",
                duration_ms=123456,
                isrc="USRC17607839",
                external_url=f"https://open.spotify.com/track/{spotify_track_id}",
            )

    return FakeSpotifyTrackClient()


def fake_youtube_client():
    class FakeYouTubeClient:
        def search_candidates(self, spotify_track):
            return [
                YouTubeCandidate(
                    youtube_video_id="video-one",
                    music_url="https://music.youtube.com/watch?v=video-one",
                    title="Example Song",
                    channel="First Artist",
                    description="Official audio",
                    duration_ms=123456,
                    source="youtube_api",
                ),
            ]

    return FakeYouTubeClient()


def apply_successful_resolver_overrides():
    app.dependency_overrides[main.create_spotify_track_client] = fake_spotify_track_client
    app.dependency_overrides[main.create_youtube_candidate_provider] = fake_youtube_client


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_resolve_accepts_spotify_track_id():
    apply_successful_resolver_overrides()
    response = client.post("/resolve", json={"spotify_track_id": "123abc"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == {
        "type": "track",
        "spotify_id": "123abc",
        "title": "Example Song",
        "artists": ["First Artist", "Second Artist"],
        "album": "Example Album",
        "duration_ms": 123456,
        "isrc": "USRC17607839",
        "external_spotify_url": "https://open.spotify.com/track/123abc",
    }
    assert body["best_match"]["music_url"] == (
        "https://music.youtube.com/watch?v=video-one"
    )
    assert 0.0 <= body["best_match"]["confidence"] <= 1.0
    assert body["candidates"] == [
        {
            "youtube_video_id": "video-one",
            "music_url": "https://music.youtube.com/watch?v=video-one",
            "title": "Example Song",
            "channel": "First Artist",
            "description": "Official audio",
            "duration_ms": 123456,
            "source": "youtube_api",
        },
    ]


def test_resolve_accepts_spotify_source_url():
    apply_successful_resolver_overrides()
    response = client.post(
        "/resolve",
        json={"source_url": "https://open.spotify.com/track/123abc?si=test"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["source"]["spotify_id"] == "123abc"


def test_resolve_rejects_missing_track_input():
    response = client.post("/resolve", json={})

    assert response.status_code == 400


def test_resolve_handles_missing_spotify_credentials():
    class MissingCredentialClient:
        def get_track(self, spotify_track_id):
            raise SpotifyConfigError(
                "Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET.",
            )

    app.dependency_overrides[main.create_spotify_track_client] = (
        lambda: MissingCredentialClient()
    )
    app.dependency_overrides[main.create_youtube_candidate_provider] = fake_youtube_client
    response = client.post("/resolve", json={"spotify_track_id": "123abc"})
    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert "SPOTIFY_CLIENT_ID" in response.json()["detail"]


def test_resolve_handles_spotify_not_found():
    class NotFoundClient:
        def get_track(self, spotify_track_id):
            raise SpotifyNotFoundError("Spotify track not found: missing.")

    app.dependency_overrides[main.create_spotify_track_client] = lambda: NotFoundClient()
    app.dependency_overrides[main.create_youtube_candidate_provider] = fake_youtube_client
    response = client.post("/resolve", json={"spotify_track_id": "missing"})
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_resolve_handles_missing_youtube_api_key():
    class MissingYouTubeKeyClient:
        def search_candidates(self, spotify_track):
            raise YouTubeConfigError("Missing YOUTUBE_API_KEY.")

    app.dependency_overrides[main.create_spotify_track_client] = fake_spotify_track_client
    app.dependency_overrides[main.create_youtube_candidate_provider] = lambda: MissingYouTubeKeyClient()
    response = client.post("/resolve", json={"spotify_track_id": "123abc"})
    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "Missing YOUTUBE_API_KEY."


def test_resolve_still_returns_android_compatible_best_match():
    apply_successful_resolver_overrides()
    response = client.post("/resolve", json={"spotify_track_id": "123abc"})
    app.dependency_overrides.clear()

    best_match = response.json()["best_match"]
    assert best_match["music_url"] == "https://music.youtube.com/watch?v=video-one"
    assert isinstance(best_match["confidence"], float)


def test_resolve_returns_candidates_from_ytmusicapi_mode():
    class FakeYTMusicProvider:
        def search_candidates(self, spotify_track):
            return [
                YouTubeCandidate(
                    youtube_video_id="ytmusic-one",
                    music_url="https://music.youtube.com/watch?v=ytmusic-one",
                    title="Example Song",
                    channel="First Artist",
                    description="",
                    duration_ms=123456,
                    source="ytmusicapi",
                ),
            ]

    app.dependency_overrides[main.create_spotify_track_client] = fake_spotify_track_client
    app.dependency_overrides[main.create_youtube_candidate_provider] = (
        lambda: FakeYTMusicProvider()
    )
    response = client.post("/resolve", json={"spotify_track_id": "123abc"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["candidates"][0]["source"] == "ytmusicapi"


def test_resolve_end_to_end_selects_highest_scoring_candidate():
    class MultipleCandidateProvider:
        def search_candidates(self, spotify_track):
            return [
                YouTubeCandidate(
                    youtube_video_id="wrong-cover",
                    music_url="https://music.youtube.com/watch?v=wrong-cover",
                    title="Different Song cover",
                    channel="Unrelated Channel",
                    description="",
                    duration_ms=200000,
                    source="youtube_api",
                ),
                YouTubeCandidate(
                    youtube_video_id="expected-match",
                    music_url="https://music.youtube.com/watch?v=expected-match",
                    title="Example Song",
                    channel="First Artist",
                    description="Official audio",
                    duration_ms=123456,
                    source="ytmusicapi",
                ),
            ]

    app.dependency_overrides[main.create_spotify_track_client] = fake_spotify_track_client
    app.dependency_overrides[main.create_youtube_candidate_provider] = (
        lambda: MultipleCandidateProvider()
    )
    response = client.post(
        "/resolve",
        json={"source_url": "https://open.spotify.com/track/123abc?si=test"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["best_match"]["youtube_video_id"] == "expected-match"
    assert response.json()["best_match"]["music_url"] == (
        "https://music.youtube.com/watch?v=expected-match"
    )


def test_empty_candidates_return_no_match_error():
    class EmptyProvider:
        def search_candidates(self, spotify_track):
            return []

    app.dependency_overrides[main.create_spotify_track_client] = fake_spotify_track_client
    app.dependency_overrides[main.create_youtube_candidate_provider] = (
        lambda: EmptyProvider()
    )
    response = client.post("/resolve", json={"spotify_track_id": "123abc"})
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "No YouTube Music candidates found for this Spotify track."
    )
