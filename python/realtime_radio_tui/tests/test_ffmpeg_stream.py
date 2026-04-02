import unittest

from realtime_radio_tui.ffmpeg_stream import build_ffmpeg_command


class BuildFfmpegCommandTest(unittest.TestCase):
    def test_build_ffmpeg_command_for_pcm_stdout(self) -> None:
        command = build_ffmpeg_command(
            "ffmpeg",
            "https://example.com/live.m3u8",
            16000,
            user_agent="Mozilla/5.0",
        )

        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-user_agent",
                "Mozilla/5.0",
                "-i",
                "https://example.com/live.m3u8",
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "pcm_s16le",
                "-f",
                "s16le",
                "-",
            ],
        )


if __name__ == "__main__":
    unittest.main()
