import json


def get_top_news(
    country: str = "US",
    language: str = "en",
    period: str = "1d",
    max_results: int = 10,
) -> str:
    """Fetch top news headlines from Google News.
    Returns a JSON list of articles, each with: title, url, published_date, publisher, description.
    Params:
      country (str, default 'US') — 2-letter country code e.g. 'US', 'CN', 'GB', 'DE'
      language (str, default 'en') — language code e.g. 'en', 'zh', 'de', 'fr'
      period (str, default '1d') — time window: '1h', '1d', '7d', '30d'
      max_results (int, default 10) — number of articles to return (max 100)
    """
    try:
        from gnews import GNews
        gn = GNews(language=language, country=country, period=period, max_results=max_results)
        raw = gn.get_top_news()
        results = []
        for item in raw:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "published_date": item.get("published date", ""),
                "publisher": item.get("publisher", {}).get("title", "") if isinstance(item.get("publisher"), dict) else str(item.get("publisher", "")),
                "description": item.get("description", ""),
            })
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error: {e}"


def search_news(
    query: str,
    language: str = "en",
    country: str = "US",
    period: str = "7d",
    max_results: int = 10,
) -> str:
    """Search news articles by keyword/topic using Google News.
    Returns a JSON list of articles with: title, url, published_date, publisher, description.
    Params:
      query (str, required) — search keywords e.g. 'AI regulation', 'Apple earnings'
      language (str, default 'en') — language code e.g. 'en', 'zh', 'de'
      country (str, default 'US') — 2-letter country code
      period (str, default '7d') — time window: '1h', '1d', '7d', '30d'
      max_results (int, default 10) — number of results (max 100)
    """
    try:
        from gnews import GNews
        gn = GNews(language=language, country=country, period=period, max_results=max_results)
        raw = gn.get_news(query)
        results = []
        for item in raw:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "published_date": item.get("published date", ""),
                "publisher": item.get("publisher", {}).get("title", "") if isinstance(item.get("publisher"), dict) else str(item.get("publisher", "")),
                "description": item.get("description", ""),
            })
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error: {e}"


def get_article(url: str) -> str:
    """Fetch and parse a full news article from a URL.
    Returns JSON with: title, text (full body up to 3000 chars), authors, publish_date, top_image, url.
    Params:
      url (str, required) — full article URL e.g. 'https://www.bbc.com/news/...'
    """
    try:
        import newspaper
        article = newspaper.article(url)
        return json.dumps({
            "title": article.title,
            "authors": article.authors,
            "publish_date": str(article.publish_date) if article.publish_date else None,
            "text": article.text[:3000] if article.text else "",
            "top_image": article.top_image,
            "url": article.url,
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error: {e}"
