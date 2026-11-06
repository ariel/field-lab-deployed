# Isolated feature performance results

These features are not installed in the OffShoot trial. All test outputs and environments are under AI Indexer Lab.

## Full trailer processing

All three source containers have different SHA-256 values but identical encoded video/audio stream hashes, so analysis and indexing cannot use previous content-identity results. A single Pipeline instance retains models between runs.

| Run | Wall time | Footage ratio | 0.25 gate |
|---|---:|---:|---|
| cold 1 | 30.656 s | 0.295× | fail |
| resident 2 | 21.454 s | 0.206× | pass |
| resident 3 | 21.726 s | 0.209× | pass |

The cold run includes startup and first-forward costs. The user permits background warmup, but these numbers do not prove that a model-loading-only prewarm removes all first-forward overhead. A representative forward warmup must actually finish before input arrival to count as resident operation.

The full measured scope includes extraction, complete Parakeet transcript, timestamped context to VLM, visual labels, Nemotron diarization, ECAPA voice embeddings, durable global registry, text/CLIP vectors and sealed catalog publication. All three runs preserved the exact same 43-word transcript. Added voice inference overlaps visual labeling; isolated stage times must not be naively added to total wall time.

The timed run exposed two issues, both retained in the raw report. A subsequent CPU-only ASR-support fix removes raw music-only public speaker turns while preserving diagnostics; replaying the cached model evidence now yields one active narrator, and the explicit lab identity policy reuses the same UUID/name across all three copies. The timed stretch link step was skipped because the controlled PATH omitted Node. A later restricted-PATH smoke using the bundled Node and the real existing CLIP vectors passed native Orama retrieval, suggestion-only behavior, explicit acceptance and provenance in 0.071 seconds (`architecture/metadata-link-smoke.json`). These fixes were smoke-tested separately; the original timings are not rewritten as though they measured a different run.

## Voice smoke fixture

Three real labeled LibriSpeech speakers: enrollment utterances0/1 are distinct from heldout probes2/3. ECAPA calibration minimum same-speaker cosine was0.74066; maximum different-speaker calibration cosine0.10316. Six heldout probes ranked their correct speaker first. Two heldout third-speaker probes were rejected when that person was not enrolled. This is a small clean regression fixture, not general field accuracy certification or an approved production threshold.

ECAPA cold load5.489s; first6s voice encode0.831s; later6s encodes about12ms. On the69.93s three-speaker clip, Nemotron+identity took2.298s after load (0.0329×), with3 speakers. The93.2% overlap-mapped utterance coverage is not DER: source utterance intervals contain internal pauses and are not hand-aligned activity references.

## Grounding and CPU costs

A forest frame paired with unrelated chocolate narration remained “Sunlit forest with fallen tree and ferns.” A bison frame with prairie narration remained “Bison in grassy prairie habitat.” These are two targeted smoke checks, not a general visual-accuracy score.

Timestamp-window lookup took about0.00093s per12frames on1200 source sentences. Registry assignment including durable SQLite writes took a median2.66ms at25 profiles and6.28ms at100 profiles, measured with synthetic unit vectors only.

Raw evidence: `benchmarks/full-pipeline.json`, `speaker-embedding.json`, `diarization.json`, `vlm-grounding.json`, `context_cpu.json`, `registry_cpu.json`.

## Actual global identity pipeline

`benchmarks/global-voices.json` runs the complete ASR/diarization/embedding/global-store path over the69.93s and86.34s three-speaker clips with different utterances. All three dataset speaker identities map to the correct same project UUIDs despite a changed speaker arrival order; operator-assigned labels persist. Total runtime9.40s was observed while OffShoot copying was permitted to overlap, so this is a quality smoke rather than a strict throughput benchmark.

## Background prewarm qualification status

Representative discarded forward warmup was subsequently GPU-qualified in `benchmarks/background-faces-before-facewarm.json`. The background actor constructor returned in 0.00031 seconds. Warmup completed in 12.808 seconds, with zero published footage snapshots and no identity database before the first input arrived. The first fresh 103.934667-second trailer then reached durable output in **25.767876 seconds (0.247924×)**, including 0.000047 seconds residual queue wait. This passes the 0.25 gate by only **0.216 seconds** in this one run; it is not a general throughput guarantee.

This measurement includes complete ASR, timestamped audio context, VLM, diarization, voice registry, face detection/embeddings, text/CLIP indexing and sealed publication. The transcript is exactly the same complete 43-word transcript as the earlier runs; one voice identity and one separate face observation are present. Analysis took 24.360 seconds, face stage 1.039 seconds (first face initialization included), registry 0.010 seconds and index 0.256 seconds. Startup plus first clip totals **38.576 seconds (0.371×)** if input is ready at launch. Background startup must finish during other work to achieve the reported ready-state ratio.

The final rerun with discarded face detector/recognizer CPU forwards is `benchmarks/background-faces.json`. Startup completed in **7.906 seconds** (including 0.406 seconds face warmup); construction returned in 0.00018 seconds and no footage/identity outputs were published by warmup. Face processing fell from 1.039 to **0.187 seconds**, but complete analysis varied upward to 25.527 seconds. Arrival-to-durable-output was **26.007831 seconds (0.250232×)** including residual wait of 0.000041 seconds: **fail by 0.024 seconds** against the strict 25.983667-second gate. Startup plus the first clip was 33.914 seconds (0.326×). The complete transcript remains identical at 43 words; one separate face observation is present. This demonstrates that the current combined process is near the requested boundary, with insufficient margin to promise the bound. Both runs are preserved; no additional optimization loop was run.

