# Operator metadata durability

Canonical storage is the project's `_DIT_NOTES/project.sqlite3`, with SQLite WAL/SHM companions while connections are open. Browser state and generated search catalogs are not the authority for names, notes, identity corrections or explicit face-to-voice links. No second writable JSON authority was introduced.

The hardened store requests WAL, synchronous=FULL, fullfsync=ON and checkpoint_fullfsync=ON for each connection. Operator mutations, their audit entry and edit revision commit together in BEGIN IMMEDIATE transactions. The containing directory is synced before an operation returns and after connection close, including initial database/WAL directory-entry creation and removal. Schema-only executescript calls are separate from the explicit serialized project-ID/revision initialization transaction. Voice split ownership validation now occurs inside its mutation transaction.

Legacy metadata migration uses SQLite's backup API, closes both connections, syncs the new file, and publishes with atomic no-replace linking. A concurrent canonical database or first saved edit always wins; migration never replaces it. Existing canonical user data was never replaced or edited by the validation tests.

Fixture tests: `test_durability.py`, log `fault-tests.log`.

- Eight operations survive SIGKILL after the committed method returns while its WAL connection remains open: voice name, face name, explicit link/unlink, note/tag update, accepted inheritance, voice merge and face merge.
- The same eight operations roll back completely when killed after mutation but before audit, and again after audit/revision but before commit:24 subprocess fault cases in total. Integrity and foreign-key checks pass after recovery.
- Eight concurrent first-open connections converge on one project ID; requested PRAGMAs and directory-sync calls are verified.
- SQLite backup includes committed WAL edits. A forced race with a new canonical saved edit proves legacy migration cannot overwrite it.
- An index build held on an older SQLite read snapshot does not erase a newer saved name/note. Its indexed revision stays behind; the next build includes the new edits and closes the revision gap.

Five tests passed in6.399seconds. No MLX/model calls or real-project mutations occur in this suite. Independent replay of all eight actual sealed analysis results into a SQLite-backup clone preserved the real user edit revision, names and explicit link exactly; see `operator-replay-evidence.json` from the performance buddy.

Analysis profile remains `56d9aa54e27c8b1d9d80`; these storage changes do not trigger new transcription or visual analysis.

These are process-crash/recovery tests and requested filesystem synchronization guarantees, not a physical power-cut or storage-failure certification. A backup of a live SQLite database must use SQLite's backup API or an appropriately coordinated snapshot; copying only the main `.sqlite3` file can omit committed WAL changes. Root owns the controlled daemon restart and final verification that current user edits remain present.

## Upstream SQLite issue found and addressed

Official SQLite documentation identifies a rare concurrent WAL writer/checkpoint corruption bug in versions through3.51.2, fixed in3.51.3 and specific backports3.50.7/3.44.6: https://www.sqlite.org/wal.html#walreset. The original bundled interpreter used SQLite3.50.4. Synchronization settings and ordinary crash tests alone cannot eliminate that upstream race.

A clean official Astral python-build-standalone20261026 candidate uses CPython3.12.16 with SQLite3.53.1. Its archive SHA-256 `fbf4afef53c2a6b72bb741bc06d5671a9dfaf87bd84e5aa73ac9b3d0d589f14e` matches the official GitHub asset digest. Existing3.12 packages are reused; critical native imports pass. Three extra probed optional modules were absent from both old and candidate environments, rather than ABI failures. Candidate offline readiness is true and the analysis profile remains unchanged.

The expanded six-test suite (including pure version policy) passed under the candidate, and passed independently again. A shared preflight rejects affected SQLite versions before operator-store or queue access and reports the requirement in offline readiness. It uses the same stdlib engine throughout; no alternative SQLite wrapper or dual database authority was introduced.

Candidate assets/provenance, import results and independent verification are under python-candidate/. Root owns the stopped-service runtime promotion and final live-edit preservation check.
