import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional

from backend.app.spotify import SpotifyTrackMetadata
from backend.app.youtube import YouTubeCandidate


NON_TARGET_WORDS = (
    "live",
    "karaoke",
    "instrumental",
    "cover",
    "remix",
    "slowed",
    "reverb",
    "nightcore",
    "lyrics",
)


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: YouTubeCandidate
    confidence: float


def score_candidates(
    spotify_track: SpotifyTrackMetadata,
    candidates: List[YouTubeCandidate],
) -> List[ScoredCandidate]:
    scored = [
        ScoredCandidate(
            candidate=candidate,
            confidence=score_candidate(spotify_track, candidate),
        )
        for candidate in candidates
    ]
    return sorted(scored, key=lambda item: item.confidence, reverse=True)


def score_candidate(
    spotify_track: SpotifyTrackMetadata,
    candidate: YouTubeCandidate,
) -> float:
    score = 0.15

    title_similarity = SequenceMatcher(
        None,
        normalize_text(spotify_track.title),
        normalize_text(candidate.title),
    ).ratio()
    score += title_similarity * 0.35

    candidate_text = normalize_text(f"{candidate.title} {candidate.channel}")
    if any(normalize_text(artist) in candidate_text for artist in spotify_track.artists):
        score += 0.2

    score += duration_score(spotify_track.duration_ms, candidate.duration_ms)

    if candidate.source == "ytmusicapi":
        score += 0.08

    score -= non_target_penalty(candidate.title)

    return clamp(score)


def duration_score(
    spotify_duration_ms: Optional[int],
    candidate_duration_ms: Optional[int],
) -> float:
    if spotify_duration_ms is None or candidate_duration_ms is None:
        return 0.0

    diff_seconds = abs(spotify_duration_ms - candidate_duration_ms) / 1000
    if diff_seconds <= 3:
        return 0.2
    if diff_seconds <= 10:
        return 0.12
    if diff_seconds > 30:
        return -0.15
    return 0.0


def non_target_penalty(title: str) -> float:
    normalized_title = normalize_text(title)
    penalty = 0.0
    for word in NON_TARGET_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", normalized_title):
            penalty += 0.12
    return penalty


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))
