from core.tools import tool


@tool(
    name="web_search",
    description="Search the web for current information, news, weather, or facts you don't know.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query."},
        },
        "required": ["query"],
    },
)
def web_search(query: str) -> str:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return "duckduckgo_search not installed."
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return "No results found."
        return " ".join(r.get("body", "")[:300] for r in results)
    except Exception as e:
        return f"Search failed: {e}"
