# Jarvis — Handoff

## What works right now

```
cd ~/Projects/jarvis && uv run python main.py
```

- Mic → Whisper `small` (CPU) → transcription
- Transcription → `claude -p` subprocess → response
- Response split into sentences → `say -v Samantha -r 220`
- HUD at http://localhost:7777 — live conversation feed + arc reactor SVG
- Conversation history: last 8 turns kept in memory per session
- Tools registered and callable by voice:
  - `get_datetime` — current date/time
  - `send_telegram` — alert via `~/.claude/scripts/tg.sh`
  - `open_app` — opens any app/URL via `open`
  - `web_search` — DuckDuckGo, 3 results
  - `remember` / `recall` / `forget` — JSON store at `~/.jarvis_memory.json`

## Known ceilings

| Issue | Cause | Fix |
|-------|-------|-----|
| ~3–5s response latency | `claude -p` subprocess cold-starts every turn | Anthropic SDK + API key |
| Tool calling unreliable | Prompt-engineered (JSON pattern matching), not native | Same: SDK with `tools=` |
| No cross-session history | History resets on restart | Persist `brain.history` to disk |
| Whisper sometimes misses quiet speech | RMS threshold 0.02, tune in `main.py` | Lower `SPEECH_THRESHOLD` |
| No wake word | Enter key / silence detection only | Add wake word (e.g. `pvporcupine`) |

## Next milestone (M2 — proper tool loop)

Blocked on Anthropic API key (company plan, can't use). Once available:

1. Swap `core/llm.py` to use `AsyncAnthropic` + `messages.stream()`
2. Pass `tools=tool_schemas()` to every call
3. Handle `tool_use` blocks natively — no prompt engineering
4. True token streaming → TTS first word latency drops to ~0.5s

The rest of the codebase (`core/tools.py`, `tools/*.py`, `hud/`) stays unchanged.

## M3 — Gesture tracker (future)

Port `~/jarvis/gestes/tracker.py` — translate French variable names, wire to
`POST /api/gesture` on the FastAPI server, map gestures to actions (pause TTS,
mute mic). Plan in `~/.claude/plans/imperative-crunching-russell.md`.

## File map

```
main.py          — entry point: audio loop + uvicorn HUD server
config.yaml      — tune voice/whisper/port
core/
  llm.py         — ClaudeCodeBrain: claude -p subprocess, history, tool dispatch
  tts.py         — SentenceSplitter + Speaker (say command)
  tools.py       — @tool decorator + REGISTRY + dispatch()
  config.py      — yaml reader
tools/
  datetime_tool.py, telegram.py, apps.py, web.py, memory.py
hud/
  server.py      — FastAPI + stdlib queue SSE
  index.html     — Iron Man HUD (ported CSS from ~/jarvis/hud.html)
```

## Repo

https://github.com/khushilohia/jarvis-khushi
