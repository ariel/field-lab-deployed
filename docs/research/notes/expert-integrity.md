# ShotPut Pro verification options

The initial videos left verification details unclear. Sam Howe described a verified report before demonstrating desktop card clearing; FocusInMotion mentioned an unexplained warning file; Scott Balkum used "triple checked" without a specific procedure. These gaps prompted searches for the software makers' instructions.

The saved searches each returned five entries:

- `Imagine Products ShotPut Pro checksum verification offload report workflow`, in `research/expert-integrity-vendor.json`.
- `DIT data wrangler card release workflow interview`, in `research/expert-integrity-release.json`.

The release search mostly repeated Sam Howe, FocusInMotion, Luis M Peña and Scott Balkum. The vendor search found official tutorials on offloading, verification and troubleshooting. The verification tutorial addresses the difference between file-size comparison and checksum checking.

## Imagine Products: Verification Options - ShotPut Pro Tutorials (macOS 2023)

[Watch](https://www.youtube.com/watch?v=3PPGH0Y6YF4), 3:23. Download metadata gives a publication date of 2022-09-07; the current title says macOS 2023 and the description references v2022. Menu details therefore need checking in the installed version.

This is the software maker's explanation of its verification settings. It supports claims about those settings; performance preferences are vendor claims. No named presenter's production credentials or independent field test were established.

The entire original-English automatic transcript was read: 493 deduplicated words through the final spoken line at 3:16, with the last cue ending at 3:23.300. The downloaded video has audio and is 720p. The `en` caption request returned HTTP 429; `en-orig` succeeded without Whisper. Files are `videos/3PPGH0Y6YF4.mp4`, `videos/3PPGH0Y6YF4.info.json`, `transcripts/3PPGH0Y6YF4.en-orig.vtt` and `transcripts/3PPGH0Y6YF4.txt`.

- [0:21-0:44](https://www.youtube.com/watch?v=3PPGH0Y6YF4&t=21s): verification can be configured globally or overridden by a preset.
- [0:46-1:52](https://www.youtube.com/watch?v=3PPGH0Y6YF4&t=46s): discusses xxHash speed and noncryptographic use, plus MD5 compatibility.
- [1:56-2:44](https://www.youtube.com/watch?v=3PPGH0Y6YF4&t=116s): covers SHA, C4 and legacy CRC32; discourages CRC32 for new workflows.
- [2:46-3:08](https://www.youtube.com/watch?v=3PPGH0Y6YF4&t=166s): explains file-size comparison. Equal file sizes can still contain different bytes.

The statement that SHA is "outdated" expresses the vendor's offload-speed preference and should not be generalized into a security claim. Choose hashes supported by the production's tools and interchange requirements. Noncryptographic checksums address accidental corruption; adversarial authenticity needs a separate assessment. The C4 filename example does not justify renaming archived camera originals.

The video does not show destination rereads, a failed transfer, report interpretation or card-release approval. Its useful addition to the guide is a preflight check of the preset that will actually run. Record the chosen algorithm and each destination's result. Pair that check with the Pomfort copy/verification demonstration and the production's release procedure.
