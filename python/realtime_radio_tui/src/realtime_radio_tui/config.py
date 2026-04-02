from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


DEFAULT_MODEL = "voxtral-mini-transcribe-realtime-2602"
DEFAULT_STREAM_URL = "https://rtvelivestream.akamaized.net/rtvesec/la2/la2_main_dvr.m3u8"
DEFAULT_TRANSLATION_MODEL = "ministral-3b-2512"
DEFAULT_TARGET_LANGUAGE = "Chinese"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@dataclass(slots=True)
class SessionConfig:
    stream_url: str
    api_key: str
    model: str = DEFAULT_MODEL
    translation_model: str = DEFAULT_TRANSLATION_MODEL
    target_language: str = DEFAULT_TARGET_LANGUAGE
    sample_rate: int = 16000
    target_delay_ms: int = 800
    chunk_duration_ms: int = 480
    user_agent: str = DEFAULT_USER_AGENT

    @property
    def chunk_bytes(self) -> int:
        return int(self.sample_rate * (self.chunk_duration_ms / 1000) * 2)


def load_api_key() -> str:
    api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    if api_key:
        return api_key

    env_path = _find_repo_env_file()
    if env_path is not None:
        api_key = _read_key_from_env_file(env_path, "MISTRAL_API_KEY")
        if api_key:
            return api_key

    raise RuntimeError(
        "Missing MISTRAL_API_KEY. Set it in the environment or in the repository .env file."
    )


def _find_repo_env_file() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / ".env"
        if candidate.exists():
            return candidate
    return None


def _read_key_from_env_file(path: Path, key: str) -> str:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() != key:
            continue
        cleaned = value.strip().strip('"').strip("'")
        return cleaned
    return api_key
