Unified UI/API regression commands:

- `python3 tests/test_metadata_api.py -q` (4 HTTP tests, fake inference backend; CPU only).
- `cd viewer && npm test` (16 tests, actual native Orama plus worker/prebuilt/quality tests).
- `cd viewer && npm run build` (React production bundle).

/api/catalog returns the sealed catalog unchanged. /api/annotations-state shows
durable edits immediately and exposes edit/indexed revisions. A coalescing worker
resumes any persistent revision gap through enrichment.publish_index, using the
same serialized MLX backend and atomic catalog/vector publisher. The React app
polls sealed publication and metadata every3 seconds. It never builds from a live
SQLite projection mixed with an older sealed vector snapshot.

Voices and faces are separate evidence. People panel lets the operator name IDs,
link/unlink a face to a voice explicitly, and merge same-modality model candidates
with explicit name-conflict handling. Conflicting simultaneous identities are
rejected by shared store safeguards. Notes panel edits text/tags and accepts or
rejects CLIP-derived metadata suggestions with provenance. Names/tags live in the
same native Orama indexes; exact complete human labels cannot be vetoed by a
poor semantic reranking score. AI-only guesses retain existing quality cutoffs.
