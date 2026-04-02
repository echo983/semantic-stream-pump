from __future__ import annotations

import asyncio
from collections.abc import Callable
import time

from mistralai.client import Mistral

from .config import SessionConfig


TranslationCallback = Callable[[str], None]
StatusCallback = Callable[[str], None]
ErrorCallback = Callable[[str], None]


class StreamingTranslator:
    SENTENCE_ENDINGS = (".", "!", "?", "。", "！", "？", "…", "\n")

    def __init__(
        self,
        config: SessionConfig,
        *,
        on_translation: TranslationCallback,
        on_status: StatusCallback,
        on_error: ErrorCallback,
    ) -> None:
        self.config = config
        self.on_translation = on_translation
        self.on_status = on_status
        self.on_error = on_error
        self.client = Mistral(api_key=config.api_key)
        self.pending_text = ""
        self.last_flush_ts = 0.0
        self.min_chars = 72
        self.force_flush_chars = 180
        self.max_wait_seconds = 6.0
        self.closed = False

    async def add_delta(self, text: str) -> None:
        if self.closed or not text:
            return
        self.pending_text += text
        if self._should_flush():
            await self.flush()

    async def flush(self, *, force: bool = False) -> None:
        if self.closed and not force:
            return

        batch, remainder = self._extract_flushable_text(force=force)
        batch = batch.strip()
        if not batch:
            return

        self.pending_text = remainder
        self.last_flush_ts = time.monotonic()
        try:
            translated = await self._translate_text(batch)
            if translated:
                self.on_translation(translated)
        except Exception as exc:
            self.on_error(f"Translation error: {exc}")

    async def close(self) -> None:
        await self.flush(force=True)
        self.closed = True

    def _should_flush(self) -> bool:
        text = self.pending_text
        stripped = text.strip()
        if len(stripped) >= self.min_chars and self._has_sentence_boundary(stripped):
            return True
        if len(stripped) >= self.force_flush_chars:
            return True
        if self.last_flush_ts and (time.monotonic() - self.last_flush_ts) >= self.max_wait_seconds:
            return True
        return False

    def _ends_sentence(self, text: str) -> bool:
        return text.rstrip().endswith(self.SENTENCE_ENDINGS)

    def _has_sentence_boundary(self, text: str) -> bool:
        return any(marker in text for marker in self.SENTENCE_ENDINGS)

    def _extract_flushable_text(self, *, force: bool) -> tuple[str, str]:
        text = self.pending_text
        stripped = text.strip()
        if not stripped:
            return "", text

        if force:
            return text, ""

        boundary = self._last_sentence_boundary(text)
        if boundary is not None and len(text[:boundary].strip()) >= self.min_chars:
            return text[:boundary], text[boundary:]

        if len(stripped) >= self.force_flush_chars:
            split_at = self._best_soft_split(text)
            return text[:split_at], text[split_at:]

        return "", text

    def _last_sentence_boundary(self, text: str) -> int | None:
        last_index = -1
        for marker in self.SENTENCE_ENDINGS:
            marker_index = text.rfind(marker)
            if marker_index > last_index:
                last_index = marker_index
        if last_index < 0:
            return None
        return last_index + 1

    def _best_soft_split(self, text: str) -> int:
        for marker in ("\n", ";", ":", ","):
            marker_index = text.rfind(marker)
            if marker_index >= self.min_chars:
                return marker_index + 1
        return len(text)

    async def _translate_text(self, text: str) -> str:
        self.on_status(
            f"Translating batch with {self.config.translation_model} to {self.config.target_language}..."
        )
        output_parts: list[str] = []
        stream = await self.client.chat.stream_async(
            model=self.config.translation_model,
            temperature=0,
            max_tokens=256,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a live subtitle translation engine. Translate the user's text into "
                        f"{self.config.target_language}. Output translation only. "
                        "Treat the input as streaming ASR text that may contain incomplete sentence fragments. "
                        "Merge obvious fragments into natural, complete sentences when the meaning is clear. "
                        "Preserve meaning conservatively and do not invent missing facts. "
                        "Use natural punctuation in the target language. "
                        "Never insert a line break in the middle of a sentence. "
                        "Insert one blank line only between completed subtitle sentences or short subtitle blocks. "
                        "Do not explain. Do not echo the source. Do not add labels."
                    ),
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
        )
        async for event in stream:
            chunk = event.data
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                output_parts.append(content)
        return "".join(output_parts).strip()
