import asyncio
import json
import queue
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

app = FastAPI()
_q: queue.Queue = queue.Queue()  # stdlib queue — thread-safe, no loop coupling

_HUD_HTML = Path(__file__).parent / "index.html"


@app.get("/")
async def root():
    return HTMLResponse(_HUD_HTML.read_text())


@app.get("/events")
async def events():
    async def generator():
        loop = asyncio.get_event_loop()
        while True:
            data = await loop.run_in_executor(None, _q.get)
            yield f"data: {json.dumps(data)}\n\n"
    return StreamingResponse(generator(), media_type="text/event-stream")


def push(role: str, text: str):
    _q.put({"role": role, "text": text})


def push_state(state: str):
    _q.put({"state": state})
