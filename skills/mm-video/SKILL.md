---
name: mm-video
description: Use when creating narration assets for existing videos, extracting timelines, generating subtitles, burning captions, or preparing optional ASR, vision, and TTS handoffs.
---

# mm-video

`mm-video` 是 Article Pool 里的现有视频解说工作流。它负责把一个已有视频拆成可审阅的时间轴、音频、关键帧、字幕和最终 MP4。模型负责理解画面与撰写解说，`scripts/mm_video.py` 只做确定性的媒体处理。

## 首次加载

先读取 `workflow/mm-video/manifest.json`，确认输入视频、宿主能力、产物路径和 ffmpeg 路径。默认 ffmpeg 根目录是：

```powershell
D:\Environment\ffmpeg\ffmpeg-7.0.2
```

如果宿主 PATH 还没有生效，命令里必须显式传：

```powershell
python scripts/mm_video.py --ffmpeg-root D:\Environment\ffmpeg\ffmpeg-7.0.2 prepare <input.mp4> --slug <slug>
```

## 工作流

1. 先运行 `prepare`，生成 `reports/mm-video/{run_id}/timeline.json`、`narration.md`、`subtitles.ass`、`subtitles.srt`、`audio/source.wav`、`frames/` 和 `contact_sheet.jpg`。
2. 如果有 ASR 能力，用 `audio/source.wav` 转写原声；没有就让用户提供转写或只基于画面写解说。
3. 如果有视觉能力，检查 `frames/` 和 `contact_sheet.jpg`，把画面、OCR、操作状态补进 `timeline.json` 或 `narration.md`。
4. 写最终解说稿，保持解释性，不编造画面中不存在的事实。
5. 把最终解说转为 `subtitles.ass`；短视频平台优先使用硬字幕。
6. 运行 `burn` 烧录字幕：

```powershell
python scripts/mm_video.py --ffmpeg-root D:\Environment\ffmpeg\ffmpeg-7.0.2 burn <input.mp4> --subtitles <subtitles.ass> --output <output.mp4>
```

## 输出契约

- `timeline.json`：视频元数据、片段、产物路径和 ffprobe 输出。
- `narration.md`：解说稿编辑区和每段时间码说明。
- `subtitles.ass`：推荐用于烧录的字幕文件，默认底部安全区、白字深色底。
- `subtitles.srt`：兼容播放器或其他工具的字幕文件。
- `audio/source.wav`：16kHz 单声道原始音频，供 ASR 使用。
- `frames/frame_0001.jpg`：按时间间隔抽取的关键帧。
- `contact_sheet.jpg`：快速审片图。
- `output.mp4`：烧录字幕后的成片。

## 质量门禁

- 没有 ASR/视觉/TTS 时，不要假装已经自动理解全部内容；明确使用占位、人工输入或当前模型可见的关键帧。
- 短视频发布版优先硬字幕，不依赖平台保留软字幕轨。
- 字幕不能压到底部平台遮挡区；默认 `ASS` 的 `MarginV` 已留出底部空间。
- 交付前至少检查 `timeline.json`、`contact_sheet.jpg` 和最终 MP4 的视频/音频流。
- 付费能力只能作为可选增强：ASR 转写、视觉理解和 TTS 配音都不能成为脚本运行的硬依赖。
