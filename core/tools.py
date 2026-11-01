import json
from typing import Callable

REGISTRY: dict[str, dict] = {}


def tool(name: str, description: str, parameters: dict):
    def decorator(fn: Callable):
        REGISTRY[name] = {"fn": fn, "schema": parameters, "description": description}
        return fn
    return decorator


def tool_schemas() -> list[dict]:
    return [
        {
            "name": name,
            "description": entry["description"],
            "input_schema": entry["schema"],
        }
        for name, entry in REGISTRY.items()
    ]


def dispatch(name: str, args: dict) -> str:
    entry = REGISTRY.get(name)
    if not entry:
        return f"Unknown tool: {name}"
    try:
        return str(entry["fn"](**args))
    except Exception as e:
        return f"Tool error: {e}"
