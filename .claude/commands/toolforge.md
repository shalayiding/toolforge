---
name: toolforge
description: Find a GitHub repository (or accept a URL) and convert it into a callable tool registered in the shared registry.
---

Convert a GitHub repository into a callable tool registered in the shared registry.

The user provides a GitHub URL, or describes what they need and Claude finds the right repo via github-search. Before doing anything, check if an existing tool already covers the need.

---

## Step 0 — Check the Registry First

Before cloning anything, call `search_tools(query)` with a description of what the repo does.

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

## Step 1 — Check Prerequisites

```bash
python --version
git --version
```

Both must be available. If not, tell the user and stop.

---

## Step 2 — Clone

```bash
mkdir -p ./temp
git clone {github_url} ./temp/{repo_name}
```

---

## Step 3 — Read and Understand the Repo

Read the following files carefully:
- `README.md` — what does this tool do? what are the main use cases?
- `pyproject.toml` or `requirements.txt` or `package.json` — package name and dependencies
- The main source files — understand the actual functions, classes, CLI interface

Answer these questions before proceeding:
1. What does this tool DO in one sentence?
2. What are the 2–5 most useful operations it performs?
3. How is it called? (importable Python API / CLI / HTTP)
4. What are the inputs and outputs of each operation?

---

## Step 4 — Decide: Is This Wrappable?

**Wrappable — continue:**
- Python package with importable functions or classes
- CLI tool with clear inputs and outputs
- HTTP API (use httpx to call it)

**Not wrappable — stop and explain:**
- Pure documentation or dataset
- Frontend-only app (no backend logic)
- No clear callable interface

---

## Step 5 — Install into the Shared Venv

All packages go into the single shared venv managed by uv at `./.venv/`.

```bash
uv pip install ./temp/{repo_name} --quiet
```

If that fails (no `pyproject.toml` or `setup.py`):

```bash
uv pip install -r ./temp/{repo_name}/requirements.txt --quiet
```

---

## Step 6 — Generate the Tool Module

Write `./temp/{repo_name}_tools.py` — a plain Python module with regular functions. No FastMCP, no decorators.

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

## Step 7 — Verify and Register

Run a quick import check:

**Mac/Linux:**
```bash
./.venv/bin/python -c "import importlib.util; spec = importlib.util.spec_from_file_location('t', './temp/{repo_name}_tools.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('OK')"
```

**Windows:**
```bash
./.venv/Scripts/python -c "import importlib.util; spec = importlib.util.spec_from_file_location('t', './temp/{repo_name}_tools.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('OK')"
```

If it prints `OK`, do two things for each function in the module:

**1. Append to `./registry/seeds.json`** — this is the source of truth for tool configs:

```json
{
  "tool_name": "{tool_name}",
  "description": "{full description including: what it does, each param name/type/default/meaning, and return value format}",
  "module_path": "temp/{repo_name}_tools.py",
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

Use a relative path for `module_path` (starting with `temp/`). Read the existing `seeds.json`, append the new entries, and write it back.

**2. Call `register_tool()` to load it into the live registry immediately:**

```
register_tool(
  tool_name     = "{tool_name}",
  description   = "{same full description as above}",
  module_path   = "{absolute path to ./temp/{repo_name}_tools.py}",
  function_name = "{function_name}",
  repo          = "{repo_name}",
  github_url    = "{https://github.com/owner/repo}",
  parameters    = { ... same parameters dict as above ... },
)
```

`seeds.json` persists the config for future re-seeding. `register_tool()` activates it in the current session. Do both.

---

## Step 8 — Tell the User

```
Done. {N} tools from '{repo_name}' are now in the registry.

To use them: call search_tools("{what it does}") — the registry will find them.
No restart needed.
```

---

## Step 9 — (Optional) Contribute to Community

**Skip this step if `./community/{repo_name}_tools.py` already exists** — the tool is already shared.

If this is a new repo not yet in `community/`, and it's a well-known public library that works cleanly after `pip install`, offer to contribute it:

1. Copy `./temp/{repo_name}_tools.py` → `./community/{repo_name}_tools.py`
2. Add the package(s) to `./community/requirements.txt`
3. Append the tool entries to `./community/seeds.json` with `"module_path": "community/{repo_name}_tools.py"`

Then commit `community/` to git. New users running `seed_registry.py --community` will get these tools automatically.
