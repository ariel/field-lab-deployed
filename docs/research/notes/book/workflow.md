# Brown chapters 9–12: additions to the small-crew workflow

Read against the existing `DEEP-DIVE.md` and `MULTI-CAMERA-WORKFLOW.md`, October 28, 2026. These notes distinguish Brown's 2015 book from suggested adaptations to the present guide. No current product specifications or prices were inferred from the book.

## Coverage

All extracted prose, headings, captions, tables and XML text in these four chapters was read. The final line in each extraction has no terminating newline, so `wc -l` understates its displayed line count by one. Word counts use whitespace splitting and include source markers and captions.

| Chapter | Full extracted coverage | Words | Original EPUB sections | Image references |
|---|---|---:|---|---:|
| 9, The DIT Cart | `research/book/chapters/ch09.txt`, lines 1–129 | 3,578 | `OEBPS/c3F1.xhtml`, `OEBPS/c3F7.xhtml` | 35 |
| 10, Data Management | `research/book/chapters/ch10.txt`, lines 1–221 | 8,579 | `OEBPS/c3R6.xhtml`, `OEBPS/c3RC.xhtml` | 31 |
| 11, Workflow | `research/book/chapters/ch11.txt`, lines 1–338 | 12,167 | `OEBPS/c42B.xhtml`, `OEBPS/c42H.xhtml` | 29 |
| 12, Metadata & Timecode | `research/book/chapters/ch12.txt`, lines 1–149 | 3,515 | `OEBPS/c4KM.xhtml`, `OEBPS/c4KU.xhtml` | 8 |

Total: 27,839 extracted words; 103 image references. No images were visually inspected for this review. Figure references below rely on captions and surrounding prose only. In particular, the actual columns and values visible in Figures 10.3, 10.9 and 12.7 have not been independently read from pixels. The skill and source-notes were also read fully. This is full text coverage of the assigned chapters, not full visual coverage of the book.

## What I like most

### Make the look part of the record

Brown's strongest addition to the existing file-management advice is his concern with preserving the intended image. The production can retain every original and still leave the editor wondering whether a dark, warm or low-contrast picture was deliberate. Chapter 11 describes sending graded stills, LUTs, color decisions and suitable offline images to post. The ASC-CDL discussion makes this practical: ten parameters can carry basic primary corrections, provided the receiving system applies them in the agreed color context.

Sources: chapter 11, “Working with the DP,” `OEBPS/c42H.xhtml`, lines 130–136; “Ten Numbers: ASC-CDL” through “Primary Correction Only,” lines 239–255. Chapter 10's Figure 10.9 caption explicitly describes a LUT log with scene/take and ASC-CDL columns for three cameras: `OEBPS/c3RC.xhtml`, lines 77–78.

My adaptation: add a small look register when looks change during shooting. Identify the camera and applicable clips or time range, the LUT/CDL filename and version, the expected source curve/gamut, transform order, the reference still and who approved it. Record whether the look was used for monitoring, baked into a derivative, or recorded into the original. This extends the guide's existing `look_version` field and `04_LOOKS` folder into a traceable history. It does not require live-grading hardware.

For the fictional pump scene, camera A's wide and camera B's close-up can share `PUMP_REPAIR_01` while using separate technical input transforms. A reference still from each angle can show the intended match. A single shared LUT name is insufficient evidence that different camera sources will look alike. This example is my synthesis, not an example from Brown.

### Design the day around the work remaining after wrap

Chapter 9 notices a very ordinary failure: lighting power may disappear while the DIT is still copying. It also treats access, cooling, cable spares, mobility and backup power as workflow requirements. Chapter 11 describes how transcoding can keep someone on location long after everyone else leaves, and explicitly warns about one person doing two jobs.

Sources: chapter 9, “Small Genni,” “AC Cables,” “Backup Power,” “Video and Data Cables,” and “Failover,” `OEBPS/c3F7.xhtml`, lines 49–69 and 81–82; chapter 11, “DIT Working Alone” and “Loader Working Alone,” `OEBPS/c42H.xhtml`, lines 124–129, plus “Transcoding” / “On or Off the Set?” lines 174–177 and “Dailies,” lines 188–196.

