<h1 align="center">ToolForge</h1>

<p align="center">
  <img src="docs/toolforge_logo.png" width="160" alt="ToolForge"/>
</p>

<h3 align="center">A self-expanding AI toolbox for Claude</h3>

<p align="center">
  Describe what you need — Claude finds the right library on GitHub,<br/>
  wraps it, and adds it to its own toolkit. No manual configuration required.
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh.md">中文</a>
</p>

---

## Contents

- [The core idea](#the-core-idea)
- [How it works](#how-it-works)
- [Architecture](#architecture)
- [Key strengths](#key-strengths)
- [Installation](#installation)
- [Adding a tool](#adding-a-tool)
- [Supported repo types](#supported-repo-types)

---

## The core idea

Most AI assistants have a fixed set of capabilities. ToolForge makes Claude's capabilities dynamic: when Claude can't do something, it finds a tool on GitHub, wraps it as an MCP service, and registers it — then uses it immediately and in every future session.

```
"Summarize this YouTube video"
        │
        ├─ search registry → no youtube tool found
        │
        ├─ search GitHub → finds youtube-transcript-api (10k+ stars)
        │
        ├─ /toolforge https://github.com/jdepoix/youtube-transcript-api
        │       clone → read → wrap → install → register
        │
        └─ call get_transcript_text("dQw4w9WgXcQ") → summarize
```

The next time someone asks about a YouTube video, the tool is already there.

---

## How it works

Every request goes through one of two flows:

<table>
  <tr>
    <th align="center">Flow A — Use Existing Tool</th>
    <th align="center">Flow B — Acquire New Tool</th>
  </tr>
  <tr>
    <td align="center" valign="top"><img src="docs/flow_a.png" width="380"/></td>
    <td align="center" valign="top"><img src="docs/flow_b.png" width="380"/></td>
  </tr>
  <tr>
    <td valign="top">

**When a tool might already exist.**

Claude searches the registry using natural language. If similarity ≥ 0.5, it doesn't just reuse the tool — it reads the description and parameters carefully to verify the tool actually fits the request (right platform, right capability, compatible inputs). Only then does it call the tool directly. If the match is misleading, it falls through to Flow B.

  </td>
    <td valign="top">

**When no suitable tool exists.**

Claude searches GitHub for the best library, reads its README to evaluate quality and wrappability, then runs `/toolforge` on it. The skill clones the repo, reads and understands the source, generates a plain Python tools module, installs the package into the shared `.venv`, and registers the tool in both ChromaDB (for future search) and `seeds.json` (for persistence). The tool is ready to use immediately — no restart needed.

  </td>
  </tr>
</table>

---

## Architecture

```
.mcp.json
│
├── toolforge-registry       ← single tool hub Claude talks to
│   ├── search_tools(query)  ← semantic search via ChromaDB (all-MiniLM-L6-v2)
│   ├── call_tool(name,args) ← dynamic import + execute, no restart needed
│   ├── register_tool(...)   ← add tool to registry + vector index at runtime
│   └── list_all_tools()
│
├── github-search            ← infrastructure MCP for autonomous tool discovery
│   ├── search_repos(query)  ← GitHub REST API, no token needed
│   └── get_repo_readme(owner, repo)
│
├── registry/
│   ├── registry_mcp.py      ← MCP server (framework, tracked in git)
│   ├── seed_registry.py     ← rebuilds ChromaDB from seeds.json
│   └── seeds.json           ← your personal tool configs (gitignored)
│
└── community/               ← pre-built tools shared with all users (tracked in git)
    ├── *_tools.py           ← plain Python tool modules (14 tools included)
    ├── seeds.json           ← community tool configs
    └── requirements.txt     ← pip deps for community tools
```

Only **two MCP entries** in `.mcp.json` regardless of how many tools you add.

---

## Key strengths

**Autonomous tool discovery.** Claude doesn't wait for you to find a GitHub URL. Describe the need — it searches GitHub, picks the best library, wraps it, and uses it.

**Capability-aware matching.** Before reusing an existing tool, Claude verifies it actually fits the request — not just that the description is semantically similar. A YouTube transcript tool won't be mistakenly used for Bilibili.

**Single registry entry point.** All tools live under one MCP server. Claude uses semantic search to route requests — no sprawling list of MCP configs to manage.

**Rich self-documenting tools.** Every registered tool stores its parameter names, types, defaults, and descriptions. Claude calls tools correctly from a single `search_tools()` result without reading source files.

**Persistent and portable.** `seeds.json` is the source of truth. Delete the vector DB and rebuild in seconds with `seed_registry.py`. Clone to a new machine, run setup, get the same environment.

---

## Installation

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| [Python](https://www.python.org/downloads/) | 3.10+ | python.org |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | latest | `pip install uv` |
| [git](https://git-scm.com/) | any | git-scm.com |
| [Claude Code](https://claude.ai/code) | latest | claude.ai/code |

### Option A — Manual setup

```bash
# 1. Clone the repo
git clone https://github.com/shalayiding/toolforge.git
cd toolforge

# 2. Install dependencies
uv sync

# 3. Generate .mcp.json with correct paths for your machine
uv run python setup_mcp.py
```

**4. Open the `toolforge` folder as the root in Claude Code** — Claude must be opened directly at the `toolforge` directory, not a parent folder or subfolder. This is how Claude picks up `CLAUDE.md` (project instructions) and `.claude/commands/` (the `/toolforge` skill).

**5. Restart Claude Code** — this step is required. The MCP servers are only loaded on startup. Without a restart, Claude won't see them.

**6. Verify both servers are connected** — run `/mcp` in Claude Code and confirm you see:

```
✓ toolforge-registry
✓ github-search
```

If either is missing, re-run `setup_mcp.py` and restart again.

> The registry starts empty on a fresh install — that's expected. Load the 14 included community tools with `uv run python registry/seed_registry.py --community`, or use `/toolforge` to add any GitHub repo.

### Option B — Let Claude install it

Open the `toolforge` folder in Claude Code **before** running any commands, then just say:

```
set up this project for me
```

Claude reads `CLAUDE.md`, knows the full setup steps, and walks you through the entire installation — including the restart reminder and `/mcp` verification.

### Option C — Load community tools

14 pre-built tools are included in the repo (yfinance, YouTube transcripts, news, Mermaid diagrams, OSINT). No tokens needed:

```bash
uv run python registry/seed_registry.py --community
```

### Option D — Restore your personal tools

If you have a `registry/seeds.json` from a previous machine:

```bash
uv run python registry/seed_registry.py
```

This rebuilds the vector database and restores all your registered tools in seconds.

---

## Adding a tool

**Option A — you know the repo:**
```
/toolforge https://github.com/owner/repo
```

**Option B — describe what you need:**
```
I need to extract text from PDF files
```
Claude searches GitHub, picks the best library, and runs `/toolforge` on it.

---

## Supported repo types

- Python packages with importable functions
- CLI tools (wrapped via subprocess)
- HTTP APIs (wrapped via httpx)

Not supported: frontend-only apps, pure datasets, repos with no callable interface.
