# Primary documentation

Sources checked on 2026-10-28. The recommendations below apply the documented behavior to a small crew; the proposed folder convention and card-release policy require agreement with production and post.

## Camera originals and annotations

WITNESS recommends retaining camera-generated filenames because they preserve context and may be required by complex formats. Separate source folders resolve duplicate names. Its folder guidance keeps media and documentation together. [Filename guidance](https://archiving.witness.org/archive-guide/organize/filenames/), [folder guidance](https://archiving.witness.org/archive-guide/organize/folders-and-directories/).

Silverstack keeps editable scene/shot/take and other annotations in its library while leaving originals and backups unchanged. Deliver metadata exports and retain the library backup so editorial can use those annotations. [Silverstack library](https://kb.pomfort.com/silverstack/hands-on/editing-metadata/the-silverstack-library/).

For this guide, copy a complete card into a unique outer folder identified by shoot date, unit/camera and roll. Preserve native contents, filenames, sidecars and relative paths. Record the reusable physical card separately from the recorded roll. Check the camera manual for spanned clips or special offload requirements. The exact folder syntax is a production choice.

## Verification results

Silverstack records Verified, Defect and Not Verified for each source/destination resource. Destination verification compares a hash with the reference recorded during the copy; optional source verification rereads the source for another comparison. The documentation shows that one verified destination can coexist with another that remains unverified. [Verification states](https://kb.pomfort.com/silverstack/reference/library/verification-states/).

Require a successful result for every required destination, retain the reports, and reconcile expected files, counts and bytes. Playback/QC checks the recording itself. Matching hashes establish consistency with the reference, while missing rolls and defects already present in the source require inventory and media inspection.

## ASC MHL

ASC MITC's XML specification records media hashes, essential file metadata and copy history. Its official repository distinguishes ASC MHL from the earlier MHL format. Version 1 requires a new manifest for each copy in the custody chain. [Specification repository](https://github.com/ascmitc/mhl-specification), [version 1 specification](https://cdn.theasc.com/ASCMHL_Specification_v1.0.pdf?mtime=20220316130804).

Keep manifests with their data in the required layout. Sender and receiver need compatible algorithms and manifest formats, and the receiver should verify against the agreed reference. A generic checksum text file is not necessarily an ASC MHL manifest. Independent copies remain necessary, including when storage uses RAID. Scene/take and sync annotations need their own metadata records.

## Editorial matching fields

Pomfort's Avid workflow requires the ALE tape value to match the value embedded in MXF dailies. A mismatch can prevent merging or relinking. The legacy workflow also describes matching by timecode with filename or tape name. [Silverstack Lab Avid workflow](https://kb.pomfort.com/silverstack/hands-on/creating-dailies/export-to-avid-media-composer/), [workflow PDF](https://pomfort.com/support/Pomfort_Metadata_workflow_AVID_Media_Composer.pdf).

Silverstack's exporters include CSV, FCPXML, Premiere XML, Avid ALE and Resolve metadata. Premiere reel mapping can draw from different source fields and becomes Premiere's Tape Name; Resolve CSV also has configurable reel naming. [Exporter reference](https://kb.pomfort.com/silverstack/reference/importandexport/exporters/).

Before shooting, deliver a camera-plus-sound test, proxy, metadata export and look to editorial. Test import, sync, field values and reconnection to originals. Record the receiver's matching fields. Burn-ins help people identify clips, while embedded metadata supports application matching.

## Proxy compatibility

Adobe documents attaching externally generated proxies and returning to originals, including limitations around Modify Audio Channels and Interpret Footage. Its reference manual requires compatible frame rate, duration, fielding and audio-channel configuration; supported frame-size differences are allowed. [Premiere ingest/proxy guide](https://helpx.adobe.com/premiere/desktop/organize-media/ingest-proxy-workflow/ingest-and-proxy-workflow.html), [reference manual](https://helpx.adobe.com/pdf/premiere_pro_reference.pdf).

Agree codec/container, dimensions, audio layout, source timecode, reel identity, naming and color treatment with editorial. Keep generated proxy/review media outside preserved card folders. Synced dailies and attachable camera proxies may need different specifications. Include off-speed, VFR and multichannel examples in the preproduction test.

## Sound metadata

Broadcast Wave adds a metadata chunk to WAV. Its time reference is a 64-bit count of samples since midnight, interpreted with the file's sample frequency. [EBU Tech 3285](https://tech.ebu.ch/docs/tech/tech3285.pdf), [FADGI BEXT definitions](https://www.digitizationguidelines.gov/audio-visual/documents/btext.html).

Sound Devices recommends agreeing sample rate and timecode frame rate with production/post in writing. Its article includes legacy film/NTSC examples, so confirm the rates required for the actual job. [Production sound rate guidance](https://support.sounddevices.com/hc/en-us/articles/44141303483419-Sample-Rate-and-Frame-Rate-Settings-for-Production-Sound).

Sound Devices recorder documentation exposes scene, take, notes, track names, circle status, timecode, user bits, roll/folder and sample rate. Wave Agent reports can include filename, scene/take, tape, channels, sample/frame rate, bit depth, start/end timecode, duration, notes, wild-track, circle and track information, in PDF or CSV. [888 manual](https://cdn.sounddevices.com/wp-content/uploads/2024/05/888-v10.01-User-Guide.pdf), [Wave Agent manual](https://cdn.sounddevices.com/wp-content/uploads/2019/04/waveagent_en.pdf).

Agree scene/take spelling across sound and script. Retain BWF/poly-WAV originals and reports, label tracks, and record wild/MOS/off-speed exceptions. Cross-check sync against a slate. The 833 documentation distinguishes a folder rename from embedded sound-roll metadata, so check both when investigating a mismatch. [833 documentation](https://guides.sounddevices.com/833/).

## Recommended records

| Record | Fields |
|---|---|
| Roll/offload | Production, shoot date/day, unit/camera, unique roll ID, physical card ID, source volume, operator, receipt time, file count, bytes, first/last clip, every destination drive/path, hash algorithm, verification result, report/manifest path, exception, release approver/time |
| Clip log | Original path/name, camera/roll, scene/shot/take, source start TC and rate, duration, capture/playback rate when different, resolution/codec, sound roll/file and sync method, track labels, circle/rating, QC notes, look ID/version, proxy path |
| Handoff | Included roll inventory, originals/sound/proxies/reports/looks, manifest format, metadata mapping, missing or quarantined items, receiver, receipt and verification acknowledgement |

Extract technical fields from camera/sound metadata where possible and add production context manually. Keep unknown values distinct from zero, false or an affirmative QC result.

## Follow-up search terms

| Query | Subject |
|---|---|
| `DIT checksum verification ASC MHL workflow` | Integrity and receiver verification |
| `Silverstack scene take metadata ALE Avid` | Exporting annotations to editorial |
| `small crew camera card offload sound report handoff` | Card custody and staffing |
| `DaVinci Resolve proxy reel name timecode relink` | Clip identity and conform |
| `production sound BWF iXML timecode metadata` | Sound metadata |

## Research limits

These documents describe formats, product behavior and professional guidance. They establish neither a universal small-crew folder tree nor a mandatory copy count before card reuse. The guide labels those choices as recommendations.

Netflix's former Production Assets: Data Management article redirected to a JavaScript-only Knowledge Hub page during retrieval. Its current detailed requirements were not read. Older vendor reproductions therefore cannot establish current Netflix policy for this guide.

Version-specific behavior needs testing with the production's actual camera, storage and NLE. Documentation alone cannot verify the downloaded videos' advice or prove a successful end-to-end handoff.
