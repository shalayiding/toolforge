# ToolForge

This is the ToolForge project — a self-expanding AI toolbox. When you receive any user request in this repo, **always check the tool registry first** before doing anything else.

---

## Setup (for new users)

If the user says "set up this project", "help me install", or the MCP servers aren't responding, guide them through these steps one at a time. Check each step before moving to the next.

### Step 1 — Check prerequisites

Ask the user to run:
```bash
python --version
uv --version
git --version
```

- Python must be 3.10+. If missing: https://www.python.org/downloads/
- uv must be installed. If missing: `pip install uv` or https://docs.astral.sh/uv/getting-started/installation/
- git must be installed. If missing: https://git-scm.com/

### Step 2 — Install dependencies

```bash
uv sync
```

This creates `.venv/` and installs all packages from `pyproject.toml`. If it fails, check that `pyproject.toml` exists in the current directory.

### Step 3 — Generate `.mcp.json`

```bash
uv run python setup_mcp.py
```

This writes `.mcp.json` with absolute paths that work on this specific machine. Must be re-run whenever the project is moved to a new location.

### Step 4 — Restart Claude Code ⚠️

**This step is mandatory.** MCP servers are only loaded at startup. Tell the user to fully close and reopen Claude Code (or use the "Reload Window" command). Do not skip or work around this — the tools will not be available until Claude Code restarts.

### Step 5 — Verify with /mcp

Ask the user to run `/mcp` in Claude Code. They must see both servers listed as connected:

```
✓ toolforge-registry
✓ github-search
```

If either is missing: re-run `setup_mcp.py` and restart Claude Code again. Do not proceed until both are confirmed connected.

### Step 6 — (Optional) Load tools

**Option A — community tools** (recommended for new users): loads the pre-built tools included in this repo (see `community/TOOLS.md` for the full list):
```bash
uv run python registry/seed_registry.py --community
```

**Option B — restore personal seeds** from a previous machine (`registry/seeds.json`):
```bash
uv run python registry/seed_registry.py
```

Both commands rebuild ChromaDB and register tools into the live registry.

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `toolforge-registry` tool not found | Re-run `setup_mcp.py`, restart Claude Code |
| `uv sync` fails | Check Python 3.10+ is active, `pyproject.toml` exists |
| `list_all_tools()` returns empty | Normal on fresh install — use `/toolforge` to add tools |
| Tools registered but `call_tool()` fails | Check `community/` folder exists; the tool module may be missing |

---

## Your primary behavior in this repo

**Before writing code, searching the web, or doing anything manually — ask: does a registered tool already cover this?**

```
1. Call search_tools("describe what the user needs")
2. If similarity ≥ 0.5 → verify the tool actually fits (platform, params, capability)
   - YES → call_tool() immediately
   - NO  → continue to step 3
3. If no match → search GitHub with github-search MCP (search_repos + get_repo_readme)
   - Try at least 5 different queries before giving up
   - Vary the query: library name, domain term, action verb, related synonyms
4. If a suitable repo is found → run /toolforge to wrap and register it
5. Then call_tool() to use it
6. ONLY if after 5+ GitHub searches no wrappable library exists → explain to the user
   why no tool is available and offer alternative approaches
```

**Do NOT fall back to writing code, using Claude's built-in knowledge, or calling web APIs directly** when the task is something a library could do. Always try to find and forge a tool first. The point of this project is that Claude acquires tools — not that Claude improvises.

Never manually reimplement something a registered tool can already do.

---

## Available MCP tools

### toolforge-registry (always check this first)
- `search_tools(query)` — semantic search over all registered tools. Returns similarity scores + full parameter descriptions. One call is enough to know if a tool exists and how to call it.
- `call_tool(tool_name, args)` — execute any registered tool by name. Dynamic import, no restart needed.
- `register_tool(tool_name, description, module_path, function_name, repo, parameters)` — add a new tool to the registry. Called at the end of /toolforge.
- `list_all_tools()` — list everything currently registered.
- `delete_tool(tool_name)` — remove a single tool from the registry and vector index.
- `clear_registry()` — remove all tools. Irreversible unless seeds.json exists.

### github-search (use when no registry match)
- `search_repos(query, language, min_stars, top_k)` — search GitHub by description. No token needed.
- `get_repo_readme(owner, repo)` — read a repo's README to evaluate before wrapping.

---

## Project architecture

```
.mcp.json                        ← two MCP servers: toolforge-registry + github-search
│
├── registry/
│   ├── registry_mcp.py          ← the toolforge-registry MCP server
│   ├── seed_registry.py         ← rebuilds ChromaDB from seeds.json
│   └── seeds.json               ← user's personal tool configs (gitignored)
│
├── community/                   ← all tool modules live here (tracked in git)
│   ├── *_tools.py               ← plain Python wrappers generated by /toolforge
│   ├── TOOLS.md                 ← list of all included community tools
│   ├── {repo_name}/             ← cloned source code for reference (gitignored)
│   ├── seeds.json               ← community tool configs
│   └── requirements.txt         ← pip deps for all community tools
│
├── github_search_mcp_server.py  ← the github-search MCP server
├── setup_mcp.py                 ← generates .mcp.json with correct absolute paths
└── .claude/commands/toolforge.md ← the /toolforge skill
```

### How tools are stored
- **ChromaDB** (`registry/chroma_db/`) — vector index for `search_tools()`. Embeddings generated by all-MiniLM-L6-v2.
- **tool_registry.json** — maps tool names to module paths and function names for `call_tool()`.
- **seeds.json** — human-readable source of truth. Run `seed_registry.py` to rebuild everything from scratch.

### How a tool gets added (/toolforge flow)
1. Check registry (avoid duplicates)
2. Clone source to `community/<repo>/` — always needed to understand the actual API
3. `uv pip install <package>` (or install from cloned source if not on pip)
4. Generate `community/<repo>_tools.py` (plain Python functions, no FastMCP)
5. Test functionally, then `register_tool()` + append to `community/seeds.json`

---

## When to use /toolforge

Use `/toolforge` when:
- A user needs a capability that isn't in the registry
- You've searched GitHub and found a suitable Python library or HTTP API
- The repo is wrappable (importable Python package, CLI, or HTTP API)

Do NOT use `/toolforge` for:
- Pure documentation repos
- Frontend-only apps
- Things Claude can do natively (writing code, answering questions, analysis)

---

## Similarity threshold guidance

`search_tools()` returns similarity scores from 0 to 1:
- **≥ 0.7** — strong match, likely the right tool
- **0.5–0.7** — possible match, read description carefully before using
- **< 0.5** — no useful match, go to GitHub

High similarity does not mean the tool works for this specific request. Always verify platform compatibility and parameter fit before calling.
