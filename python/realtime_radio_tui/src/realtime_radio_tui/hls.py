from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx


@dataclass(slots=True)
class PlaylistSnapshot:
    url: str
    segments: list[str]
    target_duration: float = 5.0
    is_master: bool = False
    audio_renditions: list[str] | None = None


def _parse_attribute_list(line: str) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for chunk in line.split(","):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        attributes[key.strip()] = value.strip().strip('"')
    return attributes


def parse_playlist(base_url: str, content: str) -> PlaylistSnapshot:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    segments: list[str] = []
    audio_renditions: list[str] = []
    target_duration = 5.0
    is_master = False

    for index, line in enumerate(lines):
        if line.startswith("#EXT-X-TARGETDURATION:"):
            try:
                target_duration = float(line.split(":", 1)[1].strip())
            except ValueError:
                target_duration = 5.0
        elif line.startswith("#EXT-X-MEDIA:") and "TYPE=AUDIO" in line:
            is_master = True
            attrs = _parse_attribute_list(line.split(":", 1)[1])
            uri = attrs.get("URI")
            if uri:
                audio_renditions.append(urljoin(base_url, uri))
        elif line.startswith("#EXT-X-STREAM-INF:"):
            is_master = True
        elif not line.startswith("#"):
            absolute = urljoin(base_url, line)
            if is_master:
                continue
            segments.append(absolute)

    return PlaylistSnapshot(
        url=base_url,
        segments=segments,
        target_duration=target_duration,
        is_master=is_master,
        audio_renditions=audio_renditions or None,
    )


class HlsSegmentStream:
    def __init__(self, stream_url: str, user_agent: str, *, timeout: float = 15.0) -> None:
        self.stream_url = stream_url
        self.user_agent = user_agent
        self.timeout = timeout
        self.headers = {
            "User-Agent": user_agent,
            "Referer": "https://www.rtve.es/",
            "Origin": "https://www.rtve.es",
        }
        self._seen_segments: set[str] = set()

    async def iter_segments(self, stop_event: asyncio.Event) -> AsyncIterator[bytes]:
        async with httpx.AsyncClient(
            headers=self.headers,
            follow_redirects=True,
            timeout=self.timeout,
        ) as client:
            media_playlist_url = await self._resolve_media_playlist(client, self.stream_url)
            while not stop_event.is_set():
                snapshot = await self._fetch_playlist(client, media_playlist_url)
                new_segments = [
                    segment
                    for segment in snapshot.segments
                    if segment not in self._seen_segments
                ]

                for segment_url in new_segments:
                    if stop_event.is_set():
                        break
                    self._seen_segments.add(segment_url)
                    yield await self._fetch_segment(client, segment_url)

                await asyncio.sleep(max(1.0, snapshot.target_duration / 2))

    async def _resolve_media_playlist(
        self, client: httpx.AsyncClient, playlist_url: str
    ) -> str:
        snapshot = await self._fetch_playlist(client, playlist_url)
        if snapshot.is_master:
            if snapshot.audio_renditions:
                return snapshot.audio_renditions[0]
            raise RuntimeError("Master playlist has no audio rendition URI.")
        return playlist_url

    async def _fetch_playlist(
        self, client: httpx.AsyncClient, playlist_url: str
    ) -> PlaylistSnapshot:
        response = await client.get(playlist_url)
        response.raise_for_status()
        return parse_playlist(str(response.url), response.text)

    async def _fetch_segment(self, client: httpx.AsyncClient, segment_url: str) -> bytes:
        response = await client.get(segment_url)
        response.raise_for_status()
        return response.content
