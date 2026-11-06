# Exporting metadata to editorial

VID SHEPHERD's episode ends before metadata export, and CineD's offload reports cover transfers rather than editorial logging. Pomfort's documentation says edited logging fields can remain in the Silverstack library. The follow-up search addressed the missing export step.

The exact queries `Pomfort Silverstack ALE metadata export Avid reel timecode` and `Pomfort ASC MHL MediaVerify verification workflow` returned no entries through yt-dlp. Those results are saved in `research/expert-ale.json` and `research/expert-mhl.json`. Shorter queries, `Silverstack ALE` and `Pomfort MediaVerify`, are saved in `research/expert-ale-refined.json` and `research/expert-mhl-refined.json`. The ALE search found the official demonstration below. MediaVerify returned broad videos already reviewed, so this search added no practical ASC MHL validation demonstration.

## Pomfort: How to export clips and metadata to Adobe Premiere Pro

[Watch](https://www.youtube.com/watch?v=aIyp5cpT-JE), published 2017-05-18, 2:35.

The complete English transcript was read: `transcripts/aIyp5cpT-JE.txt`, 317 deduplicated words, from 0:04.870 through the final spoken cue at 2:31.540. Both the supplied `en` VTT and automatic `en-orig` VTT are retained. The supplied track still misrecognizes terms such as reel name. No Whisper transcription was needed.

- 0:04-0:46: introduces XML transfer of clips and metadata using already-transcoded editorial media.
- 0:48-1:17: selects a bin/export and the media volume, directing the XML to the travel drive intended for the editor.
- 1:21-1:39: chooses metadata fields and reel-name mapping, then saves the XML.
- 1:42-2:03: imports the XML into Premiere to populate a bin.
- 2:06-2:32: describes automated metadata export during Silverstack Lab transcoding.

This short first-party demonstration makes the handoff step concrete. Its interface dates to 2017 and its transcodes are already configured. Current Pomfort documentation still describes volume selection and configurable Premiere reel mapping, but a production needs to test its installed versions. The video stops short of a complete original-media reconform or sound handoff. [Exporter reference](https://kb.pomfort.com/silverstack/reference/importandexport/exporters/).

## Handoff check

Import the delivered XML/ALE/CSV from the recipient's drive, inspect representative scene/take/notes and reel values, then open the intended files. An export can point to an unavailable on-set volume even when the delivered drive contains the media. Retain the DIT library alongside the interchange export so its annotations remain recoverable if a mapping is incomplete. This acceptance check is a recommendation drawn from the demonstration.

The local video, `videos/aIyp5cpT-JE.mp4`, passed ffprobe checks for video, audio and 720p dimensions. Source metadata is in `videos/aIyp5cpT-JE.info.json`; the download log is `research/expert-metadata-download.log`.
