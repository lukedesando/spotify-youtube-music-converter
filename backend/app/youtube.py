import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import httpx
from ytmusicapi import YTMusic

from backend.app.spotify import SpotifyTrackMetadata


YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeConfigError(Exception):
    pass


class YouTubeApiError(Exception):
    pass


class YouTubeProviderConfigError(Exception):
    pass


@dataclass(frozen=True)
class YouTubeCandidate:
    youtube_video_id: str
    music_url: str
    title: str
    channel: str
    description: str
    duration_ms: Optional[int]
    source: str


HttpGet = Callable[..., httpx.Response]


class YouTubeCandidateProvider:
    def search_candidates(
        self,
        spotify_track: SpotifyTrackMetadata,
        max_results: int = 5,
    ) -> List[YouTubeCandidate]:
        raise NotImplementedError


class YouTubeApiClient(YouTubeCandidateProvider):
    def __init__(
        self,
        api_key: Optional[str],
        get: HttpGet = httpx.get,
    ) -> None:
        self.api_key = api_key
        self.get = get

    def search_candidates(
        self,
        spotify_track: SpotifyTrackMetadata,
        max_results: int = 5,
    ) -> List[YouTubeCandidate]:
        if not self.api_key:
            raise YouTubeConfigError("Missing YOUTUBE_API_KEY.")

        query = build_search_query(spotify_track)
        try:
            search_response = self.get(
                YOUTUBE_SEARCH_URL,
                params={
                    "key": self.api_key,
                    "part": "snippet",
                    "type": "video",
                    "q": query,
                    "maxResults": max_results,
                },
                timeout=10,
            )
        except httpx.RequestError as error:
            raise YouTubeApiError(f"YouTube search request failed: {error}") from error
        if search_response.status_code >= 400:
            raise YouTubeApiError(
                f"YouTube search request failed with HTTP {search_response.status_code}.",
            )

        video_ids = extract_video_ids(search_response.json())
        if not video_ids:
            return []

        try:
            videos_response = self.get(
                YOUTUBE_VIDEOS_URL,
                params={
                    "key": self.api_key,
                    "part": "snippet,contentDetails",
                    "id": ",".join(video_ids),
                },
                timeout=10,
            )
        except httpx.RequestError as error:
            raise YouTubeApiError(f"YouTube videos request failed: {error}") from error
        if videos_response.status_code >= 400:
            raise YouTubeApiError(
                f"YouTube videos request failed with HTTP {videos_response.status_code}.",
            )

        return normalize_video_candidates(videos_response.json())


class YTMusicClient(YouTubeCandidateProvider):
    def __init__(self, ytmusic: Optional[YTMusic] = None) -> None:
        self.ytmusic = ytmusic or YTMusic()

    def search_candidates(
        self,
        spotify_track: SpotifyTrackMetadata,
        max_results: int = 5,
    ) -> List[YouTubeCandidate]:
        try:
            results = self.ytmusic.search(
                build_ytmusic_query(spotify_track),
                filter="songs",
                limit=max_results,
            )
        except Exception as error:
            raise YouTubeApiError(f"YTMusic search failed: {error}") from error
        return normalize_ytmusic_candidates(results)


class CombinedYouTubeCandidateProvider(YouTubeCandidateProvider):
    def __init__(self, providers: List[YouTubeCandidateProvider]) -> None:
        self.providers = providers

    def search_candidates(
        self,
        spotify_track: SpotifyTrackMetadata,
        max_results: int = 5,
    ) -> List[YouTubeCandidate]:
        candidates: List[YouTubeCandidate] = []
        for provider in self.providers:
            candidates.extend(provider.search_candidates(spotify_track, max_results))
        return candidates


YouTubeClient = YouTubeApiClient


def create_candidate_provider(
    provider_mode: Optional[str],
    youtube_api_key: Optional[str],
) -> YouTubeCandidateProvider:
    mode = (provider_mode or "ytmusicapi").strip().lower()
    if mode == "ytmusicapi":
        return YTMusicClient()
    if mode == "youtube_api":
        return YouTubeApiClient(api_key=youtube_api_key)
    if mode == "both":
        return CombinedYouTubeCandidateProvider(
            [
                YTMusicClient(),
                YouTubeApiClient(api_key=youtube_api_key),
            ],
        )

    raise YouTubeProviderConfigError(
        "YOUTUBE_CANDIDATE_PROVIDER must be ytmusicapi, youtube_api, or both.",
    )


def build_search_query(spotify_track: SpotifyTrackMetadata) -> str:
    primary_artist = spotify_track.artists[0] if spotify_track.artists else ""
    return f"{primary_artist} {spotify_track.title} official audio".strip()


def build_ytmusic_query(spotify_track: SpotifyTrackMetadata) -> str:
    primary_artist = spotify_track.artists[0] if spotify_track.artists else ""
    return f"{primary_artist} {spotify_track.title}".strip()


def extract_video_ids(payload: Dict[str, Any]) -> List[str]:
    video_ids = []
    for item in payload.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if video_id:
            video_ids.append(video_id)
    return video_ids


def normalize_video_candidates(payload: Dict[str, Any]) -> List[YouTubeCandidate]:
    candidates = []
    for item in payload.get("items", []):
        video_id = item.get("id")
        snippet = item.get("snippet", {})
        if not video_id:
            continue

        candidates.append(
            YouTubeCandidate(
                youtube_video_id=video_id,
                music_url=f"https://music.youtube.com/watch?v={video_id}",
                title=snippet.get("title", ""),
                channel=snippet.get("channelTitle", ""),
                description=snippet.get("description", ""),
                duration_ms=parse_youtube_duration_ms(
                    item.get("contentDetails", {}).get("duration"),
                ),
                source="youtube_api",
            ),
        )
    return candidates


def normalize_ytmusic_candidates(results: List[Dict[str, Any]]) -> List[YouTubeCandidate]:
    candidates = []
    for result in results:
        video_id = result.get("videoId")
        if not video_id:
            continue

        candidates.append(
            YouTubeCandidate(
                youtube_video_id=video_id,
                music_url=f"https://music.youtube.com/watch?v={video_id}",
                title=result.get("title", ""),
                channel=artist_display(result),
                description=result.get("description", "") or "",
                duration_ms=duration_seconds_to_ms(result.get("duration_seconds")),
                source="ytmusicapi",
            ),
        )
    return candidates


def artist_display(result: Dict[str, Any]) -> str:
    artists = result.get("artists") or []
    names = [
        artist.get("name", "")
        for artist in artists
        if isinstance(artist, dict) and artist.get("name")
    ]
    if names:
        return ", ".join(names)

    return result.get("artist", "") or result.get("channel", "") or ""


def duration_seconds_to_ms(duration_seconds: Any) -> Optional[int]:
    if duration_seconds is None:
        return None
    try:
        return int(duration_seconds) * 1000
    except (TypeError, ValueError):
        return None


def parse_youtube_duration_ms(duration: Optional[str]) -> Optional[int]:
    if not duration:
        return None

    match = re.fullmatch(
        r"P(?:(?P<days>\d+)D)?T?"
        r"(?:(?P<hours>\d+)H)?"
        r"(?:(?P<minutes>\d+)M)?"
        r"(?:(?P<seconds>\d+)S)?",
        duration,
    )
    if not match:
        return None

    days = int(match.group("days") or 0)
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return (((days * 24 + hours) * 60 + minutes) * 60 + seconds) * 1000
