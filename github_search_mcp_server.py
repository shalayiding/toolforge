import httpx
from fastmcp import FastMCP

mcp = FastMCP("github-search")

GITHUB_API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}


@mcp.tool()
def search_repos(
    query: str,
    language: str = "",
    min_stars: int = 0,
    top_k: int = 5,
) -> list[dict]:
    """Search GitHub for public repositories by description or keyword.

    Returns a list of repos with name, description, stars, URL, and language.
    Use this to find a repo before running /repoforge on it.

    Params:
      query     — what you're looking for, e.g. 'bilibili subtitle extraction python'
      language  — filter by language, e.g. 'python' or 'javascript' (optional)
      min_stars — only return repos with at least this many stars (optional)
      top_k     — number of results to return (default 5, max 10)
    """
    q = query
    if language:
        q += f" language:{language}"
    if min_stars:
        q += f" stars:>={min_stars}"

    try:
        resp = httpx.get(
            f"{GITHUB_API}/search/repositories",
            params={"q": q, "sort": "stars", "order": "desc", "per_page": min(top_k, 10)},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return [
            {
                "name": r["full_name"],
                "description": r.get("description") or "",
                "stars": r["stargazers_count"],
                "url": r["html_url"],
                "language": r.get("language") or "",
                "updated": r["updated_at"][:10],
            }
            for r in items
        ]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def get_repo_readme(owner: str, repo: str) -> str:
    """Fetch the README of a GitHub repository as plain text.

    Use this to understand what a repo does before running /repoforge on it.

    Params:
      owner — GitHub username or org, e.g. 'openai'
      repo  — repository name, e.g. 'whisper'
    """
    try:
        resp = httpx.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/readme",
            headers={**HEADERS, "Accept": "application/vnd.github.raw+json"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
