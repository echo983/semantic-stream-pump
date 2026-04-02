from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
import contextlib
from pathlib import Path
import shutil

from .config import SessionConfig


def resolve_ffmpeg_binary() -> str:
    bundled_ffmpeg = (
        Path(__file__).resolve().parents[4] / ".tools" / "ffmpeg-btbn" / "bin" / "ffmpeg"
    )
    if bundled_ffmpeg.exists():
        return str(bundled_ffmpeg)

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        from imageio_ffmpeg import get_ffmpeg_exe
    except ImportError as exc:
        raise RuntimeError(
            "ffmpeg is not available. Install system ffmpeg or imageio-ffmpeg."
        ) from exc

    return get_ffmpeg_exe()


def build_ffmpeg_command(
    ffmpeg_bin: str,
    stream_url: str,
    sample_rate: int,
    *,
    user_agent: str | None = None,
) -> list[str]:
    command = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
    ]
    if user_agent:
        command.extend(["-user_agent", user_agent])
    command.extend(
        [
            "-i",
            stream_url,
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-c:a",
            "pcm_s16le",
            "-f",
            "s16le",
            "-",
        ]
    )
    return command


class FfmpegPCMStream:
    def __init__(self, config: SessionConfig) -> None:
        self.config = config
        self.ffmpeg_bin = resolve_ffmpeg_binary()
        self.process: asyncio.subprocess.Process | None = None

    async def __aenter__(self) -> "FfmpegPCMStream":
        command = build_ffmpeg_command(
            self.ffmpeg_bin,
            self.config.stream_url,
            self.config.sample_rate,
            user_agent=self.config.user_agent,
        )
        self.process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()

    async def iter_pcm_chunks(
        self, stop_event: asyncio.Event
    ) -> AsyncIterator[bytes]:
        if self.process is None or self.process.stdout is None:
            raise RuntimeError("ffmpeg process is not running.")

        while not stop_event.is_set():
            chunk = await self.process.stdout.read(self.config.chunk_bytes)
            if not chunk:
                break
            yield chunk

    async def read_stderr_tail(self) -> str:
        if self.process is None or self.process.stderr is None:
            return ""
        with contextlib.suppress(Exception):
            data = await asyncio.wait_for(self.process.stderr.read(), timeout=0.2)
            return data.decode("utf-8", errors="replace").strip()
        return ""

    async def stop(self) -> None:
        if self.process is None:
            return

        if self.process.returncode is None:
            self.process.terminate()
            with contextlib.suppress(ProcessLookupError):
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(self.process.wait(), timeout=2)

        if self.process.returncode is None:
            self.process.kill()
            with contextlib.suppress(ProcessLookupError):
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(self.process.wait(), timeout=2)
