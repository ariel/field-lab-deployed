# Face model choice

The isolated baseline uses the official OpenCV Zoo YuNet detector and SFace face recognizer. Source/models are pinned to commit48b10fa505aeb51fbd127fc60a5c660040e823b7; the ONNX downloads are verified against the repository's Git LFS SHA-256 pointers. Licenses and source READMEs are saved beside the models in models/faces, with checksummed manifest.

- YuNet detects face boxes and five landmarks. Its directory publishes an MIT license: https://github.com/opencv/opencv_zoo/tree/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_detection_yunet
- SFace is an established MobileFaceNet trained with the SFace loss, contributed by the paper's author. The official directory reports .9940 accuracy for its evaluation, which is an upstream result, not this application's measured field accuracy. Its directory publishes Apache2: https://github.com/opencv/opencv_zoo/tree/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_recognition_sface
- Paper/source: https://github.com/zhongyy/SFace and https://arxiv.org/abs/2205.12010

Published artifact licenses are recorded here; the training dataset's rights and composition have not been independently audited. OpenCV Zoo issues313/318 request additional provenance/commercial-use clarification. Do not interpret a source code license as an independent audit of training data.

This initial face stage uses single-thread OpenCV DNN CPU inference. Other analysis/index models remain MLX. This is deliberate: the candidate MLX-UniFace port's claimed parity was not sufficient evidence. At audited revision66002ce4c3434439fb3950f19874c637b28e2e6d, its GlobalDepthwiseConv implementation constructed an ungrouped Conv2d despite describing a depthwise operation. No such port or randomly initialized weights are used. A future MLX port would require numeric parity on aligned crops against the official ONNX model before acceptance.

Face vectors are128-dimensional L2-normalized values in their own version/frontend namespace. They are not CLIP/text/speaker vectors. The operator can name a face or explicitly assert a face-to-voice relationship; the software never infers it from narration or a matching time.

Runtime bounds are12 already-selected stills,2 largest confident faces per still and24 embeddings. Input detection is downscaled to maximum640px edge. Original-resolution landmarks align112px crops for SFace. Small, blurry or poorly separated eye landmarks retain detection evidence but no enrollment vector. Quality fields are heuristic image-signal measures, not an identity probability. Exact repeated aligned pixels reuse embeddings. Sampling can miss a face between frames and may miss people in a crowd; these bounds are exposed in output counts.

Face results have their own staged, sealed, atomic cache bound to original content ID, selected-frame profile, model and preprocessing code. The raw transcript/VLM object remains immutable. Incomplete face stages are recomputed and complete results are hash checked. Registration is independently idempotent so interrupted catalog publication can be retried.
