# Resolve proxy workflow

[How to use Proxy Files to Edit SUPER FAST in DaVinci Resolve!](https://www.youtube.com/watch?v=7wSQBoLcBrA) was downloaded at up to 720p. Its complete cleaned transcript was read from the first spoken line at 00:01 through 12:58, including the closing promotion. The roughly 13:34 media also contains non-speech/outro material. The original automatic VTT and timestamped text are retained.

## Demonstration

- 01:24-02:28: sets proxy resolution and codec; recommends quarter-resolution H.264 for smaller files.
- 02:30-04:09: explains project-level and application-level storage preferences, then recommends proxy subfolders beside original media.
- 04:11-06:22: generates proxies, inspects PXY/HQ status, switches preference between proxies and originals, and disables proxies.
- 06:24-06:56: says Resolve uses originals for final rendering by default.
- 06:59-10:19: demonstrates background generation with Blackmagic Proxy Generator and watch folders.
- 10:21-12:20: describes a mismatch involving interpreted slow-motion frame rates and externally generated proxies. Suggested workarounds are to generate before interpretation or use Resolve's internal generator afterward.
- 12:22-end: recaps the procedure and promotes a cheat sheet and paid course.

## Use on a production

This is a useful software lesson after the offload and metadata tutorials. Its broad claims about speed, H.264 suitability and never needing 10-bit proxies exceed the example demonstrated. Choose the codec and bit depth with editorial, using the actual playback hardware.

For the guide's folder convention, generated media belongs in a separate derivative tree. If software requires adjacent proxy folders, use a designated working copy so the preserved camera-card package stays unchanged. That convention differs from the presenter's recommendation.

Include off-speed footage in the preproduction test. Check source/proxy duration, timecode, frame rate, audio layout and relinking in the installed software version. Confirm the source used for final export. Synced dailies may need different treatment from attachable camera proxies.
