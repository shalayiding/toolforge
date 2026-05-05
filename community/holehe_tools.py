import trio
import httpx

from holehe.core import import_submodules, get_functions, launch_module


async def _run_holehe(email: str, timeout: int) -> list[dict]:
    modules = import_submodules("holehe.modules")
    websites = get_functions(modules)
    client = httpx.AsyncClient(timeout=timeout)
    out = []
    async with trio.open_nursery() as nursery:
        for website in websites:
            nursery.start_soon(launch_module, website, email, client, out)
    await client.aclose()
    return sorted(out, key=lambda x: x["name"])


def check_email_registrations(email: str, timeout: int = 10) -> list[dict]:
    """Check which websites an email address is registered on using holehe.
    Queries 120+ sites (social, gaming, music, mail, etc.) via password-recovery probing.
    Returns a list of dicts with keys: name, domain, exists (bool), rateLimit (bool),
    emailrecovery, phoneNumber, others. Use check_email_claimed_only() to get only confirmed hits.
    Params:
      email (str, required) — target email address to search
      timeout (int, default 10) — per-request timeout in seconds
    """
    return trio.run(_run_holehe, email, timeout)


def check_email_claimed_only(email: str, timeout: int = 10) -> list[dict]:
    """Check which websites an email address is registered on and return ONLY confirmed hits.
    Returns a list of dicts with keys: name, domain, emailrecovery, phoneNumber, others.
    Skips sites with rate limits or errors. Best when you just want to know where an email has accounts.
    Params:
      email (str, required) — target email address to search
      timeout (int, default 10) — per-request timeout in seconds
    """
    all_results = trio.run(_run_holehe, email, timeout)
    return [
        {
            "name": r["name"],
            "domain": r["domain"],
            "emailrecovery": r.get("emailrecovery"),
            "phoneNumber": r.get("phoneNumber"),
            "others": r.get("others"),
        }
        for r in all_results
        if r.get("exists") is True
    ]
