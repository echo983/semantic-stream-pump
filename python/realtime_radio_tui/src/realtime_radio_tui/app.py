from __future__ import annotations

import sys

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Input, Static, TextArea
from textual.worker import Worker, WorkerCancelled

from .config import DEFAULT_STREAM_URL, SessionConfig, load_api_key
from .transcriber import RadioRealtimeTranscriber


class StatusEvent(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class TranscriptEvent(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class ErrorEvent(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class RadioTranscribeApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }
    #body {
        height: 1fr;
    }
    #controls {
        height: auto;
        padding: 1 2;
        border: round $surface;
    }
    #button-row {
        height: auto;
    }
    #transcript {
        height: 1fr;
        min-height: 6;
        border: round $accent;
        padding: 1;
        width: 100%;
    }
    .label {
        color: $text-muted;
        margin: 0 0 1 0;
    }
    Input {
        margin-bottom: 1;
    }
    Button {
        margin-right: 1;
    }
    #status {
        height: auto;
        padding: 1 2 0 2;
        color: $warning;
    }
    """

    transcript = reactive("")
    worker: Worker | None = None
    transcriber: RadioRealtimeTranscriber | None = None

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, initial_url: str | None = None) -> None:
        super().__init__()
        self.initial_url = initial_url or DEFAULT_STREAM_URL

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="body"):
            with Container(id="controls"):
                yield Static("M3U8 stream URL", classes="label")
                yield Input(value=self.initial_url, id="stream-url")
                yield Static("Target delay (ms)", classes="label")
                yield Input(value="800", id="delay-ms")
                with Horizontal(id="button-row"):
                    yield Button("Start", id="start", variant="success")
                    yield Button("Stop", id="stop", variant="error")
                    yield Button("Clear", id="clear")
            yield Static("Idle", id="status")
            yield TextArea(
                "",
                id="transcript",
                read_only=True,
                show_line_numbers=False,
                soft_wrap=True,
                placeholder="Transcript will appear here.",
            )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#stream-url", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.start_transcription()
        elif event.button.id == "stop":
            self.stop_transcription("Stopped by user.")
        elif event.button.id == "clear":
            self.transcript = ""
            self._render_transcript()

    def on_status_event(self, event: StatusEvent) -> None:
        self.query_one("#status", Static).update(event.text)

    def on_transcript_event(self, event: TranscriptEvent) -> None:
        self.transcript += event.text
        self._render_transcript()

    def on_error_event(self, event: ErrorEvent) -> None:
        self.query_one("#status", Static).update(f"Error: {event.text}")

    async def run_transcriber(self, config: SessionConfig) -> None:
        self.transcriber = RadioRealtimeTranscriber(
            config,
            on_status=lambda text: self.post_message(StatusEvent(text)),
            on_text=lambda text: self.post_message(TranscriptEvent(text)),
            on_error=lambda text: self.post_message(ErrorEvent(text)),
        )
        await self.transcriber.run()

    def start_transcription(self) -> None:
        if self.worker and self.worker.is_running:
            self.post_message(StatusEvent("A transcription session is already running."))
            return

        stream_url = self.query_one("#stream-url", Input).value.strip()
        delay_raw = self.query_one("#delay-ms", Input).value.strip()
        try:
            delay_ms = int(delay_raw)
        except ValueError:
            self.post_message(ErrorEvent("Delay must be an integer in milliseconds."))
            return

        try:
            config = SessionConfig(
                stream_url=stream_url,
                api_key=load_api_key(),
                target_delay_ms=delay_ms,
            )
        except Exception as exc:
            self.post_message(ErrorEvent(str(exc)))
            return

        self.post_message(StatusEvent("Starting ffmpeg + Mistral realtime pipeline..."))
        self.worker = self.run_worker(
            self.run_transcriber(config),
            name="radio-realtime-transcriber",
            exclusive=True,
        )

    def stop_transcription(self, status: str) -> None:
        if self.transcriber is not None:
            self.transcriber.stop()
        if self.worker is not None:
            self.worker.cancel()
        self.post_message(StatusEvent(status))

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.name != "radio-realtime-transcriber":
            return
        if event.state.name == "SUCCESS":
            self.query_one("#status", Static).update("Session ended.")
        elif event.state.name == "ERROR":
            error = event.worker.error
            if isinstance(error, WorkerCancelled):
                self.query_one("#status", Static).update("Session cancelled.")
            elif error is not None:
                self.query_one("#status", Static).update(f"Worker error: {error}")

    def _render_transcript(self) -> None:
        content = self.transcript.strip() or "Transcript will appear here."
        transcript = self.query_one("#transcript", TextArea)
        transcript.load_text(content)
        last_line = max(content.count("\n"), 0)
        last_column = len(content.splitlines()[-1]) if content.splitlines() else len(content)
        transcript.move_cursor((last_line, last_column))
        transcript.scroll_cursor_visible(animate=False)


def run() -> None:
    initial_url = sys.argv[1] if len(sys.argv) > 1 else None
    app = RadioTranscribeApp(initial_url=initial_url)
    app.run()


if __name__ == "__main__":
    run()
