import asyncio
import logging
import os
from typing import Optional

import maigret
from maigret.sites import MaigretDatabase

# Find the database bundled with the pip-installed package.
# Falls back to a locally cloned repo under temp/ if the package path doesn't exist.
_pkg_db = os.path.join(os.path.dirname(maigret.__file__), "resources", "data.json")
_clone_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp", "maigret", "maigret", "resources", "data.json")
DB_PATH = _pkg_db if os.path.exists(_pkg_db) else _clone_db


def _load_db(top: int = 500, tags: list[str] = []) -> dict:
    db = MaigretDatabase().load_from_path(DB_PATH)
    return db.ranked_sites_dict(top=top, tags=tags, disabled=False, id_type="username")


async def search_username(
    username: str,
    top_sites: int = 500,
    tags: Optional[str] = None,
    timeout: int = 30,
) -> dict:
    """Search for a username across social networks and websites.
    Returns a dict of site names to {status, url, tags}.
    Status values: CLAIMED (found), NOT_FOUND, ERROR.
    Params:
      username (str, required) — the username to search for
      top_sites (int, default 500) — how many sites to check (max 500)
      tags (str, optional) — comma-separated filter tags e.g. 'social,photo'
      timeout (int, default 30) — seconds per request
    """
    logger = logging.getLogger("maigret")
    logger.setLevel(logging.WARNING)

    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    site_dict = _load_db(top=top_sites, tags=tag_list)

    results = await maigret.search(
        username=username,
        site_dict=site_dict,
        logger=logger,
        timeout=timeout,
        id_type="username",
        no_progressbar=True,
    )

    output = {}
    for site_name, data in results.items():
        status = data.get("status")
        if status:
            output[site_name] = {
                "status": str(status.status.name),
                "url": data.get("url_user", ""),
                "tags": list(status.tags) if status.tags else [],
            }
    return output


async def search_username_claimed_only(
    username: str,
    top_sites: int = 500,
    tags: Optional[str] = None,
    timeout: int = 30,
) -> list[dict]:
    """Search for a username and return ONLY confirmed accounts (CLAIMED status).
    Returns a list of {site, url, tags}. Best tool when you just want to know where someone has accounts.
    Params:
      username (str, required) — the username to search for
      top_sites (int, default 500) — how many sites to check
      tags (str, optional) — comma-separated filter e.g. 'social,gaming'
      timeout (int, default 30) — seconds per request
    """
    all_results = await search_username(username, top_sites, tags, timeout)
    return [
        {"site": site, "url": data["url"], "tags": data["tags"]}
        for site, data in all_results.items()
        if data["status"] == "CLAIMED"
    ]


def list_available_tags() -> list[str]:
    """List all available site category tags that can be used to filter username searches.
    Returns a sorted list of tag strings such as 'social', 'gaming', 'photo', 'music', 'dating'.
    No parameters required.
    """
    db = MaigretDatabase().load_from_path(DB_PATH)
    tags = set()
    for site in db.sites:
        if site.tags:
            tags.update(site.tags)
    return sorted(tags)
