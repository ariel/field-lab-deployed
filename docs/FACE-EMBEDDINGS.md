# Face embedding research

Research checked 2026-11-06. This is a selection note, not a change to deployed recognition. Prioritize faithful native MLX inference, measured performance on the target Mac, difficult-footage matching, and downloadable weights suitable for the intended use.

## Recommendation

The most concrete native MLX candidate found is **ArcFace iResNet100 / glintr100**, through SceneWorks' `mlx-gen-face`. It has actual Rust MLX inference, a converter, downloadable converted weights, and an ONNX comparison test. It is a strong practical baseline, rather than a claim to the newest research record. Its InsightFace-derived weights are restricted to non-commercial research unless separately licensed. That prevents making it our general filmmaking default on the strength of the code's Apache license alone. [Implementation](https://github.com/SceneWorks/mlx-gen/blob/45428fa9727c569f3f3723c7343c96b0944f9007/mlx-gen-face/src/iresnet.rs), [parity test](https://github.com/SceneWorks/mlx-gen/blob/45428fa9727c569f3f3723c7343c96b0944f9007/mlx-gen-face/tests/arcface_parity.rs), [weights and terms](https://huggingface.co/SceneWorks/instantid-mlx).

That parity test requires locally generated reference outputs and is ignored in a normal test run. Its presence is useful evidence of an engineering approach, not proof that we have run it. No recognition latency on our Mac was measured during this research.

For a reusable filmmaking package, **AuraFace-v1 ResNet100** is a candidate to benchmark and, if worthwhile, port faithfully to MLX. Its publisher explicitly permits commercial use under Apache-2.0. It ships ONNX weights; this research did not verify a ready native MLX implementation. Do not load its identically named `glintr100.onnx` with an InsightFace checkpoint's assumed preprocessing. This is a different trained model and needs its own namespace and conversion validation. Its published results establish it as a candidate, not the strongest research model. [Publisher model card](https://huggingface.co/fal/AuraFace-v1), [independent implementation's preprocessing warning](https://github.com/photoprism/photoprism/blob/develop/internal/ai/face/README.md).

## Quality-oriented alternatives

| Candidate | Evidence | MLX assessment |
| --- | --- | --- |
| CVLFace AdaFace ViT-B with keypoint RPE, WebFace12M | Author table reports IJB-C 97.82 and TinyFace rank-1 76.10; an author-hosted checkpoint is available despite the table's stale release text. | No verified native MLX port found. The checkpoint includes custom RPE code and a CUDA extension, so this needs substantial port/parity work. |
| LVFace-B, Glint360K | Official downloadable ONNX/PyTorch checkpoint; author reports IJB-C TAR 97.70% at FAR 1e-4. | No verified native MLX port found. Weights explicitly restricted to non-commercial research. |

Sources: [CVLFace author results](https://github.com/mk-minchul/CVLface/blob/main/cvlface/pretrained_models/README.md), [author checkpoint](https://huggingface.co/minchul/cvlface_adaface_vit_base_kprpe_webface12m/tree/main), [LVFace official repository](https://github.com/bytedance/LVFace). These are author-reported benchmark results, not measurements of our footage. The LVFace WebFace42M paper headline must not be attributed to its downloadable Glint360K checkpoint. No universal state-of-the-art winner is established here.

The 2026 **ViT-8R** paper reports state-of-the-art results among ViT face recognizers on IJB-B/C. Its repository provides pretrained-model links and specifies CC BY-NC-SA 4.0. No ready native MLX implementation was verified. It therefore belongs in the research comparison, rather than displacing the MLX shortlist merely because its paper is newer. [Paper](https://arxiv.org/abs/2606.12036), [author code and terms](https://github.com/TaharChettaoui/ViT-FR-Registers).

## An MLX package to avoid adopting untested

`mlx-uniface` advertises native face recognition, but the inspected recognition source substitutes a simplified MobileFaceNet-style network for ArcFace variants and catches missing weights by continuing with an untrained model. A fast embedding from that path could be meaningless. Its README timing claims are not an acceptable basis for deployment. This finding concerns the inspected recognition path, not every detector in the package. [Source at inspected revision](https://github.com/CodeWithBehnam/mlx-uniface/blob/66002ce4c3434439fb3950f19874c637b28e2e6d/uniface/recognition/models_mlx.py).

## Acceptance before switching

1. Pin the exact original and converted weights, alignment, color order, normalization, dtype, and code revision. Fail if any weights are absent or incompatible.
2. Compare real aligned face embeddings against the original runtime; then compare matching decisions on manually reviewed same/different pairs across clips, lighting, pose, costumes, and small faces.
3. Measure cold load, synchronized warm batch inference, total face-stage time, and memory alongside ASR/VLM work. MLX availability does not itself prove greater speed than Core ML on the target machine.
4. Calibrate automatic grouping and review thresholds independently for the new model. More embedding dimensions alone do not establish better recognition.
5. Re-embed into a new model namespace; retain old observations, operator names, merge/split feedback, and lineage. Never compare old SFace vectors with a new model's vectors or silently discard labels.

Our current code uses YuNet detection and SFace 128-dimensional embeddings through OpenCV CPU. Its cap of 12 sampled frames and two faces per frame is also a recall limit: a better recognizer cannot identify a face that was never sampled or detected. Benchmark coverage and recognition separately.
