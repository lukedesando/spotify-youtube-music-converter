from backend.app.resolver import extract_spotify_track_id


def test_extracts_raw_spotify_track_id():
    assert extract_spotify_track_id("123abc") == "123abc"


def test_extracts_spotify_track_id_from_source_url():
    assert (
        extract_spotify_track_id("https://open.spotify.com/track/123abc?si=test")
        == "123abc"
    )


def test_ignores_non_track_spotify_url():
    assert extract_spotify_track_id("https://open.spotify.com/album/123abc") is None
