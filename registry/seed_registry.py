"""Seed registered tools into the registry.

Usage:
  uv run python registry/seed_registry.py              # personal seeds only
  uv run python registry/seed_registry.py --community  # also load shared community tools
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from registry_mcp import register_tool

BASE = Path(__file__).parent.parent
REGISTER_KEYS = {"tool_name", "description", "module_path", "function_name", "repo", "github_url", "parameters"}


def _load_and_register(seeds_file: Path) -> int:
    if not seeds_file.exists():
        print(f"  No seeds file at {seeds_file}, skipping.")
        return 0
    seeds = json.loads(seeds_file.read_text(encoding="utf-8"))
    count = 0
    for t in seeds:
        entry = {k: v for k, v in t.items() if k in REGISTER_KEYS}
        entry["module_path"] = str(BASE / entry["module_path"])
        register_tool(**entry)
        print(f"  Registered: {entry['tool_name']}")
        count += 1
    return count


community = "--community" in sys.argv

# Personal seeds
print("Loading personal seeds...")
n = _load_and_register(BASE / "registry" / "seeds.json")
print(f"  {n} tools registered from personal seeds.\n")

# Community seeds
if community:
    req_file = BASE / "community" / "requirements.txt"
    if req_file.exists():
        print("Installing community requirements...")
        subprocess.run(
            ["uv", "pip", "install", "-r", str(req_file), "--python", sys.executable],
            check=True,
        )
        print()

    print("Loading community seeds...")
    n = _load_and_register(BASE / "community" / "seeds.json")
    print(f"  {n} tools registered from community seeds.\n")

print("Done.")
