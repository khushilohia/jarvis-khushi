"""Jarvis — mic → whisper → claude → say → HUD."""
import asyncio
import sys
import threading

import numpy as np
import sounddevice as sd
import uvicorn
from faster_whisper import WhisperModel

import tools.datetime_tool  # noqa: registers tools
import tools.telegram        # noqa
import tools.apps            # noqa
import tools.web             # noqa
import tools.memory          # noqa

from core.config import get
from core.llm import ClaudeCodeBrain
from core.tts import Speaker
from hud import server as hud

# ── audio config ──────────────────────────────────────────────────────────────
SAMPLE_RATE = 16_000
SPEECH_THRESHOLD = 0.02    # RMS to start recording (tune if needed)
SILENCE_THRESHOLD = 0.015  # RMS below this = silence (after speech started)
SILENCE_SECONDS = 1.2
MIN_SPEECH_SECONDS = 0.3


def p(*args, **kwargs):
    print(*args, **kwargs, flush=True)


def record_until_silence() -> np.ndarray:
    hud.push_state("LISTENING")

    chunk_size = int(SAMPLE_RATE * 0.05)  # 50ms
    silence_chunks = int(SILENCE_SECONDS / 0.05)
    min_chunks = int(MIN_SPEECH_SECONDS / 0.05)

    buf = []
    silent = 0
    started = False
    debug_ticks = 0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        while True:
            chunk, _ = stream.read(chunk_size)
            rms = float(np.sqrt(np.mean(chunk ** 2)))

            if not started:
                debug_ticks += 1
                if debug_ticks % 20 == 0:  # print every ~1s so user can calibrate
                    p(f"  [mic] rms={rms:.4f}  threshold={SPEECH_THRESHOLD}")
                if rms > SPEECH_THRESHOLD:
                    started = True
                    hud.push_state("RECORDING")
                    p("  [mic] speech detected, recording…")
                    buf.append(chunk)
            else:
                buf.append(chunk)
                if rms < SILENCE_THRESHOLD:
                    silent += 1
                    if silent >= silence_chunks:
                        break
                else:
                    silent = 0

    audio = np.concatenate(buf, axis=0).flatten()
    if len(audio) < min_chunks * chunk_size:
        p("  [mic] clip too short, ignoring")
        return np.array([], dtype="float32")
    return audio


async def jarvis_loop(brain: ClaudeCodeBrain, tts: Speaker, whisper: WhisperModel):
    loop = asyncio.get_event_loop()

    while True:
        audio = await loop.run_in_executor(None, record_until_silence)
        if audio.size == 0:
            continue

        hud.push_state("THINKING")
        segments, _ = await loop.run_in_executor(
            None, lambda: whisper.transcribe(audio, beam_size=1)
        )
        text = " ".join(s.text for s in segments).strip()
        if not text:
            p("  [whisper] empty transcript, looping")
            continue

        p(f"You: {text}")
        hud.push("user", text)
        hud.push_state("SPEAKING")

        async for chunk in brain.ask(text):
            tts.feed(chunk)
            hud.push("jarvis", chunk)

        tts.flush()


def main():
    model_size = get("whisper.model", "small")
    port = get("hud.port", 7777)

    p(f"Loading Whisper {model_size}…")
    whisper = WhisperModel(model_size, device="cpu", compute_type="int8")
    p("Whisper ready.")

    brain = ClaudeCodeBrain()
    tts = Speaker()

    config = uvicorn.Config(hud.app, host="0.0.0.0", port=port, log_level="error")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    p(f"HUD → http://localhost:{port}")
    p(f"Speech threshold: rms > {SPEECH_THRESHOLD}  (watch [mic] lines to calibrate)")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(jarvis_loop(brain, tts, whisper))
    except KeyboardInterrupt:
        p("\nGoodbye.")


if __name__ == "__main__":
    main()