My adaptation: during the preproduction test, time an actual card through copying, verification, QC and log completion. Measure proxy rendering separately. Schedule card swaps and the last-card handover around those results, leaving power and working space available until required checks finish. If the solo operator is still filming, postpone optional proxy rendering and detailed annotations, while preserving enough cards to avoid rushed reuse. Record the unfinished tasks explicitly. The existing guide covers backlog and throughput; the useful additions are a wrap-power agreement and a deliberate order for work competing for the same person and machine.

I like this because it locates the problem in the schedule. Buying a faster drive does not create an extra pair of eyes or stop a generator being switched off. A laptop battery also warrants checking the power arrangement for every attached reader, hub and destination drive. That last check is our application of the book's power principle, not a claim about a particular Mac setup.

### Treat notes as a searchable record of the shoot

Chapter 12 distinguishes automatically captured source metadata, added metadata and derived metadata such as speech recognition. It separately describes structural, descriptive, administrative and technical metadata. Its useful observation is that keywords and notes turn the collection into something you can search and classify.

Source: chapter 12, “Other Types of Metadata,” `OEBPS/c4KU.xhtml`, lines 72–96; “Metadata at the DIT Cart,” lines 148–149. Chapter 10, “Cataloging Systems: CatDV Pro,” `OEBPS/c3RC.xhtml`, lines 135–137 describes a searchable catalog distinct from the media's physical storage. Its product-specific claims are historical.

My adaptation: extend the narrative log only with fields that answer likely editorial questions. For a documentary these could be person, place, story topic, action, useful quote, related sequence, pickup needed and a reference to any permissions or usage restrictions already documented by production. Administrative rights metadata is in Brown; this particular field selection is ours, and is not legal advice. Keep a small consistent vocabulary, such as `pump_history`, `repair_attempt`, and `family`, so similar material can be found across cameras and days.

Preserve provenance: distinguish a camera-reported field, a crew observation, an editorial interpretation and an automatically generated transcript. Mark uncertain spellings or quotations and record later corrections. The current guide already distinguishes observations from edit ideas and checked quotations from paraphrases. Brown's contribution is a broader account of where metadata comes from and why administrative context belongs with it. This gives a reason to keep the CSV/NLE workflow without making an expensive cataloging application a prerequisite.

### Keep a paper route when the digital route slows the shoot

Brad Greenspan's account prefers separate camera reports for speed and battery independence. Reports go to continuity and the loader, then may be scanned or transcribed for delivery; circled takes are passed to post. Jillian Arnold's example describes daily reports and a final consolidated report, with destination, check and operator information.

Sources: chapter 12, “Reports,” `OEBPS/c4KU.xhtml`, lines 68–71; chapter 10, Figure 10.3 caption and “Maintain Your Logs,” `OEBPS/c3RC.xhtml`, lines 25–32.

My adaptation: keep a few printed log sheets or a pocket notebook available. Write the date, camera, roll and recording reference before the note. At ingest, photograph/scan the sheet, transcribe useful entries into the canonical shoot log and mark that reconciliation complete. Preserve the original note with the daily reports. A notebook note should not quietly become a competing version of the digital log.

The guide currently proposes typed or voice notes. The book adds a practical fallback and a route for getting those notes to the editor. The choice is about speed under actual shooting conditions. It is not evidence that current digital reporting tools are poor.

### Review before the location becomes unavailable

Brown ties visual review to the opportunity to act: discovering a fault while the crew is still there can make a replacement shot possible. His dailies history includes the rule that sets remained standing until review.

Sources: chapter 10, “Always Scrub,” `OEBPS/c3RC.xhtml`, lines 48–51; chapter 11, “Dailies,” `OEBPS/c42H.xhtml`, lines 188–196.

My adaptation: add a brief location-release check for irreplaceable material: verify that the essential action exists, check its picture and sound, and review the pickup list before leaving. This expands the existing QC and pickup notes into a useful scheduling checkpoint. It is not a guarantee that a quick review finds every defect, and it should not replace the agreed copy/release checks.

