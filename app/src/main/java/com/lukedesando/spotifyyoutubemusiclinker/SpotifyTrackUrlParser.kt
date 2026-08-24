package com.lukedesando.spotifyyoutubemusiclinker

object SpotifyTrackUrlParser {
    private val spotifyTrackUrl =
        Regex("""https?://open\.spotify\.com/track/([^/?#\s]+)(?:[/?#][^\s]*)?""", RegexOption.IGNORE_CASE)
    private val spotifyId = Regex("""^[A-Za-z0-9]+$""")

    fun extractTrackId(sharedText: String?): String? {
        if (sharedText.isNullOrBlank()) {
            return null
        }

        val id = spotifyTrackUrl.find(sharedText)?.groupValues?.get(1)
        return id?.takeIf { spotifyId.matches(it) }
    }
}
