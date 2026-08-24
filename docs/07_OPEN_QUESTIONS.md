# Open Questions

## Product decisions

- Should the app auto-share high-confidence matches or always require confirmation?
- Should the app share only the URL or include song title and artist text?
- Should the app prefer official audio over official music videos?
- Should explicit versions match explicit versions when possible?

## Technical decisions

- Backend hosted remotely, locally, or both?
- Use YouTube Data API only, or add a YouTube Music-specific library later?
- How much cache should live on-device versus server-side?
- Should bad matches be reported back to improve future scoring?

## Privacy decisions

- Should conversion history be stored?
- Should the backend log source URLs?
- Should there be a local-only mode?
