# OffShoot automation audit

Reviewed 2026-11-05 against the current vendor documentation and this repository's scripts. The operator confirmed the field machine will use the same OffShoot Pro version as development. This review does not stand in for its first physical transfer test.

## Reading coverage

Read the full Scripting page requested by the operator, every event page, the Event Log page, the complete Automation section including API, Helper and all example-script pages, the directly linked support page, and verification/logging/organization/labels/elements used by our integration: **38 documentation pages**. The vendor's `llms.txt` supplied the section inventory, including Source Added and the separate Disks Idle page that the Scripting page's duplicated Disk Idle link misses. See [machine-readable coverage](offshoot-reading-coverage.json) for every URL, byte count and content hash.

Also downloaded **19 example assets** and read/decompiled **22 contained source/configuration files**, including both linked Watch Folder versions and the Pro preset example. The app-bundled and standalone transfer-report scripts were confirmed byte-identical after decompilation before reading once. Assets were only inspected; none was run or installed. Their page URLs, download hashes and source-file names are recorded in the coverage file. Full vendor pages/scripts are not redistributed here.

Scope is OffShoot's automation documentation and its workflow-relevant links, not the entire Hedge product family. Account/license pages, marketing, image-only links, unrelated third-party integration sites and malformed legacy draft links do not expand this into an unrestricted site crawl. Old event links in examples were resolved to the current event page. GitBook's generated agent-query instructions are documentation-platform boilerplate, not operator instructions. Original downloaded evidence stays in the development audit scratch directory rather than a deployed dataset.

## Event and callback contract

Scripting requires Pro. Direct Python scripts receive a JSON string argument but depend on `python3` in the app's environment. AppleScript is macOS-specific and supports parameter replacement. Our short AppleScript callbacks invoke the managed launcher/interpreter explicitly, avoiding reliance on a global Python install. They deliberately do not interpolate event strings into executable code. [Scripting](https://docs.hedge.video/offshoot/features/automation/scripts).

