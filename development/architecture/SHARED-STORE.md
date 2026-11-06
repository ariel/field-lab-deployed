# Shared store and search projection

`lab_indexer/project_store.py` uses one project SQLite database with WAL and FULL synchronous commits. Voice observations, operator names, notes, link suggestions and audit events share this lifecycle. Each connection belongs to one thread; open one per request/worker.

`lab_indexer/search_projection.py` emits the existing file/visual/speech document IDs and adds operator-note documents. `search/orama_projection.mjs` uses the existing Orama text384 and CLIP512 schema, with speaker and source facets. Person names are searchable string-array fields in that same text index. There is no independent annotation or person document search engine.

Voice enrollment is a model-native project registry operation, not general retrieval. Revision/frontend profile and dimension must match. A revision cannot silently change width. Only sufficiently long, clean, non-overlapping evidence updates centroids, capped at three crops per local speaker. Auto-match is off until a model-specific threshold and top-two margin are calibrated. Short/noisy turns have honest null embeddings and stable provisional IDs. `record_turn` adds temporal coverage without manufacturing or repeatedly enrolling vectors.

Voice identity never establishes who is visible. File and transcript documents can carry voice-person facets. Visual documents receive no automatic person IDs from simultaneous narration. Names are operator-provided. Merges, splits and reassignments are audited.

The stretch feature uses internal `clip_summary` entries in the same native Orama CLIP512 index. Public image retrieval filters `recordKind=visual`, so these internal summaries do not appear as stills. `search/link-candidates.mjs` retrieves at most three native Orama candidates among annotated clips with the same CLIP/aggregation profile. The store verifies only this bounded set and creates suggestions. It does not scan a second nearest-neighbor corpus.

Suggestions snapshot source notes and metadata when offered. Acceptance is explicit, append-only, and retains source annotation, content, edit revision and model/cosine provenance. It never overwrites an original operator annotation, propagates person identity, or transfers a source clip's timestamps to another clip.

## Local metadata editor

```sh
<lab-python> metadata_server.py --project "/Volumes/ThunderBlade X8/AI Indexer Lab/projects/example"
```

Open the printed loopback URL (default 8768). The editor supports voice names, clip notes/tags, edits and suggestion acceptance/rejection. It projects edits to the same Orama text index immediately. With the default CPU-only mode it performs no model inference and does not touch the OffShoot trial. The lab pipeline's explicit `index` command builds semantic vectors for changed annotation documents; launching with `--index-on-edit` enables coalesced background semantic reindexing through the same lab pipeline. It is OFF by default for CPU-only smoke tests and while the OffShoot trial reserves the GPU. The SQLite edit/index revision gap survives interruption and triggers retry next session; the indexed marker advances only after a sealed matching-project snapshot verifies.

All entry-point output paths pass the shared lab guard. Production runtime, live Ingests, code, model and fixture directories cannot be selected as editable projects. The HTTP endpoint is loopback-only, rejects foreign origins, limits JSON bodies and serves only its static assets.

## Verification

CPU-only tests cover stable cross-clip IDs with explicit calibrated-policy fixtures, unknown/ambiguous handling, overlap constraints, model revision/width separation, enrollment caps, names/merge/split/restart, transactional rollback, durable notes, explicit inheritance snapshots and existing document-ID compatibility. Actual native Orama tests cover name/metadata retrieval and speaker facets in the same index, separated text/CLIP widths, bounded summary candidates and summary exclusion from public still results. HTTP smoke tests cover editing, projection, static assets, origin/path guards and invalid-edit rollback.

These tests establish consistency and behavior. They are not speaker-recognition accuracy measurements; the performance buddy owns actual voice/model quality and runtime qualification.

## Model qualification

The small LibriSpeech fixture supports a **lab-only** ECAPA matching policy of 0.70 cosine and 0.10 top-two margin, identified by its calibration artifact. This is not a production-certified identity threshold. The shared store keeps auto-assignment disabled unless explicitly enabled by a model-specific caller policy. The default 0.82 guard is intentionally conservative; do not mistake either value for a probability.

The Orama CLI uses a bundled official Node v24.11.0 (`bin/node`, source/hash in `search/node-runtime.json`) so a restricted field PATH does not silently skip metadata-link suggestions. No Homebrew Node or separate neighbor-search service is required.

Speaker overlap exclusions apply within an audio-stream domain. The same voice heard on two microphones at the same time can share an identity; two distinct overlapping voices inside one mixed stream are excluded from automatic merging. Diarization false positives without ASR support must not create global speaker entities; raw model turns remain inspectable separately.

An accepted inherited note is not eligible as the source of another automatic suggestion. This prevents a chain of increasingly ungrounded copies. Model upgrades require re-enrollment into the new voice space; names and IDs are not discarded or compared across incompatible embedding namespaces.

Face API: `assign_face(content_id,seconds,embedding_or_None,model_revision,quality,
bbox=...,frame_ref=...,crop_ref=...,detection_id=...,auto_assign=False)` returns
`observation_id`, `face_id`, status and candidates. `name_face`, `merge_faces`,
`split_face`, `link_face_voice(face_id,person_id,reason)` and `unlink_face_voice`
are audited operator edits. `/api/face/name|link|unlink|merge|split` expose the
same store. The Faces editor shows sampled crops and requires an explicit Link
to speaker action. Local crop serving is allowlisted and confined under notes.
Face records are nonembedding documents in the existing Orama projection, with
face name/facet retrieval tested separately from speaker filters.