## Details that reinforce the current multi-camera example

- Separate sound can cover both cameras. Figure 10.15's caption says common audio belongs outside an individual camera's folder when both cameras share the recording; separately operating units require a distinct association. This supports the existing sibling `SOUND/S002` folder and sequence linking. Source: chapter 10, `OEBPS/c3RC.xhtml`, lines 105–107. The actual folder diagram was not visually inspected.
- Slate identity includes camera, scene, take, frame rate, MOS and pickups. Chapter 12 explains a pickup take beginning partway into a scene, which differs from a later pickup shooting day. The guide already has pickups and missing-coverage notes; keep these two meanings explicit. Source: “What goes on a slate” and subsequent paragraph, `OEBPS/c4KU.xhtml`, lines 11–24.
- Check copied clips against camera reports. Efsic's description includes this reconciliation alongside verified downloads. This reinforces the existing expected-roll inventory check and suggests preserving any camera reports with it. Source: chapter 11, “Loader,” `OEBPS/c42H.xhtml`, lines 11–15.
- Sync checks should respond to events. Greenspan mentions power loss and off-speed work, plus downloader spot-checks for drift. The guide already has these precautions. His exact twice-daily jamming schedule is a practitioner's example, not a universal interval. Source: chapter 12, “Slating on the Set,” `OEBPS/c4KU.xhtml`, lines 30–33.
- Confirm deliverables with the receiving editor before shooting. The book repeatedly includes metadata, naming, connector compatibility and color treatment in that conversation. The guide already goes further by requiring an actual round trip. Sources: chapter 10, “File Naming,” lines 86–87; chapter 11, “The Meeting,” lines 141–145 and “Files for Post and VFX,” lines 197–199; chapter 12, lines 148–149.

## Advice to qualify rather than import

The existing guide already corrects several oversimplifications in these chapters.

| Book passage | Treatment in this guide |
|---|---|
| Chapter 10, lines 48–50, calls a visual check the way to be certain footage is good. | State review coverage and its limits. A quick scrub may miss a damaged frame, short dropout or end-of-take sync drift. |
| Chapter 10, lines 144–145, presents RAID as built-in backup and suggests continued operation after drive failure without specifying the level. | Retain the guide's independent-copy requirement. RAID behavior depends on configuration and is insufficient protection from deletion or shared enclosure loss. |
| Chapter 10, lines 71–76, says all professional ingest software includes CRC and discusses MD5 as a fingerprint. | Use the actual application's verification algorithm and settings. Avoid implying every verifier uses CRC or that a checksum provides an absolute authenticity guarantee. |
| Chapter 10, line 169, gives a universal-looking annual magnetic-data loss rate. | Do not repeat this unsupported numeric generalization. Keep preservation checks, independent copies and future readability as planning topics. |
| Chapter 12, lines 40–46, describes timecode as unique. | Keep camera/roll/path identity. Timecode repeats and needs a rate/convention; it is not a globally unique clip key. |
| Chapter 12, lines 53 and 58–64, generalizes HDMI timecode and frame-rate choices. | Do not use these as current device advice. The listed `29.7` is inconsistent with the following `29.97` bullet, and “any consistent rate” is too loose for a real capture/editorial pipeline. |
| Chapter 11, lines 269–338, describes early ACES and broad scene-referred claims. | Use the distinction between source interpretation, creative look and output rendering; verify any actual modern configuration separately. Do not copy its historical ACES menu/settings language or imply scene-referred always means numerically linear. |
| Chapters 9–11 include older recorders, interfaces, storage generations and formal crew classifications. | Treat them as 2015 examples. They do not establish current products, staffing rules, costs or Mac compatibility. |

Brown occasionally dismisses data-only work in ways that add nothing to the user's decision, notably chapter 10 lines 111–113 and chapter 11 line 106. The useful distinction is the workload and expertise required by each task. Careful data handling remains consequential even when the production needs no live grading.

The original EPUB and extraction provenance are recorded in `research/book/provenance.json`. All recommendations above are proposals for the guide; no source media, camera settings or application configuration was changed.
