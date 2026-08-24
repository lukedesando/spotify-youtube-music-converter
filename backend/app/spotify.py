import base64
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import httpx


SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_TRACK_URL = "https://api.spotify.com/v1/tracks/{track_id}"


class SpotifyConfigError(Exception):
    pass


class SpotifyNotFoundError(Exception):
    pass


class SpotifyApiError(Exception):
    pass


@dataclass(frozen=True)
class SpotifyToken:
    access_token: str
    expires_at: float


@dataclass(frozen=True)
class SpotifyTrackMetadata:
    spotify_id: str
    title: str
    artists: List[str]
    album: str
    duration_ms: int
    isrc: Optional[str]
    external_url: Optional[str]


HttpPost = Callable[..., httpx.Response]
HttpGet = Callable[..., httpx.Response]


class SpotifyAuthClient:
    def __init__(
        self,
        client_id: Optional[str],
        client_secret: Optional[str],
        post: HttpPost = httpx.post,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.post = post
        self.clock = clock
        self.cached_token: Optional[SpotifyToken] = None

    def get_access_token(self) -> str:
        if not self.client_id or not self.client_secret:
            raise SpotifyConfigError(
                "Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET.",
            )

        now = self.clock()
        if self.cached_token and self.cached_token.expires_at - 60 > now:
            return self.cached_token.access_token

        auth_value = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode("utf-8"),
        ).decode("ascii")
        try:
            response = self.post(
                SPOTIFY_TOKEN_URL,
                data={"grant_type": "client_credentials"},
                headers={
                    "Authorization": f"Basic {auth_value}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=10,
            )
        except httpx.RequestError as error:
            raise SpotifyApiError(f"Spotify token request failed: {error}") from error
        if response.status_code >= 400:
            raise SpotifyApiError(
                f"Spotify token request failed with HTTP {response.status_code}.",
            )

        payload = response.json()
        access_token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if not access_token or not isinstance(expires_in, int):
            raise SpotifyApiError("Spotify token response was missing expected fields.")

        self.cached_token = SpotifyToken(
            access_token=access_token,
            expires_at=now + expires_in,
        )
        return access_token


class SpotifyTrackClient:
    def __init__(
        self,
        auth_client: SpotifyAuthClient,
        get: HttpGet = httpx.get,
    ) -> None:
        self.auth_client = auth_client
        self.get = get

    def get_track(self, spotify_track_id: str) -> SpotifyTrackMetadata:
        token = self.auth_client.get_access_token()
        try:
            response = self.get(
                SPOTIFY_TRACK_URL.format(track_id=spotify_track_id),
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
        except httpx.RequestError as error:
            raise SpotifyApiError(f"Spotify track request failed: {error}") from error
        if response.status_code == 404:
            raise SpotifyNotFoundError(f"Spotify track not found: {spotify_track_id}.")
        if response.status_code >= 400:
            raise SpotifyApiError(
                f"Spotify track request failed with HTTP {response.status_code}.",
            )

        return normalize_track(response.json())


def normalize_track(payload: Dict[str, Any]) -> SpotifyTrackMetadata:
    return SpotifyTrackMetadata(
        spotify_id=payload["id"],
        title=payload["name"],
        artists=[artist["name"] for artist in payload.get("artists", [])],
        album=payload.get("album", {}).get("name", ""),
        duration_ms=payload["duration_ms"],
        isrc=payload.get("external_ids", {}).get("isrc"),
        external_url=payload.get("external_urls", {}).get("spotify"),
    )
