import unittest

from realtime_radio_tui.config import SessionConfig
from realtime_radio_tui.translator import StreamingTranslator


class StreamingTranslatorTest(unittest.TestCase):
    def test_sentence_detection(self) -> None:
        translator = StreamingTranslator(
            SessionConfig(stream_url="https://example.com", api_key="dummy"),
            on_translation=lambda _: None,
            on_status=lambda _: None,
            on_error=lambda _: None,
        )
        self.assertTrue(translator._ends_sentence("Hello."))
        self.assertTrue(translator._ends_sentence("こんにちは。"))
        self.assertFalse(translator._ends_sentence("unfinished"))

    def test_context_history_keeps_recent_blocks_only(self) -> None:
        translator = StreamingTranslator(
            SessionConfig(stream_url="https://example.com", api_key="dummy"),
            on_translation=lambda _: None,
            on_status=lambda _: None,
            on_error=lambda _: None,
        )

        for index in range(5):
            translator._remember_context(f"source-{index}", f"translation-{index}")

        self.assertEqual(
            translator.source_history,
            ["source-2", "source-3", "source-4"],
        )
        self.assertEqual(
            translator.translation_history,
            ["translation-2", "translation-3", "translation-4"],
        )


if __name__ == "__main__":
    unittest.main()
