"""Sentence-splitting TTS — first chunk fast, abbreviation-aware."""
import re
import subprocess

from core.config import get

_ABBREVS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "vs", "etc",
    "e.g", "i.e", "a.m", "p.m", "st", "ave", "blvd",
}

_SPLIT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')


def _is_abbreviation(text: str, pos: int) -> bool:
    word_start = text.rfind(" ", 0, pos)
    word = text[word_start + 1:pos].rstrip(".").lower()
    return word in _ABBREVS


class SentenceSplitter:
    """Buffer streamed tokens; yield complete sentences."""

    def __init__(self):
        self._buf = ""

    def feed(self, chunk: str) -> list[str]:
        self._buf += chunk
        sentences = []
        while True:
            m = re.search(r'[.!?]+\s', self._buf)
            if not m:
                break
            end = m.end()
            candidate = self._buf[:end].strip()
            # skip abbreviations — check word before the dot
            dot_pos = m.start()
            if self._buf[m.start()] == "." and _is_abbreviation(self._buf, dot_pos):
                # move past this match and keep buffering
                self._buf = self._buf[end:]
                continue
            sentences.append(candidate)
            self._buf = self._buf[end:]
        return sentences

    def flush(self) -> list[str]:
        remainder = self._buf.strip()
        self._buf = ""
        return [remainder] if remainder else []


class Speaker:
    def __init__(self):
        self._splitter = SentenceSplitter()
        self._voice = get("tts.voice", "Samantha")
        self._rate = str(get("tts.rate", 220))

    def _say(self, text: str):
        if text:
            subprocess.run(
                ["say", "-v", self._voice, "-r", self._rate, text],
                check=False,
            )

    def feed(self, chunk: str):
        for sentence in self._splitter.feed(chunk):
            self._say(sentence)

    def flush(self):
        for sentence in self._splitter.flush():
            self._say(sentence)
