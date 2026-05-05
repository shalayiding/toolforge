# Community Tools

Pre-built tools included with ToolForge. Load them with:

```bash
uv run python registry/seed_registry.py --community
```

---

| Tool | Repo | What it does |
|------|------|-------------|
| `get_stock_price` | yfinance | Current price for a ticker symbol |
| `get_multiple_stock_prices` | yfinance | Prices for a list of tickers |
| `get_stock_history` | yfinance | Historical OHLCV data for a ticker |
| `get_transcript_text` | youtube-transcript-api | Full transcript of a YouTube video as plain text |
| `get_transcript_with_timestamps` | youtube-transcript-api | Transcript with per-line timestamps |
| `list_available_transcripts` | youtube-transcript-api | Available languages for a video |
| `fetch_article` | newspaper4k | Full text + title + summary of a news article URL |
| `search_news` | gnews | Recent news articles by keyword |
| `get_top_news` | gnews | Top headlines by topic/country |
| `render_mermaid_png` | mermaid.ink | Render a Mermaid diagram string to PNG (returns URL) |
| `render_mermaid_svg` | mermaid.ink | Render a Mermaid diagram string to SVG (returns URL) |
| `search_username` | maigret | Search a username across 500+ social sites |
| `search_username_claimed_only` | maigret | Same as above, returns only confirmed accounts |
| `list_available_tags` | maigret | List available site category tags for filtering |
| `check_email_registrations` | holehe | Check which of 120+ sites an email is registered on |
| `check_email_claimed_only` | holehe | Same as above, confirmed hits only |
| `download_video` | yt-dlp | Download a video from YouTube or 1000+ supported sites |
| `get_video_info` | yt-dlp | Fetch video metadata without downloading |
| `download_audio` | yt-dlp | Download audio only as m4a |
