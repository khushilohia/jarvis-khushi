from datetime import datetime
from core.tools import tool


@tool(
    name="get_datetime",
    description="Returns the current date and time as a readable English string.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def get_datetime() -> str:
    return datetime.now().strftime("%A, %B %-d, %Y at %-I:%M %p")
