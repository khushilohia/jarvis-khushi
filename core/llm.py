import asyncio
import json
import os
import re
from asyncio.subprocess import PIPE
from typing import AsyncIterator

from core.tools import REGISTRY, dispatch

_SYSTEM = """You are Jarvis, a concise voice assistant for Khushi.
Keep responses brief and natural for speech. No markdown, no bullet points.
Speak like a person — one or two sentences unless asked for more.

TOOLS AVAILABLE (output ONLY valid JSON on a single line if you want to call one):
{tool_list}

If calling a tool, your ENTIRE response must be a single JSON line like:
{{"tool":"tool_name","args":{{"param":"value"}}}}
Then wait — the result will be provided and you can respond verbally."""


def _tool_list() -> str:
    lines = []
    for name, entry in REGISTRY.items():
        props = entry["schema"].get("properties", {})
        params = ", ".join(
            f'{k}: {v.get("type","any")}' for k, v in props.items()
        )
        lines.append(f'- {name}({params}) → {entry["description"][:80]}')
    return "\n".join(lines) if lines else "none"


def _build_prompt(history: list[dict], user_text: str) -> str:
    system = _SYSTEM.format(tool_list=_tool_list())
    parts = [system, ""]
    for turn in history[-8:]:  # last 8 turns so context doesn't balloon
        parts.append(f"User: {turn['user']}")
        parts.append(f"Jarvis: {turn['assistant']}")
    parts.append(f"User: {user_text}")
    parts.append("Jarvis:")
    return "\n".join(parts)


def _parse_tool_call(text: str) -> dict | None:
    text = text.strip()
    if not text.startswith("{"):
        return None
    try:
        data = json.loads(text)
        if "tool" in data:
            return data
    except json.JSONDecodeError:
        pass
    return None


async def _claude(prompt: str) -> str:
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("ANTHROPIC_", "OPENAI_", "OPENROUTER_"))}
    proc = await asyncio.create_subprocess_exec(
        "claude", "-p", prompt,
        "--output-format", "stream-json", "--verbose",
        stdout=PIPE, stderr=PIPE, env=env,
    )
    result = ""
    async for line in proc.stdout:
        line = line.decode().strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "text":
                    result += block["text"]
        elif event.get("type") == "result" and not result:
            result = event.get("result", "")
    stderr = await proc.stderr.read()
    await proc.wait()
    if proc.returncode != 0:
        print(f"  [llm] error: {stderr.decode().strip()}", flush=True)
    return result.strip()


class ClaudeCodeBrain:
    def __init__(self):
        self.history: list[dict] = []

    async def ask(self, text: str) -> AsyncIterator[str]:
        prompt = _build_prompt(self.history, text)
        response = await _claude(prompt)

        tool_call = _parse_tool_call(response)
        if tool_call:
            name = tool_call.get("tool", "")
            args = tool_call.get("args", {})
            print(f"  [tool] {name}({args})", flush=True)
            tool_result = await asyncio.get_event_loop().run_in_executor(
                None, dispatch, name, args
            )
            print(f"  [tool] → {tool_result}", flush=True)

            # second call: give Claude the tool result so it can respond verbally
            follow_prompt = (
                prompt + f' {{"tool":"{name}","args":{json.dumps(args)}}}\n'
                f"[Tool result: {tool_result}]\nJarvis (respond verbally now):"
            )
            response = await _claude(follow_prompt)

        self.history.append({"user": text, "assistant": response})

        # yield in ~sentence chunks so TTS starts fast
        for chunk in re.split(r'(?<=[.!?])\s+', response):
            if chunk:
                yield chunk + " "
