import base64
from pathlib import Path

import httpx

MERMAID_INK = "https://mermaid.ink"


def _encode(diagram: str) -> str:
    return base64.urlsafe_b64encode(diagram.encode("utf-8")).decode("utf-8")


def render_diagram(diagram: str, output_path: str, fmt: str = "png") -> str:
    """Render a Mermaid diagram to a PNG or SVG image file using the mermaid.ink API.
    No local installation required.
    Params:
      diagram (str, required) — Mermaid diagram source code e.g. 'flowchart TD\\n A --> B'
      output_path (str, required) — absolute path to save the output file e.g. '/path/to/flow.png'
      fmt (str, default 'png') — output format: 'png' or 'svg'
    Returns the saved file path on success, or an error message.
    """
    try:
        encoded = _encode(diagram)
        url = f"{MERMAID_INK}/svg/{encoded}" if fmt == "svg" else f"{MERMAID_INK}/img/{encoded}"
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(resp.content)
        return f"Saved to {out}"
    except Exception as e:
        return f"Error: {e}"


def render_diagram_url(diagram: str, fmt: str = "png") -> str:
    """Get the mermaid.ink URL for a Mermaid diagram without downloading it.
    Useful for embedding diagrams in Markdown as image URLs.
    Params:
      diagram (str, required) — Mermaid diagram source code
      fmt (str, default 'png') — 'png' or 'svg'
    Returns the full mermaid.ink URL that renders the diagram.
    """
    try:
        encoded = _encode(diagram)
        if fmt == "svg":
            return f"{MERMAID_INK}/svg/{encoded}"
        return f"{MERMAID_INK}/img/{encoded}"
    except Exception as e:
        return f"Error: {e}"
