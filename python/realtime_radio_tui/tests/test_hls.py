import unittest

from realtime_radio_tui.hls import parse_playlist


class ParsePlaylistTest(unittest.TestCase):
    def test_parse_master_playlist_picks_audio_renditions(self) -> None:
        playlist = """#EXTM3U
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audios",NAME="Castellano",URI="audio.m3u8"
#EXT-X-STREAM-INF:BANDWIDTH=1,AUDIO="audios"
video.m3u8
"""
        snapshot = parse_playlist("https://example.com/master.m3u8", playlist)

        self.assertTrue(snapshot.is_master)
        self.assertEqual(snapshot.audio_renditions, ["https://example.com/audio.m3u8"])

    def test_parse_media_playlist_segments(self) -> None:
        playlist = """#EXTM3U
#EXT-X-TARGETDURATION:5
#EXTINF:5.0,
seg-1.ts
#EXTINF:5.0,
https://cdn.example.com/seg-2.ts
"""
        snapshot = parse_playlist("https://example.com/audio.m3u8", playlist)

        self.assertFalse(snapshot.is_master)
        self.assertEqual(
            snapshot.segments,
            [
                "https://example.com/seg-1.ts",
                "https://cdn.example.com/seg-2.ts",
            ],
        )


if __name__ == "__main__":
    unittest.main()
