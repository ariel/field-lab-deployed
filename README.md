# Field Lab

Offline media indexing for a filmmaker doing camera and data wrangling alone.

**OffShoot Pro → verified media drive → local AI indexer → CCC backup drive.**

OffShoot retains complete cards and verifies each copy. Field Lab queues verified ingests and adds full timestamped transcripts, brief visual notes, searchable stills, face/voice grouping and operator notes. A local browser provides search, identity review and chat with links to footage. Originals stay untouched; generated output and durable operator edits live in each project's `_DIT_NOTES` folder.

Parakeet, Qwen, embeddings and reranking run locally using MLX; face detection/embedding uses OpenCV. Text and image retrieval share the Orama architecture. No cloud inference key is required. Model weights are downloaded from pinned upstream revisions and checked; **no footage, weights, saved chats, identities or project metadata are included here**. Third-party model and dependency licenses remain their own.

This is an early deployment release. Supported target: **Apple Silicon, macOS 27+, Xcode Command Line Tools**, OffShoot Pro 26.3+. First installation requires internet and enough space for models, caches, dependencies and source builds; allow at least 25 GB free. Older operating systems have not been validated. OffShoot/CCC licenses are purchased separately. CCC is configured separately after explicitly choosing the second drive.

## Install with Codex

Clone this repository into a working folder, open that folder in Codex, and ask:

> Use the `$field-lab` skill in `.agents/skills/field-lab/SKILL.md` to install this workflow. Follow `docs/prompts/FIRST-INSTALL.md` and inspect this machine before choosing configuration.

The [install prompt](docs/prompts/FIRST-INSTALL.md), [update prompt](docs/prompts/FIELD-UPDATE.md), and [operations guide](docs/OPERATIONS.md) provide commands and recovery steps. The skill lives in the repository; no global skill installation is required when the checkout is the Codex project.

For a reviewed source checkout:

```sh
bash deploy/bootstrap.sh install
```

This prepares a candidate and prints its release ID. Activation, machine/drive configuration and OffShoot setup follow the operations guide. No application settings change merely from cloning or preparing. Field updates use a selected tag/commit, isolated preparation, integrity checks, a quiet-time switch and a previous release for rollback. Pending AI work resumes by reconciliation.

Do the [smoke test](docs/SMOKE-TEST.md) on your own disposable footage and a test card before field use. A successful readiness check verifies assets, not every camera codec, macOS permission or physical transfer. AI search covers sampled stills and can miss appearances. Keep cards until the required independent backup and media checks pass.

## Development

Application source is in `ditnotes/`, `search/`, `viewer/` and `native-progress/`. Deployment scripts are in `deploy/`. See [CONTRIBUTING.md](CONTRIBUTING.md). Earlier research and experiments are retained under `docs/research/` and `development/` as historical context; their old paths and benchmark results are not installation defaults or portable certification.

Source code is MIT licensed. See [THIRD-PARTY.md](THIRD-PARTY.md) for downloaded components and model provenance.
