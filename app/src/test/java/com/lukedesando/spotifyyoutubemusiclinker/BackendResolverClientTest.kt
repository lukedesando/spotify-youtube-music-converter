package com.lukedesando.spotifyyoutubemusiclinker

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.ServerSocket
import java.net.SocketTimeoutException
import java.net.URL
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

class BackendResolverClientTest {
    @Test
    fun returnsClearFailureWhenBackendUrlIsMissing() {
        val result = BackendResolverClient("").resolve("123abc")

        assertTrue(result.isFailure)
        assertEquals("Backend URL is not configured.", result.exceptionOrNull()?.message)
    }

    @Test
    fun postsTrackIdAndParsesBackendBestMatch() {
        var requestBody = ""
        val response = successfulResponse()
        val server = SingleRequestHttpServer(response) { body ->
            requestBody = body
        }

        try {
            val result = BackendResolverClient("http://127.0.0.1:${server.port}")
                .resolve("123abc")
                .getOrThrow()

            assertTrue(server.awaitRequest())
            assertEquals("""{"spotify_track_id":"123abc"}""", requestBody)
            assertEquals("https://music.youtube.com/watch?v=video-one", result.musicUrl)
            assertEquals(0.95, result.confidence, 0.0)
        } finally {
            server.close()
        }
    }

    @Test
    fun retriesOnceAfterTransportTimeout() {
        var connectionCount = 0
        val sleepDelays = mutableListOf<Long>()
        val client = BackendResolverClient(
            baseUrl = "http://resolver.test",
            connectionFactory = { url ->
                connectionCount += 1
                if (connectionCount == 1) {
                    FakeHttpURLConnection(
                        url = url,
                        outputFailure = SocketTimeoutException("connect timed out"),
                    )
                } else {
                    FakeHttpURLConnection(
                        url = url,
                        responseBody = successfulResponse(),
                    )
                }
            },
            sleeper = { delayMs -> sleepDelays += delayMs },
        )

        val result = client.resolve("123abc").getOrThrow()

        assertEquals(2, connectionCount)
        assertEquals(listOf(1_000L), sleepDelays)
        assertEquals("https://music.youtube.com/watch?v=video-one", result.musicUrl)
        assertEquals(0.95, result.confidence, 0.0)
    }

    @Test
    fun doesNotRetryBackendHttpFailure() {
        var connectionCount = 0
        val sleepDelays = mutableListOf<Long>()
        val client = BackendResolverClient(
            baseUrl = "http://resolver.test",
            connectionFactory = { url ->
                connectionCount += 1
                FakeHttpURLConnection(
                    url = url,
                    statusCode = 503,
                    responseBody = "temporarily unavailable",
                )
            },
            sleeper = { delayMs -> sleepDelays += delayMs },
        )

        val result = client.resolve("123abc")

        assertTrue(result.isFailure)
        assertEquals(1, connectionCount)
        assertTrue(sleepDelays.isEmpty())
        assertEquals(
            "Backend returned HTTP 503: temporarily unavailable",
            result.exceptionOrNull()?.message,
        )
    }

    @Test
    fun returnsSecondTransportFailureAfterOneRetry() {
        var connectionCount = 0
        val sleepDelays = mutableListOf<Long>()
        val client = BackendResolverClient(
            baseUrl = "http://resolver.test",
            connectionFactory = { url ->
                connectionCount += 1
                FakeHttpURLConnection(
                    url = url,
                    outputFailure = SocketTimeoutException("timeout $connectionCount"),
                )
            },
            sleeper = { delayMs -> sleepDelays += delayMs },
        )

        val result = client.resolve("123abc")

        assertTrue(result.isFailure)
        assertEquals(2, connectionCount)
        assertEquals(listOf(1_000L), sleepDelays)
        assertEquals("timeout 2", result.exceptionOrNull()?.message)
    }

    private class SingleRequestHttpServer(
        private val responseBody: String,
        private val onBody: (String) -> Unit,
    ) {
        private val serverSocket = ServerSocket(0)
        private val requestHandled = CountDownLatch(1)
        val port: Int = serverSocket.localPort

        init {
            Thread {
                serverSocket.accept().use { socket ->
                    val input = socket.getInputStream().bufferedReader()
                    var contentLength = 0
                    generateSequence { input.readLine() }
                        .takeWhile { it.isNotEmpty() }
                        .forEach { header ->
                            if (header.startsWith("Content-Length:", ignoreCase = true)) {
                                contentLength = header.substringAfter(":").trim().toInt()
                            }
                        }

                    val body = CharArray(contentLength)
                    input.read(body)
                    onBody(String(body))

                    val bytes = responseBody.toByteArray()
                    val response = "HTTP/1.1 200 OK\r\n" +
                        "Content-Type: application/json\r\n" +
                        "Content-Length: ${bytes.size}\r\n" +
                        "Connection: close\r\n" +
                        "\r\n"

                    socket.getOutputStream().use { output ->
                        output.write(response.toByteArray())
                        output.write(bytes)
                    }
                    requestHandled.countDown()
                }
            }.start()
        }

        fun awaitRequest(): Boolean {
            return requestHandled.await(2, TimeUnit.SECONDS)
        }

        fun close() {
            serverSocket.close()
        }
    }

    private class FakeHttpURLConnection(
        url: URL,
        private val statusCode: Int = 200,
        private val responseBody: String = "",
        private val outputFailure: IOException? = null,
    ) : HttpURLConnection(url) {
        private val requestBody = ByteArrayOutputStream()

        override fun disconnect() = Unit

        override fun usingProxy(): Boolean = false

        override fun connect() = Unit

        override fun getOutputStream(): OutputStream {
            outputFailure?.let { throw it }
            return requestBody
        }

        override fun getResponseCode(): Int = statusCode

        override fun getInputStream(): InputStream {
            return ByteArrayInputStream(responseBody.toByteArray())
        }

        override fun getErrorStream(): InputStream {
            return ByteArrayInputStream(responseBody.toByteArray())
        }
    }

    private companion object {
        fun successfulResponse(): String {
            return """
                {
                  "source": {"type": "track", "spotify_id": "123abc"},
                  "best_match": {
                    "youtube_video_id": "video-one",
                    "music_url": "https://music.youtube.com/watch?v=video-one",
                    "title": "Example Song",
                    "channel": "First Artist",
                    "confidence": 0.95
                  },
                  "candidates": []
                }
            """.trimIndent()
        }
    }
}
