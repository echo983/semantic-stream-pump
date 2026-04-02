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


if __name__ == "__main__":
    unittest.main()
