package com.lukedesando.spotifyyoutubemusiclinker

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    private lateinit var sharedTextView: TextView
    private lateinit var trackIdView: TextView
    private lateinit var youtubeMusicUrlView: TextView
    private lateinit var shareButton: Button
    private val resolverClient = BackendResolverClient(BuildConfig.RESOLVER_BASE_URL)
    private var currentYoutubeMusicUrl: String? = null
    private var currentTrackId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(createContentView())
        renderIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        renderIntent(intent)
    }

    private fun createContentView(): LinearLayout {
        val padding = (24 * resources.displayMetrics.density).toInt()

        sharedTextView = TextView(this).apply {
            textSize = 16f
        }
        trackIdView = TextView(this).apply {
            textSize = 20f
        }
        youtubeMusicUrlView = TextView(this).apply {
            textSize = 16f
        }
        shareButton = Button(this).apply {
            text = "Share YouTube Music Link"
            isEnabled = false
            setOnClickListener {
                shareYoutubeMusicLink()
            }
        }

        return LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(padding, padding, padding, padding)
            addView(
                TextView(context).apply {
                    text = "Shared Spotify link"
                    textSize = 24f
                },
                LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                ),
            )
            addView(sharedTextView)
            addView(trackIdView)
            addView(youtubeMusicUrlView)
            addView(shareButton)
        }
    }

    private fun renderIntent(intent: Intent?) {
        val sharedText = intent?.sharedText()
        val trackId = SpotifyTrackUrlParser.extractTrackId(sharedText)
        currentTrackId = trackId
        currentYoutubeMusicUrl = null

        sharedTextView.text = "Shared text: ${sharedText ?: "None"}"
        trackIdView.text = if (trackId == null) {
            "Spotify track ID: not found"
        } else {
            "Spotify track ID: $trackId"
        }

        shareButton.isEnabled = false
        when {
            trackId == null -> {
                youtubeMusicUrlView.text = "YouTube Music URL: not available"
            }
            BuildConfig.RESOLVER_BASE_URL.isBlank() -> {
                youtubeMusicUrlView.text =
                    "Backend URL is not configured. Add resolverBaseUrl to local.properties."
            }
            else -> {
                youtubeMusicUrlView.text = "Resolving with backend..."
                resolveWithBackend(trackId)
            }
        }
    }

    private fun Intent.sharedText(): String? {
        if (action != Intent.ACTION_SEND || type != "text/plain") {
            return null
        }

        return getCharSequenceExtra(Intent.EXTRA_TEXT)?.toString()
    }

    private fun shareYoutubeMusicLink() {
        val musicUrl = currentYoutubeMusicUrl ?: return
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, musicUrl)
        }

        startActivity(Intent.createChooser(shareIntent, "Share YouTube Music link"))
    }

    private fun resolveWithBackend(trackId: String) {
        Thread {
            val result = resolverClient.resolve(trackId)
            runOnUiThread {
                if (currentTrackId != trackId) {
                    return@runOnUiThread
                }

                result.fold(
                    onSuccess = { resolved ->
                        currentYoutubeMusicUrl = resolved.musicUrl
                        youtubeMusicUrlView.text =
                            "YouTube Music URL: ${resolved.musicUrl}\nConfidence: ${resolved.confidence}"
                        shareButton.isEnabled = true
                    },
                    onFailure = { error ->
                        currentYoutubeMusicUrl = null
                        youtubeMusicUrlView.text =
                            "Could not resolve YouTube Music link: ${error.message ?: "unknown error"}"
                        shareButton.isEnabled = false
                    },
                )
            }
        }.start()
    }
}
