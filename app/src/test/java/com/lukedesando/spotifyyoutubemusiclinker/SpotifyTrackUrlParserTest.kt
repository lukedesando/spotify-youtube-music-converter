package com.lukedesando.spotifyyoutubemusiclinker

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class SpotifyTrackUrlParserTest {
    @Test
    fun extractsTrackIdFromPlainSpotifyTrackUrl() {
        assertEquals(
            "123abc",
            SpotifyTrackUrlParser.extractTrackId("https://open.spotify.com/track/123abc"),
        )
    }

    @Test
    fun extractsTrackIdFromSpotifyTrackUrlWithQueryString() {
        assertEquals(
            "123abc",
            SpotifyTrackUrlParser.extractTrackId("https://open.spotify.com/track/123abc?si=test"),
        )
    }

    @Test
    fun ignoresNonTrackSpotifyUrls() {
        assertNull(SpotifyTrackUrlParser.extractTrackId("https://open.spotify.com/album/123abc"))
    }
}
