import tempfile
import unittest
from pathlib import Path

import sys

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import mm_video


class MmVideoTests(unittest.TestCase):
    def test_resolve_ffmpeg_tools_uses_absolute_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            ffmpeg = bin_dir / "ffmpeg.exe"
            ffprobe = bin_dir / "ffprobe.exe"
            ffmpeg.write_text("", encoding="utf-8")
            ffprobe.write_text("", encoding="utf-8")

            tools = mm_video.resolve_ffmpeg_tools(root)

        self.assertEqual(tools.ffmpeg, ffmpeg)
        self.assertEqual(tools.ffprobe, ffprobe)

    def test_ass_subtitle_writer_formats_and_escapes_cues(self):
        cues = [
            mm_video.SubtitleCue(start=0.0, end=2.5, text="第一句{重点}"),
            mm_video.SubtitleCue(start=2.5, end=5.0, text="第二句\n换行"),
        ]

        ass_text = mm_video.build_ass_subtitles(cues, title="Demo")

        self.assertIn("Title: Demo", ass_text)
        self.assertIn("Dialogue: 0,0:00:00.00,0:00:02.50", ass_text)
        self.assertIn("第一句\\{重点\\}", ass_text)
        self.assertIn("第二句\\N换行", ass_text)

    def test_build_timeline_segments_cover_video_duration(self):
        segments = mm_video.build_timeline_segments(duration=24.2, interval=10)

        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0]["start"], 0.0)
        self.assertEqual(segments[-1]["end"], 24.2)
        self.assertEqual(segments[-1]["frame"], "frames/frame_0003.jpg")

    def test_generate_placeholder_cues_uses_readable_ranges(self):
        segments = mm_video.build_timeline_segments(duration=12.0, interval=5)

        cues = mm_video.generate_placeholder_cues(segments)

        self.assertEqual(len(cues), 3)
        self.assertEqual(cues[0].start, 0.0)
        self.assertEqual(cues[-1].end, 12.0)
        self.assertIn("第 3 段", cues[-1].text)

    def test_subtitle_filter_does_not_force_windows_fontsdir(self):
        subtitle = Path("C:/tmp/subtitles.ass")

        filter_arg, cwd = mm_video.subtitle_filter_arg(subtitle, None)

        self.assertEqual(cwd, Path("C:/tmp"))
        self.assertEqual(filter_arg, "subtitles=filename='subtitles.ass'")


if __name__ == "__main__":
    unittest.main()
