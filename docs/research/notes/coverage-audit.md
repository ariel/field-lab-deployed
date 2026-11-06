# Media and transcript audit

Audited on 2026-10-28, America/Los_Angeles. The checks cover the initial ten search results and the follow-up videos listed below. Review coverage comes from the research notes; this audit did not repeat the transcript readings or screen every frame.

## Files and streams

All 20 videos have source metadata, raw English VTT and cleaned timestamped text. Every MP4 contains video and audio, with a duration less than one second away from its source metadata. Total runtime is 164.15 minutes; video files occupy 656,962,685 bytes (626.5 MiB). No `.part` or `.ytdl` files remained.

Video height is at most 720 pixels; one source is 640 pixels. MP4 files retain H.264, VP9 or AV1 video and Opus audio. Use YouTube, Chrome or a compatible player such as VLC if needed. Native QuickTime playback was not tested.

## Identity and caption timing

The table records the latest cue end among retained English tracks. Automatic cues sometimes extend roughly 1-2 seconds beyond the video. A short uncaptioned tail may contain music or an outro, but timing alone cannot establish whether speech was omitted.

| # | Source / ID | Media | Last caption end | Clean text | Review note contains source |
|---|---|---:|---:|---|---|
| 1 | [Bullet Proof DIT: Data Wrangling, Shotput Pro, Workflow for Film & TV](https://www.youtube.com/watch?v=LabiSMxjM84) / `LabiSMxjM84` | 3:48 | 3:50 | yes | yes |
| 2 | [My Video Editing Folder Structure and File Management Template](https://www.youtube.com/watch?v=zoAXqrr1pgc) / `zoAXqrr1pgc` | 14:10 | 14:09 | yes | yes |
| 3 | [How to Manage Data on a Film Set](https://www.youtube.com/watch?v=zMS7-K-if4c) / `zMS7-K-if4c` | 9:16 | 9:18 | yes | yes |
| 4 | [What Does A Digital Imaging Technician Do On Set? - DIT](https://www.youtube.com/watch?v=zXaN4djhghY) / `zXaN4djhghY` | 7:29 | 7:30 | yes | yes |
| 5 | [Intelligent Data Wrangling Software for DIT & Data Management for filmmakers from Hedge](https://www.youtube.com/watch?v=GumCcLnIlYA) / `GumCcLnIlYA` | 7:57 | 7:59 | yes | yes |
| 6 | [DATA MANAGEMENT for Film and Video Part 1: Intro and Transferring Media](https://www.youtube.com/watch?v=G83k5aZ1Gr8) / `G83k5aZ1Gr8` | 12:24 | 12:26 | yes | yes |
| 7 | [DMT vs DIT... but more importantly, BACK UP YOUR FOOTAGE](https://www.youtube.com/watch?v=jc3mq1uNOmM) / `jc3mq1uNOmM` | 6:29 | 6:19 | yes | yes |
| 8 | [My Free DIT/Data Wrangling Workflow On Set](https://www.youtube.com/watch?v=yfRbRjTaO3s) / `yfRbRjTaO3s` | 10:57 | 10:56 | yes | yes |
| 9 | [DIT/Media Management Basics for Beginners](https://www.youtube.com/watch?v=kHPxUm3zv5I) / `kHPxUm3zv5I` | 21:32 | 21:33 | yes | yes |
| 10 | [Data Management for Video Production](https://www.youtube.com/watch?v=1zFbvpD0EeQ) / `1zFbvpD0EeQ` | 4:14 | 4:15 | yes | yes |
| 11 | [Silverstack Lab Series Ep 2 \| Essential Camera Metadata Checks for DITs](https://www.youtube.com/watch?v=m2pmNhTd9Kg) / `m2pmNhTd9Kg` | 7:12 | 7:14 | yes | yes |
| 12 | [Pomfort Silverstack Offload Manager Released - Securely Backup Your Footage on Set](https://www.youtube.com/watch?v=iqMpSs7AN3c) / `iqMpSs7AN3c` | 9:44 | 9:45 | yes | yes |
| 13 | [Timecode basics for audio & video sync](https://www.youtube.com/watch?v=jJWe_bn9BlQ) / `jJWe_bn9BlQ` | 9:06 | 9:04 | yes | yes |
| 14 | [Timecode Masterclass: How Timecode Works Through Production](https://www.youtube.com/watch?v=msXlVokMK7w) / `msXlVokMK7w` | 11:09 | 11:11 | yes | yes |
| 15 | [How to use Proxy Files to Edit SUPER FAST in DaVinci Resolve!](https://www.youtube.com/watch?v=7wSQBoLcBrA) / `7wSQBoLcBrA` | 13:33 | 13:31 | yes | yes |
| 16 | [Verification Options - ShotPut Pro Tutorials (macOS 2023)](https://www.youtube.com/watch?v=3PPGH0Y6YF4) / `3PPGH0Y6YF4` | 3:22 | 3:23 | yes | yes |
| 17 | [Quickly Generate Sound Reports From Sound Devices WaveAgent](https://www.youtube.com/watch?v=Z1Qg5Twvzns) / `Z1Qg5Twvzns` | 3:50 | 3:52 | yes | yes |
| 18 | [OffShoot - Getting Started](https://www.youtube.com/watch?v=UCHBx3iE4ls) / `UCHBx3iE4ls` | 3:06 | 3:03 | yes | yes |
| 19 | [OffShoot Tutorial: Verification Modes Explained - Speed Up Your Video Ingest Workflow](https://www.youtube.com/watch?v=aLLa-M6wbDI) / `aLLa-M6wbDI` | 2:06 | 2:06 | yes | yes |
| 20 | [How to export clips and metadata to Adobe Premiere Pro](https://www.youtube.com/watch?v=aIyp5cpT-JE) / `aIyp5cpT-JE` | 2:34 | 2:36 | yes | yes |

## Transcript provenance

The initial, expansion and expert review notes record full readings, including introductions, promotion, tangents and endings. Those coverage statements support the full-read record; the table separately confirms that each source appears in a review note.

Joshua Kirk's supplied English track was read after its automatic counterpart. The preferred wording reference is `zoAXqrr1pgc.manual.txt`, derived from `zoAXqrr1pgc.en-ehkg1hFWq8A.vtt`. The canonical `.txt` preserves the earlier automatic transcript. Other supplied tracks are retained where retrieved.

All successful transcripts came from YouTube. A Whisper request for `zMS7-K-if4c` returned HTTP 401; the original-English YouTube track was subsequently recovered. No Whisper output is included, and the failed request did not print the credential.

## Scope of the checks

ffprobe checked stream presence and duration. No full decode-error scan or word-by-word audio correction was performed. Automatic captions can omit speech or misrecognize names; review of those captions leaves visual-only details unassessed. Cleaned text removes rolling duplicates, with raw VTT retained for inspection.

The saved yt-dlp result defines initial search order. Signed-in Chrome returned a different order, and future searches may differ again. Technical advice is assessed in the source notes and primary-document checks, independently of download success.

Exact stream and caption timing is saved in `research/coverage-audit.json`. The inventory can be regenerated with `scripts/agent-a-audit.py`; `scripts/agent-a-write-audit.py` renders the audit report.
