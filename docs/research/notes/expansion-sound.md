# Sound, timecode and editorial handoff

Research date: 2026-10-28, America/Los_Angeles. The initial videos gave little detail about sound beyond preserving recorder cards and agreeing settings. The follow-up results are saved in `research/expansion-sound-reports.json`. Both selected videos were downloaded at up to 720p with metadata and captions. All transcript lines were read. Frames and uncaptioned material were not reviewed exhaustively; no Whisper call was needed.

## Curtis Judd: Timecode basics for audio & video sync

[Watch](https://www.youtube.com/watch?v=jJWe_bn9BlQ), published 2025-08-31, 9:07. The search estimate was 9:08.

The preferred transcript is the uploader-provided `transcripts/jJWe_bn9BlQ.en.vtt`; `jJWe_bn9BlQ.txt` derives from it. Both that track and the retained automatic `en-orig` track were read in full. The preferred track contains 194 text lines covering 00:00-08:54. Judd promotes his courses and discloses receiving Saramonic TC Neo generators free.

- 00:34-01:09: describes hours, minutes, seconds and frames as a way to identify frame positions.
- 01:14-02:53: explains start timecode in clip metadata and oscillator drift, including temperature-compensated generators. Product accuracy figures remain untested presenter/vendor claims.
- 02:59-04:57: synchronizes generators, then feeds a suitable generator to each camera or recorder's timecode input.
- 04:57-06:02: explains that disconnecting a generator returns the device to its own clock. He recommends continuous feed for the beginner setup; actual jam stability depends on equipment and settings.
- 06:05-07:19: describes recording LTC on an audio input when the device lacks a timecode input. This signal needs decoding into timecode metadata before timecode-based alignment. Tentacle Sync Studio and Deity software are examples.
- 07:20-07:53: returns to drift after disconnecting the generator.
- 07:53-08:41: explains that matching start timecode cannot prevent independent recording clocks drifting through a long take. He suggests feeding recorder audio to the camera as an alternative for long recordings.

This is the most useful sound supplement in the expansion. The long-take discussion qualifies the earlier impression of guaranteed sync. An LTC generator should not be assumed to supply genlock or sample-clock synchronization. Test both ends of a representative full-length recording in the actual post workflow; drift depends on the equipment, so a universal take-length threshold would be misleading.

Recommended log fields are capture and playback FPS, timecode rate/drop-frame mode, native metadata or audio-LTC method, LTC channel, jam/check time, measured offset and correction notes. This field list is the guide's application of Judd's explanation. Keep decoded or retimed derivatives separate from originals.

## Deity Microphones: Timecode Masterclass | How Timecode Works | How To Use Timecode

[Watch](https://www.youtube.com/watch?v=msXlVokMK7w), published 2022-09-16, 11:09. The search estimate was 11:10.

The complete automatic-English transcript, `transcripts/msXlVokMK7w.en-orig.vtt`, was read as the deduplicated `msXlVokMK7w.txt`: 311 lines covering 00:00-10:51. Music and demonstration passages without captions remain visually unassessed. This manufacturer video includes producer, sound-mixer and post-sound interviews and promotes timecode equipment.

- 01:16-03:04: asks during prep for camera count/models, cables, smart-slate use and frame rates so sound can bring suitable equipment.
- 03:30-04:27: coordinates with first AC, mounts hardware after the camera is built, and assigns synchronized units to sound, cameras and slate.
- 04:37-05:05: recommends spare cables and a generator for failures or an additional camera.
- 05:08-05:41: recommends a re-jam or check after lunch. Slate/viewfinder comparisons can expose a mismatch, but interpretation needs to account for display latency and repeated measurements.
- 06:24-08:09: explains common reference numbers and reduced editorial setup, then discusses distance/reflection problems in waveform alignment. Its categorical claim against timecode slip needs Judd's long-take qualification.
- 08:14-09:08: uses source timecode with clip/roll identity to make notes actionable across departments.
- 09:13-10:08: agrees the reference movie's start timecode, sync point and two-pop with picture editorial. The example has a two-second lead-in ending at 01:00:00:00.
- 10:11-10:51: closing links, promotion and giveaway; these lines were read but supplied no further workflow advice.

The prep and handoff discussion is useful, while detailed rate, drop-frame, genlock and metadata requirements need other sources. Post and delivery requirements can constrain FPS as well as cinematography. Agree start timecode and any two-pop convention with the receiver instead of adopting the example automatically.

## Production records

Assign someone to check synchronization after startup and equipment changes that could reset it. Record the method, settings and observed offsets. The schedule depends on the devices and production, including relevant power or battery changes.

Keep recorder originals, sound reports and channel labels with the same custody records as camera media. Preserve an LTC channel until the receiver can decode it. Slates and scratch audio provide useful cross-checks, and long takes need an end-of-take check as well as an aligned start.

Track source timecode, timeline/reference-picture timecode and shoot date separately. For sound turnover, agree reference-picture version, start timecode, any sync reference/two-pop, audio format, channel map and exceptions. These videos do not establish detailed AAF, BWF or iXML export settings; use the receiving sound department's requirements and relevant documentation.
