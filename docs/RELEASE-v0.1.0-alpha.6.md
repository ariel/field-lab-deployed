# v0.1.0-alpha.6 — optional MacDroid camera sources

Documentation-only update to alpha.5. Adds the optional MTP camera → MacDroid folder → OffShoot → existing AI queue → separately configured CCC procedure, linked from the README, operations guide, install/update prompts, deployment skill and smoke test.

Observed on the development Mac: MISSION 1 PRO was mounted in MacDroid, and OffShoot accepted/enumerated its approximately 2.8 MB camera-storage folder. No transfer was started. A full copy/verification, receipt, AI enqueue and interrupted uncached-download test remain required. Skydio X10 support through MacDroid remains untested; its earlier Image Capture listing did not expose flight media.

MacDroid's observed native CloudStorage integration uses on-demand files. OffShoot verification establishes agreement with the adapter-presented bytes; it does not establish a fresh independent reread of camera storage. The procedure retains companion files, physical destination UUID checks, normal receipt gating, independent backup/QC and operator release of source media.

No application code, model pins, analysis profiles, database schema, hooks, OffShoot settings or CCC settings change. No reindex is needed. MacDroid is optional, separately installed/licensed, and not installed by Field Lab. Existing installations can read the new procedure without activating a new runtime; updating the source/skill delivers the guidance. Normal software updates must preserve existing adapter configuration.

Validation: skill structure validation, documentation link/whitespace checks and three source-distribution tests passed locally. Release publication also checks the existing GitHub CI suite. These checks do not validate a physical MacDroid transfer or X10 compatibility.

See [MacDroid setup and acceptance](MACDROID-INGEST.md). Existing runtime behavior and validation are inherited from alpha.5; this release adds no stronger device-support claim.
