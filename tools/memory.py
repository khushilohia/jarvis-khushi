import json
from pathlib import Path
from core.tools import tool

_MEM_FILE = Path.home() / ".jarvis_memory.json"


def _load() -> dict:
    if _MEM_FILE.exists():
        return json.loads(_MEM_FILE.read_text())
    return {"facts": [], "preferences": {}, "people": {}, "projects": {}}


def _save(m: dict):
    _MEM_FILE.write_text(json.dumps(m, indent=2))


@tool(
    name="remember",
    description="Permanently store something about the user — a preference, person, project, or fact. Call automatically when user shares personal info.",
    parameters={
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": ["preference", "person", "project", "fact"]},
            "content": {"type": "string"},
            "key": {"type": "string", "description": "Short label (optional for facts)."},
        },
        "required": ["category", "content"],
    },
)
def remember(category: str, content: str, key: str = "") -> str:
    m = _load()
    cat_map = {"preference": "preferences", "person": "people", "project": "projects", "fact": "facts"}
    cat = cat_map.get(category, "facts")
    if cat == "facts":
        if content not in m["facts"]:
            m["facts"].append(content)
    else:
        m[cat][key or content[:40]] = content
    _save(m)
    return "Got it."


@tool(
    name="recall",
    description="Search long-term memory for information about the user.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Topic to search (empty = summarize all)."},
        },
    },
)
def recall(query: str = "") -> str:
    m = _load()
    q = query.lower().strip()
    found = []
    for cat in ("preferences", "people", "projects"):
        for k, v in m[cat].items():
            if not q or q in f"{k} {v}".lower():
                found.append(f"{k}: {v}")
    for f in m["facts"]:
        if not q or q in f.lower():
            found.append(f)
    return "I know: " + "; ".join(found) if found else "Nothing stored yet."


@tool(
    name="forget",
    description="Remove stored memories matching a topic.",
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
        },
        "required": ["topic"],
    },
)
def forget(topic: str) -> str:
    m = _load()
    q = topic.lower().strip()
    removed = 0
    for cat in ("preferences", "people", "projects"):
        for k in list(m[cat]):
            if q in f"{k} {m[cat][k]}".lower():
                del m[cat][k]; removed += 1
    before = len(m["facts"])
    m["facts"] = [f for f in m["facts"] if q not in f.lower()]
    removed += before - len(m["facts"])
    _save(m)
    return f"Forgot {removed} item(s)." if removed else "Nothing to forget."
