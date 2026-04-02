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
        self.min_chars = 48
        self.max_wait_seconds = 4.0
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

        batch = self.pending_text.strip()
        if not batch:
            return

        if not force and len(batch) < self.min_chars and not self._ends_sentence(batch):
            return

        self.pending_text = ""
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
        if len(text.strip()) >= self.min_chars and self._ends_sentence(text):
            return True
        if len(text.strip()) >= self.min_chars * 2:
            return True
        if self.last_flush_ts and (time.monotonic() - self.last_flush_ts) >= self.max_wait_seconds:
            return True
        return False

    def _ends_sentence(self, text: str) -> bool:
        return text.rstrip().endswith((".", "!", "?", "。", "！", "？", "…", "\n"))

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
                        "You are a live translation engine. Translate the user's text into "
                        f"{self.config.target_language}. Output translation only. "
                        "Keep natural sentence order. Do not explain. Do not echo the source."
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
