import subprocess
from pathlib import Path
from core.tools import tool

_TG = Path.home() / ".claude" / "scripts" / "tg.sh"


@tool(
    name="send_telegram",
    description=(
        "Send an urgent Telegram message to the user. Use for emergencies, "
        "important alerts, or anything needing attention when away from desk. "
        "Do NOT use for routine replies."
    ),
    parameters={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Alert message, max ~200 chars."},
        },
        "required": ["message"],
    },
)
def send_telegram(message: str) -> str:
    if not _TG.exists():
        return f"Telegram script not found at {_TG}"
    r = subprocess.run(["bash", str(_TG), message], capture_output=True, text=True, timeout=15)
    return "Sent." if r.returncode == 0 else f"Failed: {r.stderr.strip()}"
