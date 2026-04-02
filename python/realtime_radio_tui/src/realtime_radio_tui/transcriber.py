from __future__ import annotations

import asyncio
from collections.abc import Callable

from mistralai.client import Mistral
from mistralai.client.models import (
    AudioFormat,
    RealtimeTranscriptionError,
    RealtimeTranscriptionSessionCreated,
    TranscriptionStreamDone,
    TranscriptionStreamTextDelta,
)
from mistralai.extra.realtime import UnknownRealtimeEvent

from .config import SessionConfig
from .ffmpeg_stream import FfmpegPCMStream


StatusCallback = Callable[[str], None]
TextCallback = Callable[[str], None]
ErrorCallback = Callable[[str], None]


class RadioRealtimeTranscriber:
    def __init__(
        self,
        config: SessionConfig,
        *,
        on_status: StatusCallback,
        on_text: TextCallback,
        on_error: ErrorCallback,
    ) -> None:
        self.config = config
        self.on_status = on_status
        self.on_text = on_text
        self.on_error = on_error
        self.stop_event = asyncio.Event()

    def stop(self) -> None:
        self.stop_event.set()

    async def run(self) -> None:
        client = Mistral(api_key=self.config.api_key)
        audio_format = AudioFormat(
            encoding="pcm_s16le",
            sample_rate=self.config.sample_rate,
        )

        try:
            async with FfmpegPCMStream(self.config) as ffmpeg_stream:
                self.on_status("Connecting to Mistral realtime transcription...")
                audio_stream = ffmpeg_stream.iter_pcm_chunks(self.stop_event)
                async for event in client.audio.realtime.transcribe_stream(
                    audio_stream=audio_stream,
                    model=self.config.model,
                    audio_format=audio_format,
                    target_streaming_delay_ms=self.config.target_delay_ms,
                ):
                    if self.stop_event.is_set():
                        break

                    if isinstance(event, RealtimeTranscriptionSessionCreated):
                        self.on_status("Session created. Streaming audio...")
                    elif isinstance(event, TranscriptionStreamTextDelta):
                        self.on_text(event.text)
                    elif isinstance(event, TranscriptionStreamDone):
                        self.on_status("Stream finished.")
                    elif isinstance(event, RealtimeTranscriptionError):
                        self.on_error(f"Mistral realtime error: {event}")
                        break
                    elif isinstance(event, UnknownRealtimeEvent):
                        self.on_status(f"Unknown realtime event: {event.type}")

                stderr_tail = await ffmpeg_stream.read_stderr_tail()
                if stderr_tail and not self.stop_event.is_set():
                    self.on_status(f"ffmpeg closed: {stderr_tail}")
        except Exception as exc:
            self.on_error(str(exc))

