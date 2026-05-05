---
name: toolforge
description: Find a GitHub repository (or accept a URL) and convert it into a callable tool registered in the shared registry.
---

Convert a GitHub repository into a callable tool registered in the shared registry.

The user provides a GitHub URL, or describes what they need and Claude finds the right repo via github-search. Before doing anything, check if an existing tool already covers the need.

---

## Step 0 — Check the Registry First

Before doing anything else, call `search_tools(query)` with a description of what the repo does.

**Similarity < 0.5** → no useful match, continue to Step 1.

**Similarity ≥ 0.5** → a semantically similar tool exists, but do NOT stop yet.
Read its `description` and `parameters` carefully and ask:
- Does it actually support the specific input? (e.g. bilibili URL vs YouTube URL)
- Does it have the capability needed? (e.g. subtitle extraction vs just metadata)
- Would calling it with the user's input succeed, or fail silently?

If yes to all → tell the user which tool matches and use it directly. Stop here.
If no (wrong platform, missing feature, parameter mismatch) → the similarity is misleading. Continue to Step 1 anyway.

**The test is not "is it similar?" but "will it actually work for this specific request?"**

---

## Step 1 — Find the Repo

**If the user already provided a GitHub URL** → skip directly to Step 2.

**If no URL was given**, use `search_repos(query)` from the github-search MCP to find a suitable library.

Try at least **5 different queries** before concluding no library exists. Vary the terms:
- Task domain: `"email registration checker"`, `"osint email lookup"`
- Action + noun: `"check email sites"`, `"email footprint"`, `"pdf text extraction"`
- Related synonyms or known tool names if the user mentioned one

If after 5 queries nothing wrappable is found (importable Python package, CLI, or HTTP API), tell the user why and stop. **Do NOT fall back to implementing the task yourself using Claude's own knowledge.**

---

## Step 2 — Check Prerequisites

```bash
python --version
git --version
```

Both must be available. If not, tell the user and stop.

---

## Step 3 — Clone the Repo

Always clone the source code — the README alone is not enough to understand the exact API:

```bash
git clone {github_url} ./community/{repo_name}
```

The cloned source stays in `community/{repo_name}/` for reference. It is gitignored (nested `.git` dirs are not tracked by the parent repo).

---

## Step 4 — Read and Understand the Repo

Read these files from `./community/{repo_name}/`:
- `README.md` — what does this tool do? what are the main use cases?
- `pyproject.toml` or `requirements.txt` or `package.json` — package name and dependencies
- The main source files — actual functions, classes, CLI interface, async patterns

Answer these questions before proceeding:
1. What does this tool DO in one sentence?
2. What are the 2–5 most useful operations it performs?
3. How is it called? (importable Python API / CLI / HTTP)
4. What are the exact function signatures, arguments, and return types?

---

## Step 5 — Decide: Is This Wrappable?

**Wrappable — continue:**
- Python package with importable functions or classes
- CLI tool with clear inputs and outputs
- HTTP API (use httpx to call it)

**Not wrappable — stop and explain:**
- Pure documentation or dataset
- Frontend-only app (no backend logic)
- No clear callable interface

---

## Step 6 — Install into the Shared Venv

All packages go into the single shared venv managed by uv at `./.venv/`.

**For pip packages (most common):**
```bash
uv pip install {package_name} --quiet
```

**For source-only packages (no pip release):**
```bash
uv pip install ./community/{repo_name} --quiet
```

If that fails (no `pyproject.toml` or `setup.py`):
```bash
uv pip install -r ./community/{repo_name}/requirements.txt --quiet
```

---

## Step 7 — Generate the Tool Module

Write `./community/{repo_name}_tools.py` — a plain Python module with regular functions. No FastMCP, no decorators.

**For a Python package (import and call directly):**

```python
import {package_name}

def {tool_name}({param}: {type}) -> {return_type}:
    """{clear description of what this tool does}"""
    result = {package_name}.{function}({param})
    return result
```

**For a CLI tool (subprocess):**

```python
import subprocess

def {tool_name}({param}: str) -> str:
    """{clear description of what this tool does}"""
    result = subprocess.run(
        ["{cli_command}", {args}],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        return f"Error: {result.stderr}"
    return result.stdout
```

**For an HTTP API (httpx):**

```python
import httpx

def {tool_name}({param}: str) -> str:
    """{clear description of what this tool does}"""
    resp = httpx.get(f"https://api.example.com/{param}", timeout=30)
    resp.raise_for_status()
    return resp.text
```

**Rules when writing the module:**
- Expose only the 2–5 most useful operations as functions
- Write clear docstrings — Claude reads these to decide what to call
- Use proper Python type hints on all parameters and return values
- For async functions in the underlying package, use `async def` and `await`
- Return errors as strings rather than raising exceptions
- Keep it simple — no extra abstraction, no FastMCP

---

## Step 8 — Verify and Register

Run a quick import check:

**Mac/Linux:**
```bash
./.venv/bin/python -c "import importlib.util; spec = importlib.util.spec_from_file_location('t', './community/{repo_name}_tools.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('OK')"
```

**Windows:**
```bash
./.venv/Scripts/python -c "import importlib.util; spec = importlib.util.spec_from_file_location('t', './community/{repo_name}_tools.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('OK')"
```

If it prints `OK`, also run a quick **functional test** by calling one of the functions with a real input to confirm it actually works before registering.

Then do three things:

**1. Append to `./community/seeds.json`:**

```json
{
  "tool_name": "{tool_name}",
  "description": "{full description including: what it does, each param name/type/default/meaning, and return value format}",
  "module_path": "community/{repo_name}_tools.py",
  "function_name": "{function_name}",
  "repo": "{repo_name}",
  "github_url": "{https://github.com/owner/repo}",
  "parameters": {
    "{param_name}": {
      "type": "string|integer|boolean",
      "required": true,
      "description": "{what this param does}",
      "default": "{default value if optional}"
    }
  }
}
```

**Description must be self-contained** — include param names, types, and what each does. This is the only info Claude has when deciding how to call the tool; don't make it go read source files.

**2. Add the package to `./community/requirements.txt`** so new users get it via `seed_registry.py --community`.

**3. Call `register_tool()` to load it into the live registry immediately:**

```
register_tool(
  tool_name     = "{tool_name}",
  description   = "{same full description as above}",
  module_path   = "{absolute path to ./community/{repo_name}_tools.py}",
  function_name = "{function_name}",
  repo          = "{repo_name}",
  github_url    = "{https://github.com/owner/repo}",
  parameters    = { ... same parameters dict as above ... },
)
```

`community/seeds.json` persists the config for future re-seeding. `register_tool()` activates it in the current session. Do both.

---

## Step 9 — Tell the User

```
Done. {N} tools from '{repo_name}' are now in the registry.

To use them: call search_tools("{what it does}") — the registry will find them.
No restart needed.
```
