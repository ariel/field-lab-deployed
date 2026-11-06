# Shared project contract

This lab does not change the OffShoot trial runtime.

- Immutable `content_id` is the original file SHA-256. Paths are aliases, not identity.
- Audio/visual observations are regenerable timed evidence. Operator annotations, names, merges and corrections are durable edits in one project SQLite store.
- Every speaker embedding has a revision, frontend profile and dimension namespace. Its cosine is never compared with text384 or CLIP512 embeddings.
- Voice matching enrolls a few clean, non-overlapping speech crops. Low-quality speech does not update centroids. Auto-assignment remains disabled until model-specific open-set threshold and margin are calibrated.
- Person UUIDs identify project speaker entities, not verified real-world identities. Names come only from the operator. Ambiguous matches create separate provisional IDs and merge suggestions.
- Shared search projection feeds the existing Orama text/hybrid index and CLIP image index. Person IDs are facets; names and operator notes are searchable fields/documents. There is no second document retrieval engine.
- Similarity links are provenance-bearing suggestions. Inherited text is indexed only after explicit acceptance and cannot overwrite original operator annotations. Similarity and inheritance never establish identity.
- Atomic AI snapshot publication remains separate from the durable edit store. A new edit revision invalidates only affected search projections, not source media or all AI analysis.
- Audio supplied to the VLM is timestamp-windowed evidence, clearly marked as spoken context. It must not be treated as proof that a narrated object is visible.

## APIs

`ProjectStore(db_path, project_id=None)` owns speaker observations, entities, profiles, names, annotations, links and audit events. `assign_speaker` accepts clip-local diarization turns and revision-namespaced embeddings. `project_documents(catalog, store)` emits Orama-compatible records; `personIds` and `personNames` extend the existing record schema.

Use `auto_assign=False` until the performance buddy calibrates real cross-clip speaker fixtures. A quality value is a heuristic with recorded components, not a probability of identity.

## Face evidence

Face observations share the project SQLite lifecycle, atomic catalog projection,
operator audit and the existing native Orama text384/CLIP512 indexes. SFace128
identity vectors remain in model-revision-scoped registry profiles, never in text
or CLIP space. `faceIds`/`faceNames` are visible evidence; `speakerIds` are audible
evidence. A narrator is not presumed to be visible. `personIds` on visual records
only include an explicitly operator-linked face/voice association. Separate
entity IDs are retained, and unlinking restores that separation. Names alone
never establish identity. Unnamed faces start with UUIDs. Default auto matching
is disabled; lab transforms-only calibration does not establish field accuracy.

Derived face observations carry content ID, exact sampled timestamp, normalized
xyxy bbox, local frame/crop reference, detector/embedding model revision, quality
components and candidate match provenance. Low quality crops stay provisional
with no fake vector. Two detections in one frame cannot auto-collapse. Sealed
face analysis is independently recoverable; durable operator names, merges,
splits and links are not regenerated from model output.
