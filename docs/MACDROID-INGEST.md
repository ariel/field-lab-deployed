# USB cameras through MacDroid

Some cameras expose media through MTP/Image Capture rather than a Finder disk. MacDroid can make that media accessible as a filesystem folder, which OffShoot can select as a source. This is an optional source adapter, not a replacement for OffShoot or a new AI ingest path.

**Camera → MacDroid folder → OffShoot verified destination → existing AI queue → CCC (if separately configured).**

## What has been exercised

On 2026-11-07, MacDroid showed a connected MISSION 1 PRO in MTP mode. Its native Finder integration exposed a folder under `~/Library/CloudStorage/`, containing an MP4, LRV, THM and camera metadata. OffShoot accepted the enclosing camera-storage folder under Sources and enumerated approximately 2.8 MB. No destination was selected and no transfer was started. **Folder selection/enumeration passed; copying, verification, callback receipt and AI processing through this adapter remain untested.**

A Skydio X10 had previously been browsed in Image Capture without a mounted disk. That listing contained only four WAVs and two small system files, not flight video/photos. MacDroid compatibility with the X10 and access to its actual flight media remain untested. Do not infer X10 acceptance from the GoPro result.

## Setup and use

1. If the operator chooses MacDroid, install it from its official vendor site and handle its license separately. Field Lab does not bundle, purchase, install or configure it automatically. Keep Image Capture and other MTP clients closed while MacDroid owns the connection; do not indiscriminately kill unrelated device sessions.
2. Connect and mount the camera in MacDroid, then use **Show in Finder**. Inspect the actual exposed storage and confirm the expected footage is present. A device name alone does not establish the camera, card or completeness of its contents.
3. In OffShoot's Disks screen, double-click the empty Sources area to open the folder picker. Navigate through the MacDroid sidebar location and select the actual camera-storage folder. Do not select a Photos alias or just the MP4: retain companion files and the exposed directory hierarchy. Do not hard-code a developer's CloudStorage path, serial number or device name.
4. Confirm OffShoot shows the source and plausible content size. Select the usual configured, UUID-checked physical ingest destination and verified-ingest preset. Apply an operator-chosen camera/roll label as with a card. MacDroid is a source only: do not configure its CloudStorage folder as Field Lab's ingest/backup destination or place `_DIT_NOTES` there.
5. Keep MacDroid running and the camera connected during transfer. OffShoot's normal successful-receipt gate remains required before AI enqueueing. Do not bypass it or index the on-demand camera folder directly. CCC, when configured, reads the verified destination and its AI sidecars, not the MacDroid source.

## Caching and verification

The observed native integration used CloudStorage placeholders: the MP4 had a logical size but zero allocated data blocks before reading. Opening/copying these files can download them into a local cache. Allow enough free space for hydration in addition to the destination copy; do not assume direct streaming or a configurable cache location for native-drive mode.

OffShoot verifies the bytes presented by MacDroid. Its subsequent source read may come from that cache; a successful Source & Destination result does **not** establish an independent second read of the camera's original storage. Describe this as verification against the MacDroid-presented source, not proven device-level rereading. Retain camera originals until independent backup and media QC are complete and the operator authorizes reuse.

If OffShoot cannot select/read the adapter, use a completed local staging download as its folder source. Keep incomplete downloads separate; only hand off a finished, inventoried folder. The staging hop has its own verification limitation. This release adds no automatic MTP importer, staging watcher or new transfer receipts.

## Acceptance before field use

Use a small disposable recording owned by the operator. Record the camera/firmware, macOS, MacDroid version/mount mode, OffShoot version, observed file inventory and actual results locally. Do not commit private paths, serials or footage.

- Confirm expected video and companions, folder selection, a full OffShoot copy with Source & Destination verification, a supported successful receipt, exactly one AI queue job, playable destination media and browsable AI output. Check the exposed source inventory again for omissions; successful enumeration alone is insufficient.
- In a separate disposable transfer, disconnect the camera or stop MacDroid before all uncached media has downloaded. Confirm failure/incompletion cannot produce a successful AI enqueue. Reconnect, inspect/retry through OffShoot and confirm successful recovery without missing files or duplicate completed AI jobs. A cached transfer may continue after unplugging; that demonstrates caching, not a fresh camera read.
- Test a second session/reconnection: rediscover the actual source folder and verify the selected destination again. Do not depend on a source arrival Disk Added event; the observed native adapter was not a separate `/Volumes` mount.
- Keep existing physical-card acceptance results separate. Until these adapter checks pass on the actual camera/laptop, report MacDroid ingestion as provisional. Do not erase device media as part of testing.

## Sources

- [OffShoot sources and folder selection](https://docs.hedge.video/offshoot/overview)
- [MacDroid MTP connection and competing clients](https://www.macdroid.app/faq/connect-and-mount-android-device-using-mtp/)
- [MacDroid native-drive and cache preferences](https://www.macdroid.app/faq/macdroid-preferences/)
- [Skydio X10 transfer instructions for Mac](https://support.skydio.com/hc/en-us/articles/20768299014683-How-to-transfer-media-from-Skydio-X10)
