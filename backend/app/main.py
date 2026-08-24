import os
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.app.resolver import extract_spotify_track_id
from backend.app.scoring import ScoredCandidate, score_candidates
from backend.app.spotify import (
    SpotifyApiError,
    SpotifyAuthClient,
    SpotifyConfigError,
    SpotifyNotFoundError,
    SpotifyTrackClient,
    SpotifyTrackMetadata,
)
from backend.app.youtube import (
    YouTubeCandidateProvider,
    YouTubeApiError,
    YouTubeCandidate as YouTubeCandidateMetadata,
    YouTubeConfigError,
    YouTubeProviderConfigError,
    create_candidate_provider,
)


app = FastAPI(title="Spotify to YouTube Music Linker Backend")


class HealthResponse(BaseModel):
    status: str


class ResolveRequest(BaseModel):
    spotify_track_id: Optional[str] = Field(default=None)
    source_url: Optional[str] = Field(default=None)


class SourceTrack(BaseModel):
    type: str
    spotify_id: str
    title: Optional[str] = None
    artists: List[str] = Field(default_factory=list)
    album: Optional[str] = None
    duration_ms: Optional[int] = None
    isrc: Optional[str] = None
    external_spotify_url: Optional[str] = None


class YouTubeMusicMatch(BaseModel):
    youtube_video_id: str
    music_url: str
    title: str
    channel: str
    confidence: float


class YouTubeCandidate(BaseModel):
    youtube_video_id: str
    music_url: str
    title: str
    channel: str
    description: str
    duration_ms: Optional[int] = None
    source: str


class ResolveResponse(BaseModel):
    source: SourceTrack
    best_match: YouTubeMusicMatch
    candidates: List[YouTubeCandidate]


def create_spotify_track_client() -> SpotifyTrackClient:
    return SpotifyTrackClient(
        SpotifyAuthClient(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        ),
    )


def create_youtube_candidate_provider() -> YouTubeCandidateProvider:
    return create_candidate_provider(
        provider_mode=os.getenv("YOUTUBE_CANDIDATE_PROVIDER"),
        youtube_api_key=os.getenv("YOUTUBE_API_KEY"),
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/resolve", response_model=ResolveResponse)
def resolve(
    request: ResolveRequest,
    spotify_client: SpotifyTrackClient = Depends(create_spotify_track_client),
    candidate_provider: YouTubeCandidateProvider = Depends(
        create_youtube_candidate_provider,
    ),
) -> ResolveResponse:
    spotify_track_id = extract_spotify_track_id(
        request.spotify_track_id or request.source_url or "",
    )
    if spotify_track_id is None:
        raise HTTPException(
            status_code=400,
            detail="Provide a Spotify track ID or open.spotify.com/track source_url.",
        )

    try:
        spotify_track = spotify_client.get_track(spotify_track_id)
    except SpotifyConfigError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except SpotifyNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except SpotifyApiError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    try:
        youtube_candidates = candidate_provider.search_candidates(spotify_track)
    except YouTubeConfigError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except YouTubeProviderConfigError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except YouTubeApiError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    scored_candidates = score_candidates(spotify_track, youtube_candidates)
    if not scored_candidates:
        raise HTTPException(
            status_code=404,
            detail="No YouTube Music candidates found for this Spotify track.",
        )

    return ResolveResponse(
        source=source_from_spotify_track(spotify_track),
        best_match=best_match_from_scored_candidate(scored_candidates[0]),
        candidates=[
            candidate_from_youtube_candidate(candidate)
            for candidate in youtube_candidates
        ],
    )


def best_match_from_scored_candidate(
    scored_candidate: ScoredCandidate,
) -> YouTubeMusicMatch:
    candidate = scored_candidate.candidate
    return YouTubeMusicMatch(
        youtube_video_id=candidate.youtube_video_id,
        music_url=candidate.music_url,
        title=candidate.title,
        channel=candidate.channel,
        confidence=scored_candidate.confidence,
    )


def source_from_spotify_track(track: SpotifyTrackMetadata) -> SourceTrack:
    return SourceTrack(
        type="track",
        spotify_id=track.spotify_id,
        title=track.title,
        artists=track.artists,
        album=track.album,
        duration_ms=track.duration_ms,
        isrc=track.isrc,
        external_spotify_url=track.external_url,
    )


def candidate_from_youtube_candidate(
    candidate: YouTubeCandidateMetadata,
) -> YouTubeCandidate:
    return YouTubeCandidate(
        youtube_video_id=candidate.youtube_video_id,
        music_url=candidate.music_url,
        title=candidate.title,
        channel=candidate.channel,
        description=candidate.description,
        duration_ms=candidate.duration_ms,
        source=candidate.source,
    )
