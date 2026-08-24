import re
from typing import Optional


TRACK_URL_PATTERN = re.compile(
    r"https?://open\.spotify\.com/track/([^/?#\s]+)(?:[/?#][^\s]*)?",
    re.IGNORECASE,
)
SPOTIFY_ID_PATTERN = re.compile(r"^[A-Za-z0-9]+$")


def extract_spotify_track_id(value: str) -> Optional[str]:
    if not value or not value.strip():
        return None

    text = value.strip()
    if SPOTIFY_ID_PATTERN.fullmatch(text):
        return text

    match = TRACK_URL_PATTERN.search(text)
    if not match:
        return None

    spotify_track_id = match.group(1)
    if not SPOTIFY_ID_PATTERN.fullmatch(spotify_track_id):
        return None

    return spotify_track_id
