"""One-time script to seed existing tools into the registry."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from registry_mcp import register_tool

BASE = Path(__file__).parent.parent
SEEDS_FILE = Path(__file__).parent / "seeds.json"

seeds = json.loads(SEEDS_FILE.read_text(encoding="utf-8"))

for t in seeds:
    t["module_path"] = str(BASE / t["module_path"])
    register_tool(**t)
    print(f"Registered: {t['tool_name']}")

print("\nDone. All tools registered.")
