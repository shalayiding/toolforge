from typing import Optional
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi

_api = YouTubeTranscriptApi()


def _extract_video_id(video_id_or_url: str) -> str:
    """Accept either a video ID or a full YouTube URL."""
    if "youtube.com" in video_id_or_url or "youtu.be" in video_id_or_url:
        parsed = urlparse(video_id_or_url)
        if "youtu.be" in parsed.netloc:
            return parsed.path.lstrip("/")
        qs = parse_qs(parsed.query)
        return qs.get("v", [video_id_or_url])[0]
    return video_id_or_url


def get_transcript(video: str, languages: Optional[str] = "en") -> list[dict]:
    """Fetch the transcript for a YouTube video as a list of timestamped snippets.
    Returns list of {text, start, duration}.
    Params:
      video (str, required) — video ID e.g. 'dQw4w9WgXcQ' or full YouTube URL
      languages (str, default 'en') — comma-separated language priority list e.g. 'en' or 'zh,en'
    """
    try:
        video_id = _extract_video_id(video)
        lang_list = [l.strip() for l in languages.split(",")] if languages else ["en"]
        transcript = _api.fetch(video_id, languages=lang_list)
        return [{"text": s.text, "start": s.start, "duration": s.duration} for s in transcript]
    except Exception as e:
        return [{"error": str(e)}]


def get_transcript_text(video: str, languages: Optional[str] = "en") -> str:
    """Fetch the full transcript of a YouTube video as a single plain text string.
    Best for summarizing, translating, or analyzing video content.
    Params:
      video (str, required) — video ID e.g. 'dQw4w9WgXcQ' or full YouTube URL
      languages (str, default 'en') — comma-separated language priority list e.g. 'en' or 'zh,en'
    """
    try:
        video_id = _extract_video_id(video)
        lang_list = [l.strip() for l in languages.split(",")] if languages else ["en"]
        transcript = _api.fetch(video_id, languages=lang_list)
        return " ".join(s.text for s in transcript)
    except Exception as e:
        return f"Error: {e}"


def list_available_transcripts(video: str) -> list[dict]:
    """List all available transcript languages for a YouTube video.
    Returns list of {language, language_code, is_generated, is_translatable}.
    Use this before get_transcript when the default 'en' language fails.
    Params:
      video (str, required) — video ID or full YouTube URL
    """
    try:
        video_id = _extract_video_id(video)
        transcript_list = _api.list(video_id)
        return [
            {
                "language": t.language,
                "language_code": t.language_code,
                "is_generated": t.is_generated,
                "is_translatable": t.is_translatable,
            }
            for t in transcript_list
        ]
    except Exception as e:
        return [{"error": str(e)}]
