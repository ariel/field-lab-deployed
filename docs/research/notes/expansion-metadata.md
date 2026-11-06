# Camera metadata checks and offload reports

Both transcripts were read in full, including introductions, sponsorship, digressions and endings. The original automatic English VTTs retain the timestamps. Caption errors include "good text" for what appears to be "good takes," "real tape" for reel/tape, and product names. Video frames were not reviewed exhaustively. Dates and durations come from the downloaded YouTube metadata; neither source required Whisper.

## VID SHEPHERD: Essential Camera Metadata Checks for DITs

[Watch](https://www.youtube.com/watch?v=m2pmNhTd9Kg), published 2026-03-05, 7:13.

The full transcript is `transcripts/m2pmNhTd9Kg.txt`: 1,523 deduplicated words, ending at the spoken cue 7:11.599.

- 0:02-1:44: changes project day/location and checks card/project size, duration and counts.
- 1:46-2:38: examines list columns for flags, ratings, camera, duration, exposure, white balance and shutter.
- 2:38-4:05: checks flicker and sensor frame rate. High-speed modes can change resolution or aspect ratio; the presenter recommends telling camera and recording the change in reports.
- 4:09-5:49: checks project frame rate, planned recording mode and timecode, particularly on the first card.
- 5:50-6:35: inspects reel/tape, date, tracks, look/color metadata and backup count.
- 6:37-7:11: explains that wind spoiled the longer recording and defers backup configuration to another episode.

This belongs in the main watchlist because it shows which recorded settings deserve attention. The camera examples need checking against the relevant manual, and intentional off-speed recording must be assessed against the production plan. Wind affects the audio. Backup setup and metadata export are outside this episode's coverage.

## CineD: Silverstack Offload Manager launch demonstration

[Watch](https://www.youtube.com/watch?v=iqMpSs7AN3c), published 2018-09-19, 9:44.

The full transcript is `transcripts/iqMpSs7AN3c.txt`: 1,656 deduplicated words, with the final spoken cue at 9:23.870 before the outro.

- 0:45-1:49: the vendor introduces multiple-destination offloads and reports.
- 1:53-3:18: demonstrates a card scan, two destinations, a reusable preset and task history.
- 3:23-4:23: shows separate copy and verification phases. Verification rereads destination files for checksum comparison. The discussion of deferred verification assumes the source card is retained.
- 4:24-5:42: covers simultaneous sources/destinations and media-aware copying.
- 5:44-6:21 and 8:00-8:32: the daily report lists cards, formats, running time, copy/verification times and hash algorithm; a detailed report lists files.
- 7:09-7:59 and 8:36-9:23: presents speed, price and trial claims from 2018.

The copy and report demonstrations are useful supplements. Treat the quoted 300 MB/s hashing speed as a historical product claim; current performance, prices and trial terms need separate checks. Fast noncryptographic integrity hashes do not establish resistance to deliberate tampering.

## Report contents

An offload report records destinations and verification results. An editorial clip log records scene/take, sync context, intended camera mode and exceptions. Keep both linked to the same roll and original clip identifiers. When an unexpected camera-mode change appears, record the affected clips and tell camera promptly. This is the guide's recommended procedure.
