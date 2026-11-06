# Initial YouTube results 6-10

Research date: 2026-10-28, America/Los_Angeles. Selection follows `research/initial-search.json` for `dit file organization on production`. All videos were downloaded with audio at up to 720p; source metadata is retained as `videos/ID.info.json`.

Every source has an automatic-English `transcripts/ID.en-orig.vtt` and a complete timestamped `transcripts/ID.txt`. Scott Baker's supplied `en-CA` track was later downloaded, read and preferred for his text derivative. All five transcripts were read from beginning to end. Cleaning removed rolling-caption duplicates; the raw tracks remain available. Captions may misrecognize technical terms, and video frames were not reviewed exhaustively.

The first caption request for source 6 returned HTTP 429 and aborted before media download. Separate media/caption requests, with `en-orig` requested first, succeeded for all five. These sources required no Whisper calls.

## chinfat: DATA MANAGEMENT for Film and Video Part 1: Intro and Transferring Media

[Watch](https://www.youtube.com/watch?v=G83k5aZ1Gr8), published 2022-05-18, 12:25. The complete available speech transcript covers 00:08-12:10 in 408 deduplicated lines. The captions represent the remaining edges as non-speech or silence.

- 01:29-02:48: the presenter identifies himself as an editor who consulted a professional DIT. He introduces checksum software and incremental backup/synchronization.
- 02:55-04:26: creates project, shoot-day and roll/card folders.
- 04:29-05:31: copies the entire card and preserves source names. The RED example shows several files belonging to one clip.
- 06:04-07:04: examines camera-letter, roll and clip identifiers, plus possible exposure/lens metadata. Available fields depend on the camera and format.
- 07:09-08:52: the Sony example contains multiple root folders, XML and still images. He preserves the full structure.
- 08:57-10:07: imports into Premiere and organizes the project. Removing a thumbnail or photo from the project need not delete its disk source.
- 10:11-12:10: changes NLE display names while retaining disk filenames for a Resolve round trip. He advises keeping card internals unchanged during production.

This explains why extracting only the MP4s can lose useful or required companion files. Pair its ordinary Finder-copy demonstration with a verified offload procedure. At 03:30-03:45, the claim that filename spaces corrupt footage is overstated: simple character sets help interoperability and scripting, but spaces do not inherently alter video bytes. The reshoot warning about renamed RED clips also describes an extreme outcome; recovery depends on the actual change. Preserve native names without assuming every rename is irrecoverable.

This is useful for learning card structure, although Jon Branden covers much of the same material. Follow-up queries were `DIT camera card folder structure sidecar metadata preserve`, `DaVinci Resolve proxy original camera filename reel name relink`, and `RED spanned clips camera originals naming`.

## Scott Baker: DMT vs DIT... but more importantly, BACK UP YOUR FOOTAGE

[Watch](https://www.youtube.com/watch?v=jc3mq1uNOmM), published 2024-07-31, 6:30. The complete supplied English-Canadian track covers 00:07-06:16 in 92 lines. Its 163-line automatic counterpart was also read fully.

- 00:43-01:18: assigns someone to receive cards and start backups even when the crew has no DIT/DMT position.
- 01:18-01:43: calls for two backups before reusing a card so wiping it does not leave a single copy.
- 01:45-02:28: catalogs footage by day or scene and records the relationship between original clip names, scenes and takes.
- 02:29-03:20: agrees specifications and labels before shooting across slates, editorial and the data role. On smaller shoots, the editor may also handle data.
- 03:25-05:29: describes the DIT's work with the cinematographer on the look and dailies color.
- 06:01-06:14: repeats the need for an assigned backup owner.

The responsibility and labeling advice is useful. His role description emphasizes dailies color and underrepresents broader camera/image-pipeline work. The supplied caption at 03:26 expands DIT as "Digital Intermediate Technician"; whether the error is spoken or caption-generated remains unverified. The relevant title is Digital Imaging Technician.

The video leaves checksum details unspecified. The guide interprets the backup requirement as independent, verified destination copies. It is a short role introduction and falls below the main practical demonstrations in watch priority.

Follow-up queries: `small crew camera report clip filename scene take metadata`; `digital imaging technician data manager responsibilities small production`; `camera sound editorial workflow preproduction test`.

## FocusInMotion: My Free DIT/Data Wrangling Workflow On Set

[Watch](https://www.youtube.com/watch?v=yfRbRjTaO3s), published 2025-10-21, 10:58. The full available transcript covers 00:02-10:52 in 275 deduplicated lines. The presenter reports using the procedure on a six-day student short involving more than six TB and 30 cards; that experience was not independently verified.

- 00:38-01:14: introduces Resolve's Media-page Clone Tool with a whole-card source, one or more destinations and checksum verification.
- 01:15-02:45: adds Parashoot, Pomfort SealVerify and Disk Drill for erasure, verification and recovery. Captions misrecognize the product names; check the official documentation before adopting the tools.
- 02:47-04:27: places full cards on the left, ingest in the middle and released cards on the right, with labeled areas. The dock is optional.
- 04:29-04:53: moves a card's identifying label onto its reader during ingest.
- 04:55-05:51: clones the whole card into a `day/video/A001` folder and describes adding SSD destinations. The example uses only the laptop SSD.
- 05:53-06:07: says jobs must be prepared before a batch starts in the demonstrated Clone Tool version.
- 06:10-07:00: configures Parashoot destinations, then imports the copied card into a corresponding Resolve bin.
- 07:02-08:03: reverifies a manifest in SealVerify and saves a report. The presenter cannot recall why one file cannot be checked.
- 08:04-09:08: checks destinations, uses Parashoot erase, assigns the next roll label and releases the card for in-camera formatting.
- 09:09-10:52: repeats the procedure with another card, keeping its physical label, folder and bin aligned.

The visible card states and labels are worth adopting. Before release, identify every warning or excluded file and record its disposition. The unexplained verification warning and single-destination example leave the demonstrated release decision inadequately supported for a real shoot.

Reversible erasure and recovery software cannot replace verified independent copies, especially after overwrite. Product availability and recovery pricing also need current checks. The guide therefore places authorization after verification and documented review, with in-camera formatting as a separate step.

The physical demonstration is useful supplementary viewing. Jon Branden provides a more conservative, though longer and older, foundation. Follow-up queries were `Pomfort SealVerify Media Hash List verification`, `Parashoot camera card erase backup verification`, `DIT card labeling camera roll offload log release workflow`, and `DaVinci Resolve clone tool multiple destinations checksum`.

## Jon Branden: DIT/Media Management Basics for Beginners

[Watch](https://www.youtube.com/watch?v=kHPxUm3zv5I), published 2020-01-29, 21:33. All 455 deduplicated transcript lines were read, covering 00:03-21:28, including the final audio-card addendum.

- 00:38-01:53: organizes folders for another person to understand; numbered top-level folders control their order.
- 02:15-03:43: uses year-month-day naming for chronological sorting and accepts a four-digit year. A production should choose one consistent date convention.
- 03:52-05:04: identifies camera/roll with `A001`, `A002` and `B001`, even when card volume labels repeat.
- 05:04-07:14: preserves whole cards, including Panasonic/Sony metadata and internal folders.
- 07:20-09:24: sets up a Resolve 15/16-era project and opens Clone Tool.
- 09:24-12:00: selects the volume as source, creates the destination folder and checks both paths.
- 12:00-13:53: allows copying and verification to finish under deadline pressure.
- 13:58-16:57: checks completion, inspects `.mhl` and `md5sum.txt`, and organizes reports by roll. He moves manifests away from the card folder to make its contents resemble the source.
- 17:08-19:25: recommends three separate copies, preferably made from the card, and describes geographically separated storage saving a project after two drive failures.
- 19:41-21:28: applies the same copying and verification to audio, usually grouped by shoot date with extra card identifiers as needed. Labels are agreed with editorial.

This is the broadest operational lesson in the batch. Its older interface needs translating to the installed Resolve version. Preserve manifests where their generating tool expects them; relative paths or MHL-version layout may matter. A central report folder can hold a copy or index. Read the completion result and report rather than inferring success from the presence of a manifest.

Direct copies from the source can reduce propagation risk, but a verified copy chain with preserved reference hashes and destination checks can also be valid. Geographic separation requires copies to travel and remain apart. Sound may produce several cards per day, so the inventory must reflect the actual shoot.

Follow-up queries: `ASC MHL chain of custody verified camera offload`; `DIT offload reports checksums media hash list`; `location sound BWF metadata sound report camera sync workflow`.

## Martin Leon Lindstedt: Data Management for Video Production

[Watch](https://www.youtube.com/watch?v=1zFbvpD0EeQ), published 2025-04-13, 4:14. The search estimate was 4:15; video metadata gives 254 seconds. The complete transcript covers 00:00-04:11 in 101 deduplicated lines.

- 00:30-01:16: uses the laptop SSD for offloads/cache, an external copy and iCloud Drive.
- 01:16-02:00: keeps active projects on an external SSD; both it and the laptop are backed up to a Time Machine drive at work.
- 02:07-03:04: sends the complete project to an offline archive and a consolidated timeline or finished export to an online NAS-attached drive.
- 03:10-03:52: accepts keeping unused originals on only one archive disk while the consolidated project/export exists elsewhere.

That retention choice conflicts with the request to preserve all production material. A consolidated subset or final export omits unused originals. Any decision to accept their loss needs an explicit production retention policy.

Cloud sync also needs checks for completed upload, retained versions and restoration before it counts as a dependable copy. The video gives no checksum-based release procedure or metadata specification. It is low-priority viewing for this guide.

## Follow-up subjects

The initial videos prompted supplementary research on timecode, BWF metadata and sound handoff. They also left the relationship between copying, verification, QC and card release insufficiently specified. The guide records a result for each stage.

A practical record should link the reusable physical card to each new roll, original clip names to production notes, and every copy to its destination and report. Keep manifests valid while retaining a readable daily summary. The guide's conservative retention policy follows the user's requirement to preserve originals; Lindstedt's single-copy archive example should remain a documented disagreement.
