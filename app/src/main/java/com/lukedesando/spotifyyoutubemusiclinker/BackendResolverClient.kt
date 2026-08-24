package com.lukedesando.spotifyyoutubemusiclinker

import java.io.IOException
import java.net.HttpURLConnection
import java.net.SocketException
import java.net.SocketTimeoutException
import java.net.URL
import java.net.UnknownHostException

data class BackendResolveResult(
    val musicUrl: String,
    val confidence: Double,
)

class BackendResolverClient private constructor(
    private val baseUrl: String,
    private val connectionFactory: (URL) -> HttpURLConnection,
    private val retryDelayMs: Long,
    private val sleeper: (Long) -> Unit,
) {
    constructor(baseUrl: String) : this(
        baseUrl = baseUrl,
        connectionFactory = { url -> url.openConnection() as HttpURLConnection },
        retryDelayMs = RETRY_DELAY_MS,
        sleeper = { delayMs -> Thread.sleep(delayMs) },
    )

    internal constructor(
        baseUrl: String,
        connectionFactory: (URL) -> HttpURLConnection,
        sleeper: (Long) -> Unit,
    ) : this(
        baseUrl = baseUrl,
        connectionFactory = connectionFactory,
        retryDelayMs = RETRY_DELAY_MS,
        sleeper = sleeper,
    )

    fun resolve(spotifyTrackId: String): Result<BackendResolveResult> {
        if (baseUrl.isBlank()) {
            return Result.failure(IllegalStateException("Backend URL is not configured."))
        }

        return runCatching {
            try {
                resolveOnce(spotifyTrackId)
            } catch (error: IOException) {
                if (!error.isRetryableTransportFailure()) {
                    throw error
                }

                sleeper(retryDelayMs)
                resolveOnce(spotifyTrackId)
            }
        }
    }

    private fun resolveOnce(spotifyTrackId: String): BackendResolveResult {
        val endpoint = URL("${baseUrl.trimEnd('/')}/resolve")
        val connection = connectionFactory(endpoint)

        return try {
            connection.requestMethod = "POST"
            connection.connectTimeout = TIMEOUT_MS
            connection.readTimeout = TIMEOUT_MS
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use { output ->
                output.write("""{"spotify_track_id":"${spotifyTrackId.escapeJson()}"}""".toByteArray())
            }

            val responseCode = connection.responseCode
            val body = if (responseCode in 200..299) {
                connection.inputStream.bufferedReader().use { it.readText() }
            } else {
                val errorBody = connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
                throw IOException("Backend returned HTTP $responseCode: $errorBody")
            }

            BackendResolveResult(
                musicUrl = body.requiredStringField("music_url"),
                confidence = body.requiredNumberField("confidence"),
            )
        } finally {
            connection.disconnect()
        }
    }

    private fun IOException.isRetryableTransportFailure(): Boolean {
        return this is SocketTimeoutException ||
            this is SocketException ||
            this is UnknownHostException
    }

    private fun String.escapeJson(): String {
        return replace("\\", "\\\\").replace("\"", "\\\"")
    }

    private fun String.requiredStringField(name: String): String {
        val pattern = Regex("\"$name\"\\s*:\\s*\"([^\"]+)\"")
        return pattern.find(this)?.groupValues?.get(1)
            ?: throw IOException("Backend response missing $name.")
    }

    private fun String.requiredNumberField(name: String): Double {
        val pattern = Regex("\"$name\"\\s*:\\s*([0-9]+(?:\\.[0-9]+)?)")
        return pattern.find(this)?.groupValues?.get(1)?.toDouble()
            ?: throw IOException("Backend response missing $name.")
    }

    private companion object {
        const val TIMEOUT_MS = 5_000
        const val RETRY_DELAY_MS = 1_000L
    }
}
