# Android App Scope

## Stack

- Kotlin
- Jetpack Compose
- Android share intent receiver
- Retrofit or Ktor client for backend calls
- Room or DataStore for local cache/settings if needed

## Main screens

### 1. Incoming share screen

Responsibilities:

- Receive shared text.
- Extract URL.
- Detect unsupported links.
- Show loading state while resolving.

### 2. Match confirmation screen

Show:

- Spotify track title and artist.
- Best YouTube Music match.
- Confidence score.
- Duration comparison.
- Buttons:
  - Share YouTube Music link
  - Choose another match
  - Copy link
  - Cancel

### 3. Candidate picker

Show alternate matches when confidence is low or the user rejects the first match.

## Android intent behavior

The app should register for shared text:

```xml
<intent-filter>
    <action android:name="android.intent.action.SEND" />
    <category android:name="android.intent.category.DEFAULT" />
    <data android:mimeType="text/plain" />
</intent-filter>
```

## Output share behavior

After selecting a match, the app should send text back to the Android share sheet:

```text
https://music.youtube.com/watch?v=<videoId>
```

## MVP edge cases

- Shared text contains more than just a URL.
- Spotify short links or tracking parameters are present.
- Link is an album or playlist, not a track.
- Backend unavailable.
- No confident YouTube match found.
- User wants to copy instead of share.