## Face identity CPU stage (isolated lab)

Official pinned OpenCV Zoo YuNet + SFace use a 128-dimensional L2-normalized model-specific namespace. CPU DNN and one OpenCV thread are requested explicitly. OpenCV 5 emits a warning that its new graph engine ignores target selection; this run imports no MLX modules and invokes no lab GPU inference. Production workload may overlap, so these are indicative stage costs rather than an uncontended overall pipeline qualification.

| CPU stage input | First stage including load | Resident stage |
|---|---:|---:|
| Six portrait variants | 0.285 s | 0.221–0.230 s |
| Twelve trailer stills, one eligible detected face | model already resident | 0.204–0.232 s |
| Twelve duplicate two-face frames, exact-crop cache | 0.409 s | 0.287–0.348 s |
| Twelve distinct two-face frames, 24 unique embeddings | 1.191 s | 0.699–0.764 s |

The duplicate case computes 2 embeddings and reuses 22; the unique case computes all 24. No crops are omitted by the configured bounds in either fixture. The original twelve trailer stills produce one detection and one eligible embedding. This is selected-still coverage only: it cannot count all people or faces appearing between samples, and no whole-video face-recall ground truth exists. The 48-pixel minimum face size, 12-pixel eye separation and sharpness checks intentionally reject weak crops.

Two anonymous public-domain fixture identities each have one original photo plus brightness/resize transformations. All six embeddings are eligible; minimum same-source cosine is 0.956 and maximum different-identity cosine 0.186. This checks basic separation and transformation stability only. It does **not** validate independent-shot identity, unknown-person rejection, broad demographics or a universal matching threshold. Auto-assignment remains off pending representative project calibration.

The official Zoo directory publishes SFace under Apache-2.0 and YuNet under MIT; their upstream training-data provenance has not been independently audited here. Source assets, hashes and attribution are in `fixtures/faces/manifest.json`. Raw CPU outputs are `benchmarks/faces-cpu.json`, `faces-bound.json`, and `faces-unique.json`. The added stage is promising against the approximately 4-second resident headroom, but adding isolated times does not prove the complete enhanced pipeline meets the gate. The full qualification above is near the strict gate: one narrow pass and one 24-millisecond failure.

## Canonical unified runtime: actual trailer and NJARAW rerun

The user subsequently authorized folding the experiments into the single runtime and allowed some performance leeway. After CPU/offline/portability checks, the root agent promoted the release to `/Volumes/ThunderBlade X8/AI Indexer`. One canonical startup reconciliation processed the existing verified receipts in `/Volumes/ThunderBlade X8/Ingests`; no additional source-media copy or duplicate staged NJARAW inference was performed.

| Scope | Wall time | Footage | Ratio |
|---|---:|---:|---:|
| Daemon start through all three jobs ready | 241.538 s | 904.654 s unique footage | 0.267× |
| First job claimed through all jobs ready | 237.960 s | 904.654 s unique footage | 0.263× |
| NJARAW seven-file job, models already resident | 198.075 s | 800.675 s | 0.247× |
| Cached duplicate trailer alias | 0.494 s | excluded from denominator | — |

The two trailer aliases refer to one content SHA and are counted once in the footage denominator. Their actual processing overhead remains in the wall time. Background warmup took 17.252 seconds total; 13.857 seconds remained after the first job claim, with the rest overlapping startup/reconciliation. The first trailer job took 39.384 seconds including that residual wait; processing begin through job completion was 25.527 seconds. All eight unique analyses total 222.631 seconds. Actual NJARAW complete-job time improved from the earlier 216.821-second baseline, though those are separate runs rather than a controlled isolated-kernel comparison.

Validation: all three jobs finished with zero errors; nine canonical aliases and eight original content SHAs remain; eight new profiles are sealed. All 128 files listed in those seals pass size and SHA-256 verification. All original source sizes/mtimes are unchanged. Every ASR track text exactly matches the earlier baseline: the complete 43-word trailer transcript and zero words for each NJARAW clip. Two trailer highlights receive timestamped audio context.

The canonical API serves catalog and 192 text/CLIP vectors from the same sealed revision. Search vectors remain 384/512-dimensional; speaker and face identity embeddings stay in their own model-specific registry spaces. Registry/index edit revisions both equal 20. There is one voice identity and fifteen sampled face observations, of which three pass the quality gates for 128-dimensional face embedding. All thirty face frame/crop references resolve. This is **not** a full-video face census: the detector sees only 81 selected stills across eight unique files; weak crops remain observations without enrollment-quality vectors. No automatic face↔voice association is inferred.

Evidence: `benchmarks/canonical-upgrade.json`, `canonical-timeline.json`, `canonical-quality.json`, `canonical-seals.json`, `canonical-api-readonly.json`, and `canonical-validation.json`. The latter catalog-only structural report has zero inline face observations because these live in the shared metadata registry; `canonical-seals.json` and `canonical-api-readonly.json` contain the actual face counts.

Promotion readiness was independently checked offline: all declared analysis/identity/search models, native selector and built viewer are ready; twelve symlinks resolve within the bundle; no runtime Python reference points to the lab/prototype; bundled Python/cv2/MLX imports, Node and ffmpeg work. Four metadata API tests independently passed; the UI and backend owners separately reported sixteen frontend tests and three deep unified CPU tests. Root owns the final native/browser interaction review.
