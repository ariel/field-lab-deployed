# Performance qualification

The lab is separate from the OffShoot trial. Production files are read-only. No lab GPU work runs until the parent grants a window.

The release gate is measured end-to-end wall time no greater than 0.25 × source duration. For the 103.979-second trailer this is 25.995 seconds. The existing analysis baseline is about 21 seconds plus 0.3 seconds for indexing; new features have about 4.7 seconds of headroom. Target at most 3 seconds of added critical-path time, reserving 1.7 seconds for variation.

Measure the complete pipeline, not the sum of isolated kernels: source probing/read/extraction, complete Parakeet transcript, frame selection, transcript-window construction, VLM labels, diarization, clean-voice embeddings, project-registry matching/writes, metadata projection, text/CLIP vectors and durable output publication. Report overlaps explicitly. Never claim a throughput gain by dropping transcript words, omitting difficult speakers, or padding the source duration with silence.

Background warmup is allowed. Report its wall time separately and state whether it actually finished before footage processing started. Any remaining startup wait after the input becomes available belongs in the end-to-end measurement. Keep models resident through a batch.

## Proposed bounds to test

- Keep audio extraction/Parakeet and frame preparation concurrent. Parakeet normally finishes before visual preparation, so transcript context should not introduce a new serial dependency.
- Supply only the timestamped ±5-second audio window. Cap the quoted context; do not send the whole transcript to every frame.
- Run maintained MLX Nemotron diarization and independent MLX ECAPA speaker verification. Model-card latency/parity figures are leads, not measured evidence on this Mac.
- Enroll at most two clean 2–6-second crops per local speaker, avoiding overlapped or unsupported speech. Identity matching against a small project registry should be negligible compared with neural inference.
- Names and operator notes require no AI recomputation. Reuse existing text/CLIP vectors and only rebuild affected search documents. Similarity suggestions use the existing CLIP space and Orama architecture.
- A silent/noisy/short/overlapping sample must not become a confident enrolled identity. Never force the nearest speaker when absolute similarity or top-two margin is insufficient.

## Fixtures and quality coverage

`fixtures/manifest.json` pins twelve real LibriSpeech test utterances from three dataset speaker IDs, with source revision, hashes, transcripts, attribution and CC-BY-4.0 license. `cross-clip-a.wav` and `cross-clip-b.wav` use different utterances from the same speakers. Enroll speakers 6930 and 1320 while holding speaker 5639 out as an open-set control; then enroll all three for cross-clip matching. Silence, noise and an overlap construction are separate controls.

Utterance extents contain internal pauses and are not hand-aligned speech activity. Evaluate voice-pair discrimination and turn/identity assignment on this smoke fixture; do not report strict DER or universal field speaker accuracy from it. Broad real-world validation remains separate.

The original trailer is useful for total runtime, one-speaker stability and checking that narration context does not invent visible objects. It cannot validate multi-speaker quality by itself.

## Required evidence

For every measured run save source duration/hash, model revisions, package lock, stage durations, overall wall time/ratio, warmup state, peak memory when available, offline network enforcement, transcript completeness comparison, identity unknown/match decisions and production-isolation checks. Report every repeat, not only the fastest. A failed or incomplete quality check is not a performance pass.
