import base64

import httpx
import pytest

from backend.app.spotify import (
    SPOTIFY_TOKEN_URL,
    SpotifyAuthClient,
    SpotifyConfigError,
    SpotifyNotFoundError,
    SpotifyTrackClient,
    normalize_track,
)


def spotify_track_payload():
    return {
        "id": "123abc",
        "name": "Example Song",
        "artists": [{"name": "First Artist"}, {"name": "Second Artist"}],
        "album": {"name": "Example Album"},
        "duration_ms": 123456,
        "external_ids": {"isrc": "USRC17607839"},
        "external_urls": {"spotify": "https://open.spotify.com/track/123abc"},
    }


def test_token_request_payload_and_header_behavior():
    calls = []

    def post(url, data, headers, timeout):
        calls.append(
            {
                "url": url,
                "data": data,
                "headers": headers,
                "timeout": timeout,
            },
        )
        return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})

    token = SpotifyAuthClient("client-id", "client-secret", post=post).get_access_token()

    expected_auth = base64.b64encode(b"client-id:client-secret").decode("ascii")
    assert token == "token-1"
    assert calls == [
        {
            "url": SPOTIFY_TOKEN_URL,
            "data": {"grant_type": "client_credentials"},
            "headers": {
                "Authorization": f"Basic {expected_auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            "timeout": 10,
        },
    ]


def test_token_is_cached_until_near_expiry():
    call_count = 0

    def post(url, data, headers, timeout):
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            json={"access_token": f"token-{call_count}", "expires_in": 3600},
        )

    auth_client = SpotifyAuthClient(
        "client-id",
        "client-secret",
        post=post,
        clock=lambda: 1000,
    )

    assert auth_client.get_access_token() == "token-1"
    assert auth_client.get_access_token() == "token-1"
    assert call_count == 1


def test_successful_track_metadata_normalization():
    track = normalize_track(spotify_track_payload())

    assert track.spotify_id == "123abc"
    assert track.title == "Example Song"
    assert track.artists == ["First Artist", "Second Artist"]
    assert track.album == "Example Album"
    assert track.duration_ms == 123456
    assert track.isrc == "USRC17607839"
    assert track.external_url == "https://open.spotify.com/track/123abc"


def test_missing_credentials_are_clear():
    with pytest.raises(SpotifyConfigError) as exc:
        SpotifyAuthClient("", "").get_access_token()

    assert "SPOTIFY_CLIENT_ID" in str(exc.value)
    assert "SPOTIFY_CLIENT_SECRET" in str(exc.value)


def test_spotify_not_found_response():
    class FakeAuthClient:
        def get_access_token(self):
            return "token-1"

    def get(url, headers, timeout):
        return httpx.Response(404, json={"error": {"status": 404}})

    client = SpotifyTrackClient(FakeAuthClient(), get=get)

    with pytest.raises(SpotifyNotFoundError):
        client.get_track("missing")
