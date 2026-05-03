"""Generate .mcp.json with absolute paths for the current machine."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent.resolve()

# uv creates .venv by default
if sys.platform == "win32":
    python = BASE / ".venv" / "Scripts" / "python.exe"
else:
    python = BASE / ".venv" / "bin" / "python"

if not python.exists():
    print(f"ERROR: {python} not found. Run 'uv sync' first.")
    sys.exit(1)

config = {
    "mcpServers": {
        "toolforge-registry": {
            "type": "stdio",
            "command": str(python),
            "args": [str(BASE / "registry" / "registry_mcp.py")],
            "env": {}
        },
        "github-search": {
            "type": "stdio",
            "command": str(python),
            "args": [str(BASE / "github_search_mcp_server.py")],
            "env": {}
        }
    }
}

out = BASE / ".mcp.json"
out.write_text(json.dumps(config, indent=2), encoding="utf-8")
print(f"Generated {out}")
