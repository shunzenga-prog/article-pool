#!/usr/bin/env python3
"""Prepare and render existing-video narration assets.

This script is the deterministic leaf tool for the mm-video workflow. It does
not call any paid model API by itself; agents or humans can edit the generated
timeline, narration, and subtitle files before rendering.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence


DEFAULT_FFMPEG_ROOT = Path(r"D:\Environment\ffmpeg\ffmpeg-7.0.2")
DEFAULT_OUTPUT_ROOT = Path("reports") / "mm-video"


@dataclass(frozen=True)
class FfmpegTools:
    ffmpeg: Path
    ffprobe: Path


@dataclass(frozen=True)
class SubtitleCue:
    start: float
    end: float
    text: str


def _as_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    return Path(value).expanduser()


def _tool_from_root(root: Path, tool_name: str) -> Path | None:
    candidates = [
        root / "bin" / f"{tool_name}.exe",
        root / "bin" / tool_name,
        root / f"{tool_name}.exe",
        root / tool_name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_ffmpeg_tools(
    ffmpeg_root: str | Path | None = None,
    *,
    ffmpeg: str | Path | None = None,
    ffprobe: str | Path | None = None,
) -> FfmpegTools:
    """Resolve ffmpeg and ffprobe paths.

    Resolution order:
    1. Explicit executable paths.
    2. Explicit root, MM_VIDEO_FFMPEG_ROOT, then the known local default.
    3. PATH fallback.
    """
    ffmpeg_path = _as_path(ffmpeg)
    ffprobe_path = _as_path(ffprobe)

    root_value = ffmpeg_root or os.environ.get("MM_VIDEO_FFMPEG_ROOT")
    roots = []
    if root_value:
        roots.append(Path(root_value).expanduser())
    roots.append(DEFAULT_FFMPEG_ROOT)

    if not ffmpeg_path or not ffprobe_path:
        for root in roots:
            if not ffmpeg_path:
                ffmpeg_path = _tool_from_root(root, "ffmpeg")
            if not ffprobe_path:
                ffprobe_path = _tool_from_root(root, "ffprobe")
            if ffmpeg_path and ffprobe_path:
                break

    if not ffmpeg_path:
        found = shutil.which("ffmpeg")
        ffmpeg_path = Path(found) if found else None
    if not ffprobe_path:
        found = shutil.which("ffprobe")
        ffprobe_path = Path(found) if found else None

    if not ffmpeg_path or not ffmpeg_path.exists():
        raise FileNotFoundError(
            "ffmpeg not found. Pass --ffmpeg-root, --ffmpeg, or set MM_VIDEO_FFMPEG_ROOT."
        )
    if not ffprobe_path or not ffprobe_path.exists():
        raise FileNotFoundError(
            "ffprobe not found. Pass --ffmpeg-root, --ffprobe, or set MM_VIDEO_FFMPEG_ROOT."
        )

    return FfmpegTools(ffmpeg=ffmpeg_path, ffprobe=ffprobe_path)


def run_command(args: Sequence[str | Path], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        [str(arg) for arg in args],
        cwd=str(cwd) if cwd else None,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        command = " ".join(str(arg) for arg in args)
        raise RuntimeError(
            f"Command failed with exit code {process.returncode}: {command}\n"
            f"STDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}"
        )
    return process


def probe_video(video: Path, tools: FfmpegTools) -> dict[str, Any]:
    result = run_command(
        [
            tools.ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            video,
        ]
    )
    return json.loads(result.stdout)


def video_duration(probe: dict[str, Any]) -> float:
    duration = probe.get("format", {}).get("duration")
    if duration is None:
        for stream in probe.get("streams", []):
            if stream.get("duration"):
                duration = stream["duration"]
                break
    if duration is None:
        raise ValueError("Video duration is unavailable from ffprobe output.")
    return float(duration)


def video_dimensions(probe: dict[str, Any]) -> tuple[int, int]:
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "video":
            width = int(stream.get("width") or 1080)
            height = int(stream.get("height") or 1920)
            return width, height
    return 1080, 1920


def has_audio_stream(probe: dict[str, Any]) -> bool:
    return any(stream.get("codec_type") == "audio" for stream in probe.get("streams", []))


def safe_slug(value: str | None) -> str:
    if not value:
        return "video"
    slug = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", value, flags=re.UNICODE).strip("-._")
    return slug or "video"


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def ensure_run_dir(output_root: Path, slug: str | None) -> Path:
    run_dir = output_root / f"{timestamp()}-{safe_slug(slug)}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def build_timeline_segments(duration: float, interval: int | float) -> list[dict[str, Any]]:
    if duration <= 0:
        raise ValueError("duration must be positive")
    if interval <= 0:
        raise ValueError("interval must be positive")

    count = max(1, math.ceil(duration / interval))
    segments: list[dict[str, Any]] = []
    for index in range(count):
        start = round(index * interval, 3)
        end = round(min(duration, (index + 1) * interval), 3)
        if end <= start:
            end = round(min(duration, start + 0.001), 3)
        segments.append(
            {
                "index": index + 1,
                "start": start,
                "end": end,
                "frame": f"frames/frame_{index + 1:04d}.jpg",
                "visual_notes": "",
                "ocr_notes": "",
                "source_audio_notes": "",
                "narration_goal": "",
            }
        )
    return segments


def generate_placeholder_cues(segments: list[dict[str, Any]]) -> list[SubtitleCue]:
    cues: list[SubtitleCue] = []
    for segment in segments:
        text = f"第 {segment['index']} 段解说：请根据画面补充旁白。"
        cues.append(SubtitleCue(start=float(segment["start"]), end=float(segment["end"]), text=text))
    return cues


def split_plain_text(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[。！？!?；;])\s*", text)
    return [part.strip() for part in parts if part.strip()]


def generate_cues_from_text(text: str, duration: float) -> list[SubtitleCue]:
    lines = split_plain_text(text)
    if not lines:
        return []
    cue_length = duration / len(lines)
    cues: list[SubtitleCue] = []
    for index, line in enumerate(lines):
        start = round(index * cue_length, 3)
        end = round(duration if index == len(lines) - 1 else (index + 1) * cue_length, 3)
        cues.append(SubtitleCue(start=start, end=end, text=line))
    return cues


def _format_ass_time(seconds: float) -> str:
    centiseconds = int(round(seconds * 100))
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, centis = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def _format_srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _escape_ass_text(text: str) -> str:
    return text.replace("{", r"\{").replace("}", r"\}").replace("\r\n", "\n").replace("\n", r"\N")


def build_ass_subtitles(
    cues: list[SubtitleCue],
    *,
    title: str = "mm-video subtitles",
    play_res_x: int = 1080,
    play_res_y: int = 1920,
    font_name: str = "Microsoft YaHei",
    font_size: int = 54,
    margin_v: int = 140,
) -> str:
    header = f"""[Script Info]
