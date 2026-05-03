import asyncio
import importlib.util
import json
from pathlib import Path
from typing import Any, Optional

import chromadb
from fastmcp import FastMCP

mcp = FastMCP("toolforge-registry")

REGISTRY_DIR = Path(__file__).parent
REGISTRY_FILE = REGISTRY_DIR / "tool_registry.json"
CHROMA_DIR = REGISTRY_DIR / "chroma_db"

_chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_collection = _chroma_client.get_or_create_collection(
    name="tools",
    metadata={"hnsw:space": "cosine"},
)

_module_cache: dict = {}


def _load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {}
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def _save_registry(registry: dict) -> None:
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _get_module(module_path: str):
    if module_path not in _module_cache:
        spec = importlib.util.spec_from_file_location("_dyn", module_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _module_cache[module_path] = mod
    return _module_cache[module_path]


@mcp.tool()
def search_tools(query: str, top_k: int = 5) -> list[dict]:
    """Search registered tools by describing what you need in natural language.

    Returns tools ranked by similarity (0–1). Similarity >= 0.5 means a usable
    match exists — call it directly. Below 0.5, consider finding a new repo.
    """
    count = _collection.count()
    if count == 0:
        return []

    results = _collection.query(
        query_texts=[query],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )

    registry = _load_registry()
    output = []
    for tool_id, doc, meta, dist in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "tool_name": tool_id,
            "repo": meta.get("repo", ""),
            "description": doc,
            "parameters": registry.get(tool_id, {}).get("parameters", {}),
            "similarity": round(1 - dist, 3),
        })
    return output


@mcp.tool()
def call_tool(tool_name: str, args: Optional[dict] = None) -> Any:
    """Execute a registered tool by name.

    Use search_tools() first to find the right tool_name.
    """
    registry = _load_registry()
    if tool_name not in registry:
        return f"Error: '{tool_name}' not found. Use search_tools() to see what's available."

    info = registry[tool_name]
    module = _get_module(info["module_path"])
    func = getattr(module, info["function_name"])

    kwargs = args or {}
    if asyncio.iscoroutinefunction(func):
        return asyncio.run(func(**kwargs))
    return func(**kwargs)


@mcp.tool()
def register_tool(
    tool_name: str,
    description: str,
    module_path: str,
    function_name: str,
    repo: str,
    parameters: Optional[dict] = None,
) -> str:
    """Register a tool into the registry and vector index.

    Called automatically by /toolforge after generating an MCP server.
    module_path must be the absolute path to the _mcp_server.py file.
    """
    registry = _load_registry()
    registry[tool_name] = {
        "module_path": module_path,
        "function_name": function_name,
        "description": description,
        "repo": repo,
        "parameters": parameters or {},
    }
    _save_registry(registry)

    _collection.upsert(
        ids=[tool_name],
        documents=[description],
        metadatas=[{"repo": repo, "function_name": function_name}],
    )
    return f"✅ Registered '{tool_name}' from repo '{repo}'"


@mcp.tool()
def list_all_tools() -> list[dict]:
    """List every tool currently registered in the registry."""
    registry = _load_registry()
    return [
        {
            "tool_name": name,
            "repo": info["repo"],
            "description": info["description"][:120] + "..."
            if len(info["description"]) > 120
            else info["description"],
        }
        for name, info in registry.items()
    ]


if __name__ == "__main__":
    mcp.run()
