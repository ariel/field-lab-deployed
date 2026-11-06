# Wave Agent sound reports

Scott Baker recommends mapping original clip names to scene/take, and Jon Branden applies the same preservation procedure to sound as to picture. Their videos leave the sound report unspecified. Curtis Judd's distinction between native timecode metadata and audio LTC adds another field editorial needs to understand.

Follow-up searches on 2026-10-28 each returned five entries:

- `Sound Devices Wave Agent sound report metadata tutorial`, saved in `research/expert-wave-agent.json`.
- `Tentacle Sync Studio metadata timecode workflow editorial`, saved in `research/expert-tentacle.json`.

Matt Price's demonstration was selected because it shows report-field choices. A vendor overview also appeared in the results. The assessment here relies on Price's demonstrated procedure; professional credits were not independently checked.

## Matt Price (Soundrolling): Quickly Generate Sound Reports From Sound Devices WaveAgent

[Watch](https://www.youtube.com/watch?v=Z1Qg5Twvzns), published 2021-08-06, 3:51.

The complete video and audio are in `videos/Z1Qg5Twvzns.mp4`, with source metadata in `videos/Z1Qg5Twvzns.info.json`. No supplied subtitle language was listed. The automatic English VTT is `transcripts/Z1Qg5Twvzns.en-orig.vtt`; its readable derivative is `transcripts/Z1Qg5Twvzns.txt`. All 118 lines, covering 00:01-03:49, were read, including the introduction and closing. Video frames were not reviewed exhaustively. No Whisper call was needed.

- 00:01-00:48: imports example files from two projects and inspects dates, track information, notes and timecodes. Separate production reports should remain clearly identified.
- 00:49-01:13: discusses daily reports and a larger searchable report.
- 01:20-01:38: selects files and creates a report. Clearing an application list must be distinguished from deleting its source files.
- 01:38-02:15: includes every take, then chooses frame rate, start/end timecode and duration. Checks sample rate and bit depth, and adjusts the display of notes and track names.
- 02:18-02:40: reviews the exported report. T1/T2/T3 identify channels in a polyphonic file; descriptive track labels still need to be entered.
- 02:43-03:04: adds a note and regenerates the report.
- 03:06-03:30: adds project/header information and confirms that the notes appear.
- 03:32-03:49: discusses Broadcast WAV metadata.

## Report fields and corrections

The guide recommends a daily report with a project-level index. Key entries to original filename, sound roll/date and project. Include scene/take where available, start/end timecode, duration, recording frame-rate/timecode mode, sample rate, bit depth, track names and notes. This field list combines the demonstration with the earlier custody and timecode research. The video itself covers report inclusion, notes and headers; it does not show LTC decoding or sound-sync QC.

Check actual field values. A metadata-capable format cannot ensure that someone entered the right scene or channel name. Identify any LTC audio channel and the required decode method, and preserve it until the receiver can decode it.

Enter labels correctly in the recorder when possible. Document later corrections and make them through a controlled database/export or working-copy procedure. The transcript does not establish whether each demonstrated edit writes back to the audio file. Avoid changing checksum-verified originals without deliberately creating and verifying a new version.

The interface dates to 2021, so current platform compatibility needs a separate check. Although Price mentions multiple report formats, the transcript does not name them; any CSV/PDF claim requires documentation. The 3:51 demonstration is a useful sound-specific follow-up to the main watchlist.
