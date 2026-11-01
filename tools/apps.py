import subprocess
from core.tools import tool


@tool(
    name="open_app",
    description="Open an application or URL on this Mac. Use for 'open Safari', 'launch Spotify', 'open youtube.com'.",
    parameters={
        "type": "object",
        "properties": {
            "name_or_url": {"type": "string", "description": "App name or URL to open."},
        },
        "required": ["name_or_url"],
    },
)
def open_app(name_or_url: str) -> str:
    r = subprocess.run(["open", name_or_url], capture_output=True, text=True)
    return f"Opened {name_or_url}." if r.returncode == 0 else f"Failed: {r.stderr.strip()}"