OffShoot Started fires once per app launch and is suitable for waking reconciliation. File Copy Completed is per transfer/destination and also fires on failure, warnings, cancellation and stop. Two copy destinations generate separate completion events. Its current example includes a transfer ID and JSON-log path; those are useful evidence locators, not a reason to assume success. [Started](https://docs.hedge.video/offshoot/features/automation/scripts/events/offshoot-started), [File Copy Completed](https://docs.hedge.video/offshoot/features/automation/scripts/events/filecopycompleted).

Disk Idle means no transfer on that disk remains queued/running. Disks Idle concerns all disks. Neither means the AI indexer has finished. Disk Added includes virtual and network mounts, so a volume name or arrival event is not trustworthy camera identity or backup-destination identity. [Disk Idle](https://docs.hedge.video/offshoot/features/automation/scripts/events/disk-idle), [Disks Idle](https://docs.hedge.video/offshoot/features/automation/scripts/events/disks-idle), [Disk Added](https://docs.hedge.video/offshoot/features/automation/scripts/events/disk-added).

Our completion callback only wakes receipt recovery. `offshoot_receipts.py` requires the observed supported JSON schema, success with no reason, source-and-destination verification, and every listed asset verified. `ingest_events.py` checks the actual destination hierarchy, mount and volume UUID before enqueueing. Unknown receipt formats do not authorize work. The JSON schema adapter is based on observed version-1.1 receipts, not a vendor guarantee that every future receipt will use that layout. A future schema needs a new fixture and adapter test.

## API, preferences and preset findings

The supported `offshoot://` API can set source/destination, reset dropzones, reload presets and set preferences. API JSON/path parameters must be URL-encoded. The macOS response log is a single-line file that is cleared between requests; empty content is not a rejection and must be polled until a bounded result. Chained calls can have timing issues, so our setup sends and acknowledges sequential requests. [API](https://docs.hedge.video/offshoot/features/automation/api).

The audit found and prompted these implementation corrections:

- **Acknowledgement race:** `setup_workflow.api()` previously treated a newly emptied response log as immediate failure. It now waits through empty content for the result.
- **Log-location drift:** the Logging page names `Application Support/Hedge/Transfer Logs`, while the newer completion-event example uses `Application Support/OffShoot/Transfer Logs`. Recovery now scans both, plus retained portable receipts, with the same strict validation. [Logging](https://docs.hedge.video/offshoot/features/logging).
- **Remembered destination risk:** the installed app's `SFIDefaults.plist` enables automatic destination recognition by default. Setup now disables automatic destinations and both automatic-source modes. The operator selects the card; a later app restart must not silently add another remembered destination.
- **Stable callbacks:** hooks live in application shared runtime and call the stable `home/run` launcher. A software update changes the release pointer, not the hook paths.
- **Machine configuration:** setup derives paths from this machine's chosen destination/UUID. It supports the configured relative ingest folder rather than a hardcoded development mount or `Ingests` prefix.
- **Counter preservation:** setup takes the existing app/preset counters and existing ingest suffixes into account. A new or reorganized disk must not reset the next roll to the example's initial counter.
- **Backup and interruption:** setup exports current preferences and saves the replaced preset before API changes; compiled hooks are staged before replacement. A failure can leave a partly applied app configuration, so inspect the saved setup plan and visible settings, then retry or deliberately restore. Do not declare configuration successful after only the first API call.

The app's documented preference-key inventory is `/Applications/OffShoot.app/Contents/Resources/SFIDefaults.plist`; inspect the actual bundle and read back affected settings when validating another installation. The field setup must observe an idle app, not infer idle merely because its API can reset a dropzone. Resetting dropzones does not cancel existing transfers.

`.hedge` presets are supported editable/shareable files and can be reloaded via the API. Our whole-card preset leaves filenames/hierarchy intact: no selective extension filter, no flattening, no source renaming and no ignored empty folders. Source-name plus counter creates a distinct wrapper. [Organization](https://docs.hedge.video/offshoot/features/organization).

Labels do not rename the camera card's volume. They can contain slashes, which create further directories; the visible destination preview is therefore part of acceptance. Automatic labels/counters may update as sources are added or changed. Review the actual next destination rather than assuming a prior screenshot is still authoritative. [Labels](https://docs.hedge.video/offshoot/features/labels).

Custom metadata elements are recorded in logs/MHLs and can drive paths. Pro presets can supply source/clip review fields. They are available when useful, but our default does not add forms or a seeded project/people dataset to a solo operator's ingest. Narrative notes stay in the local library. [Elements](https://docs.hedge.video/offshoot/features/elements).

## Verification and source release

The vendor distinguishes Transfer, Source and Source & Destination modes. The selected workflow requires the last mode; its result is still checked for warnings. Source & Destination independently reads/verifies source and destination data, subject to documented MHL awareness. Neither a green callback nor AI completion proves two independent copies or playable media. Retain cards until verified copies, QC and the operator's release decision. [Verification](https://docs.hedge.video/offshoot/features/verification).

An Event Log is useful for callback execution/returned results, but is capped at 1000 lines. Durable retained transfer receipts and queue records are the recovery mechanism, not an assumption that the event log retains the entire shoot. Command-Shift-L opens that log; Command-L opens transfer logs. [Event Log](https://docs.hedge.video/offshoot/features/automation/scripts/event-log), [support log collection](https://docs.hedge.video/offshoot/need-help).

## What we do not import from vendor examples

The examples demonstrate mechanisms, not ready-made policies for this workflow:

- Helper workspaces can reset all preferences and run arbitrary commands. We keep our narrower versioned setup; no Helper login item or global reset is installed. [Helper](https://docs.hedge.video/offshoot/features/automation/offshoot-helper).
- Swap Presets moves all existing presets into an archive. Our setup preserves unrelated presets. [Preset swapping](https://docs.hedge.video/offshoot/features/automation/offshoot-helper/set-destinations-and-swap-presets).
- Auto-start examples match loose volume-name fragments and use legacy keys/timing. We retain explicit card selection and verified mounted destination identity. [Auto-start transfers](https://docs.hedge.video/offshoot/features/automation/examples/automated-transfers).
- The Finder-tag example labels sources at Transfers Added, before verified completion. We do not use that as an “ingested” or card-release gate. [Finder tags](https://docs.hedge.video/offshoot/features/automation/examples/set-finder-tags).
- Watch Folders has documented limitations, including simultaneous additions and existing subfolders. It is not a substitute for our receipt-backed queue/reconciliation. [Watch Folders](https://docs.hedge.video/offshoot/features/automation/examples/watch-folders).
- Deleting MHLs, moving camera files for ZCAM, sending mail/Slack, and starting a cascading copy are separate actions. None is installed by this workflow. The cascading example specifically excludes Organize support, which our date/card hierarchy uses. [Cascading copy](https://docs.hedge.video/offshoot/features/automation/examples/cascading-copy).

## Acceptance on the recipient Mac

Optional MTP/Image Capture camera sources can be presented as folders by MacDroid; see [setup, evidence and verification limits](MACDROID-INGEST.md). Use the same successful-receipt gate. Native CloudStorage folder arrival is not a guaranteed Disk Added event, and source verification through an adapter does not prove a fresh read from device storage. No MTP automation is installed by this integration.

Show the configured source/destination, preset, counter, verification and callback settings. Perform a disposable verified transfer and check both transfer receipt and Event Log execution. Confirm a duplicate receipt yields one durable job; failed/warning/stopped and unsupported-schema fixtures must yield none. Interrupt AI on disposable footage, restart and confirm reconciliation. Confirm remounting a different disk with the same name is rejected by UUID. Confirm an OffShoot restart retains exactly the intended destination and does not start a transfer automatically. These checks supplement, rather than replace, `docs/SMOKE-TEST.md` and the separately chosen [CCC task acceptance](CCC-SETUP.md).