Title: {title}
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&HAA000000,&H66000000,0,0,0,0,100,100,0,0,3,2,0,2,72,72,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = [
        f"Dialogue: 0,{_format_ass_time(cue.start)},{_format_ass_time(cue.end)},Default,,0,0,0,,{_escape_ass_text(cue.text)}"
        for cue in cues
    ]
    return header + "\n".join(events) + "\n"


def build_srt_subtitles(cues: list[SubtitleCue]) -> str:
    blocks = []
    for index, cue in enumerate(cues, start=1):
        text = cue.text.replace("\r\n", "\n").strip()
        blocks.append(f"{index}\n{_format_srt_time(cue.start)} --> {_format_srt_time(cue.end)}\n{text}\n")
    return "\n".join(blocks)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_narration_template(path: Path, segments: list[dict[str, Any]], cues: list[SubtitleCue]) -> None:
    lines = [
        "# mm-video narration",
        "",
        "把下面的占位解说改成最终旁白后，可以重新生成字幕或直接编辑 subtitles.ass。",
        "",
        "## Suggested Cues",
        "",
    ]
    for cue in cues:
        lines.extend(
            [
                f"### {_format_srt_time(cue.start)} --> {_format_srt_time(cue.end)}",
                cue.text,
                "",
            ]
        )
    lines.extend(["## Timeline Notes", ""])
    for segment in segments:
        lines.extend(
            [
                f"- {segment['index']}. {segment['start']}s-{segment['end']}s",
                f"  - frame: {segment['frame']}",
                "  - visual_notes:",
                "  - narration_goal:",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract_audio(video: Path, output: Path, tools: FfmpegTools) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run_command([tools.ffmpeg, "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", output])


def extract_frames(video: Path, output_dir: Path, tools: FfmpegTools, *, interval: int, frame_width: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            tools.ffmpeg,
            "-y",
            "-i",
            video,
            "-vf",
            f"fps=1/{interval},scale={frame_width}:-2",
            "-q:v",
            "3",
            output_dir / "frame_%04d.jpg",
        ]
    )


def create_contact_sheet(video: Path, output: Path, tools: FfmpegTools, *, duration: float) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    interval = max(1, math.floor(duration / 12))
    run_command(
        [
            tools.ffmpeg,
            "-y",
            "-i",
            video,
            "-vf",
            f"fps=1/{interval},scale=220:-1,tile=4x3",
            "-frames:v",
            "1",
            "-update",
            "1",
            output,
        ]
    )


def _load_narration(args: argparse.Namespace) -> str:
    if args.narration_text:
        return args.narration_text
    if args.narration_file:
        return Path(args.narration_file).read_text(encoding="utf-8")
    return ""


def prepare_assets(args: argparse.Namespace) -> dict[str, Any]:
    video = Path(args.input).resolve()
    if not video.exists():
        raise FileNotFoundError(f"Input video not found: {video}")

    tools = resolve_ffmpeg_tools(args.ffmpeg_root, ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
    run_dir = ensure_run_dir(Path(args.output_root), args.slug or video.stem)
    frame_dir = run_dir / "frames"
    audio_path = run_dir / "audio" / "source.wav"
    timeline_path = run_dir / "timeline.json"
    narration_path = run_dir / "narration.md"
    ass_path = run_dir / "subtitles.ass"
    srt_path = run_dir / "subtitles.srt"
    contact_sheet_path = run_dir / "contact_sheet.jpg"

    probe = probe_video(video, tools)
    duration = video_duration(probe)
    width, height = video_dimensions(probe)
    segments = build_timeline_segments(duration, args.interval)
    narration = _load_narration(args)
    cues = generate_cues_from_text(narration, duration) if narration else generate_placeholder_cues(segments)

    audio_extracted = False
    if not args.skip_audio and has_audio_stream(probe):
        extract_audio(video, audio_path, tools)
        audio_extracted = True

    if not args.skip_frames:
        extract_frames(video, frame_dir, tools, interval=args.interval, frame_width=args.frame_width)
        create_contact_sheet(video, contact_sheet_path, tools, duration=duration)

    play_res_x, play_res_y = (1080, 1920) if height >= width else (1920, 1080)
    ass_path.write_text(
        build_ass_subtitles(cues, title=video.stem, play_res_x=play_res_x, play_res_y=play_res_y),
        encoding="utf-8",
    )
    srt_path.write_text(build_srt_subtitles(cues), encoding="utf-8")
    write_narration_template(narration_path, segments, cues)

    report = {
        "workflow": "mm-video",
        "source_video": str(video),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "ffmpeg": str(tools.ffmpeg),
        "ffprobe": str(tools.ffprobe),
        "duration": duration,
        "dimensions": {"width": width, "height": height},
        "audio_extracted": audio_extracted,
        "artifacts": {
            "run_dir": str(run_dir),
            "timeline": str(timeline_path),
            "narration": str(narration_path),
            "subtitles_ass": str(ass_path),
            "subtitles_srt": str(srt_path),
            "audio": str(audio_path) if audio_extracted else "",
            "frames": str(frame_dir),
            "contact_sheet": str(contact_sheet_path),
        },
        "segments": segments,
        "probe": probe,
    }
    write_json(timeline_path, report)
    return report


def _escape_filter_path(path: Path) -> str:
    text = path.as_posix()
    return text.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")


def _is_windows_drive_path(path: Path) -> bool:
    return bool(re.match(r"^[A-Za-z]:[/\\]", str(path)))


def _filter_path(path: Path) -> Path:
    if _is_windows_drive_path(path):
        return path
    return path.resolve()


def subtitle_filter_arg(subtitle_path: Path, fonts_dir: Path | None) -> tuple[str, Path]:
    subtitle_path = _filter_path(subtitle_path)
    cwd = subtitle_path.parent
    filename = subtitle_path.name.replace("\\", "\\\\").replace("'", r"\'")
    value = f"subtitles=filename='{filename}'"
    if fonts_dir:
        value += f":fontsdir='{_escape_filter_path(_filter_path(fonts_dir))}'"
    return value, cwd


def burn_subtitles(args: argparse.Namespace) -> dict[str, str]:
    video = Path(args.input).resolve()
    subtitles = Path(args.subtitles).resolve()
    output = Path(args.output).resolve()
    fonts_dir = Path(args.fonts_dir).resolve() if args.fonts_dir else None
    if not video.exists():
        raise FileNotFoundError(f"Input video not found: {video}")
    if not subtitles.exists():
        raise FileNotFoundError(f"Subtitle file not found: {subtitles}")
    output.parent.mkdir(parents=True, exist_ok=True)

    tools = resolve_ffmpeg_tools(args.ffmpeg_root, ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
    subtitle_filter, cwd = subtitle_filter_arg(subtitles, fonts_dir)
    run_command(
        [
            tools.ffmpeg,
            "-y",
            "-i",
            video,
            "-vf",
            subtitle_filter,
            "-c:v",
            "libx264",
            "-crf",
            str(args.crf),
            "-preset",
            args.preset,
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            output,
        ],
        cwd=cwd,
    )
    return {"output": str(output), "subtitles": str(subtitles), "ffmpeg": str(tools.ffmpeg)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare and render mm-video narration assets.")
    parser.add_argument("--ffmpeg-root", default=str(DEFAULT_FFMPEG_ROOT), help="Directory containing ffmpeg bin/.")
    parser.add_argument("--ffmpeg", help="Explicit ffmpeg executable path.")
    parser.add_argument("--ffprobe", help="Explicit ffprobe executable path.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Extract audio, frames, timeline, and editable subtitles.")
    prepare.add_argument("input", help="Input video path.")
    prepare.add_argument("--slug", help="Run directory slug.")
    prepare.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Output root directory.")
    prepare.add_argument("--interval", type=int, default=10, help="Seconds between extracted frames.")
    prepare.add_argument("--frame-width", type=int, default=960, help="Extracted frame width.")
    prepare.add_argument("--narration-file", help="Plain-text narration file to convert into timed subtitles.")
    prepare.add_argument("--narration-text", help="Plain-text narration to convert into timed subtitles.")
    prepare.add_argument("--skip-audio", action="store_true", help="Do not extract source audio.")
    prepare.add_argument("--skip-frames", action="store_true", help="Do not extract frames or contact sheet.")
    prepare.set_defaults(func=prepare_assets)

    burn = subparsers.add_parser("burn", help="Hard-burn SRT or ASS subtitles into a video.")
    burn.add_argument("input", help="Input video path.")
    burn.add_argument("--subtitles", required=True, help="Subtitle file path, preferably .ass.")
    burn.add_argument("--output", required=True, help="Output MP4 path.")
    burn.add_argument("--fonts-dir", help="Optional fonts directory for ASS rendering.")
    burn.add_argument("--crf", type=int, default=18, help="H.264 quality. Lower is higher quality.")
    burn.add_argument("--preset", default="medium", help="x264 preset.")
    burn.set_defaults(func=burn_subtitles)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    result = args.func(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
