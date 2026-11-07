# Face detection and grouping

The local recognizer remains OpenCV YuNet + SFace. A detection is a reviewable face crop; an eligible embedding is separate identity evidence. Naming a small or occluded crop does not manufacture a reliable embedding or identify an audio speaker.

Detection first uses the normal 640px pass. Only frames without a detection get one bounded 1280px retry. Coordinates and all five alignment landmarks map back using the actual resized dimensions. Source-size, eye-distance and sharpness enrollment guards remain in force; interpolating a small image does not improve its source quality. The alternative passes are not combined, so detector NMS remains responsible for deduplication.

The versioned `face-complete-link-v2` grouping policy uses a 0.65 anonymous centroid threshold, a 0.50 minimum cross-member cosine, and a 0.08 ambiguity margin. Named assignment retains the stricter 0.72 threshold. Clean observations excluded by enrollment quotas still constrain cluster support. Mutually supported fragments do not block one another as artificial rival identities; incompatible near-ties abstain from both directions. Co-visible detections, operator different-person feedback, conflicting names, voice links and embedding namespaces remain exclusions. Voice matching is unchanged.

These are calibrated defaults, not universal identity probabilities. In a private single-camera interview evaluation, the policy was frozen on 18 people before testing nine additional people. Anonymous sequential replay improved pair recall from 14.1% to 85.6% on calibration and 10.7% to 62.1% on the holdout; neither subset produced a mixed-person group. This does not validate cross-camera/session performance, lookalikes, costumes or all lighting conditions. Uncertain groups still need operator review. No private footage, vectors or labels are distributed with this repository.

## Existing projects: face-only maintenance

Use the prepared release's Python and CLI. Planning is read-only:

```sh
/path/to/release/.venv/bin/python /path/to/release/dit_notes.py tune-faces /path/to/project
/path/to/release/.venv/bin/python /path/to/release/dit_notes.py tune-faces /path/to/project --run
```

Apply only when ingestion is quiet. The command checks existing sealed analysis, makes a SQLite backup, and examines selected stills that have **no saved face observation**. It adds new crops in `_DIT_NOTES/face-maintenance/`, leaving original files and sealed transcript/caption results intact. It does not search between selected stills or recover a second person in a frame that already has a detection.

Crops are durably sealed before one SQLite transaction appends observations and groups faces. Existing observations, operator labels, voice data and annotations are retained. A deterministic job/audit marker makes resuming safe after an interruption; search publication resumes independently if it fails. Projection-only publication does not regroup voices or inherit notes. Do not restore the backup over subsequent operator edits as a routine retry.

The whole-analysis cache remains conservatively keyed by detector implementation. This command backfills existing seals without changing their analysis profiles; it does not make later full-analysis cache invalidation stage-specific. Inspect the normal reindex plan after an update, and do not trigger a full transcript/VLM reanalysis merely to refresh faces. The installer does not automatically run this maintenance command.

A synthetic 500-observation/50-identity check took 9.46 seconds to assign normally and 0.16 seconds for regrouping. A deliberately fragmented 500-group historical registry did not finish regrouping within the 55-second benchmark bound. Large historical backfills belong in downtime; this is not a fixed wall-clock guarantee.
