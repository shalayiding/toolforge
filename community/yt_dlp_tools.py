import os
import yt_dlp


def download_video(url: str, output_dir: str = "output", format: str = "best[ext=mp4]/best") -> str:
    """Download a video from YouTube or any supported site to a local directory.

    Uses yt-dlp to download a pre-merged mp4 file — no ffmpeg required.
    For highest quality (requires ffmpeg), pass format='bestvideo+bestaudio/best'.
    Params:
      url (str, required) — full video URL e.g. 'https://www.youtube.com/watch?v=xxx'
      output_dir (str, default 'output') — directory path to save the file
      format (str, default 'best[ext=mp4]/best') — yt-dlp format selector
    Returns a string with the downloaded file path on success, or an error message.
    """
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        "format": format,
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "video")
            ext = info.get("ext", "mp4")
            filename = ydl.prepare_filename(info)
            # merged output uses mp4 extension
            if not os.path.exists(filename):
                filename = os.path.splitext(filename)[0] + ".mp4"
            return f"Downloaded: {filename}"
    except Exception as e:
        return f"Error: {e}"


def get_video_info(url: str) -> str:
    """Fetch metadata for a video without downloading it.

    Params:
      url (str, required) — full video URL
    Returns a JSON-serializable string with title, duration, uploader, view_count, formats.
    """
    import json
    ydl_opts = {"quiet": True, "no_warnings": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            info = ydl.sanitize_info(info)
            summary = {
                "title": info.get("title"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "view_count": info.get("view_count"),
                "upload_date": info.get("upload_date"),
                "webpage_url": info.get("webpage_url"),
                "formats_count": len(info.get("formats", [])),
            }
            return json.dumps(summary, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error: {e}"


def download_audio(url: str, output_dir: str = "output") -> str:
    """Download only the audio from a video as an m4a file.

    Params:
      url (str, required) — full video URL
      output_dir (str, default 'output') — directory path to save the file
    Returns the file path on success or an error message.
    """
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        "format": "m4a/bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "m4a"}],
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            audio_path = os.path.splitext(filename)[0] + ".m4a"
            return f"Downloaded audio: {audio_path}"
    except Exception as e:
        return f"Error: {e}"
