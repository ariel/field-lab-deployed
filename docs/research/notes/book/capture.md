# Capture, measurement and exposure: additions from Brown

These notes apply chapters 1, 3 and 5 of Blain Brown’s *The Filmmaker’s Guide to Digital Imaging* (2015) to the existing [multiple-camera workflow](../../reference/previous-system/MULTI-CAMERA-WORKFLOW.md). The book adds the most value where the current guide moves from preserving files to preserving an image’s intended interpretation. Its examples explain why two safely copied recordings can still be difficult to cut together.

## The passages I like most

### Keep exposure consistent through a sequence

Brown includes Art Adams and Geoff Boyle’s criticism of automatically exposing every shot as far right as possible. The brightest object changes with framing; choosing exposure around it can change both noise and the amount of matching work between adjacent shots. Adams instead describes placing meaningful midtones, checking highlights and shadows, and using a meter for continuity as the camera moves. Brown also includes historical Blackmagic advice favoring ETTR for maximum signal-to-noise ratio, so this chapter presents a trade-off rather than one unanimous rule.

I like this because it connects capture to the edit. In the pump example, the wide shot and close-up should feel like the same repair attempt even though a bright window appears in only one angle. A solo filmmaker benefits from a repeatable baseline that reduces later matching work.

**Book:** chapter 5, “Using Light Meters,” “Placing Middle Gray,” and “Expose to the Right,” `OEBPS/c1W2.xhtml`; [extracted text](../../research/book/chapters/ch05.txt:234), lines 234–252 and 260–262. Counterpoint: “Black Magic Camera Exposure Advice,” lines 275–283.

**Application:** establish a tested exposure method for each camera and maintain intentional subject/midtone placement within a sequence. Log deliberate deviations and their first affected clip. This does not require identical ISO or aperture across different cameras, lenses or angles. Choosing a common visual result is the objective; a manufacturer’s specific curve and the actual light still matter.

### Record a useful reference alongside the scene

Brown distinguishes electronic test patterns from photographed charts: bars can test the downstream signal path, while a chart includes the lighting, lens, filters and sensor. His discussion of Art Adams’s compact OneShot chart is particularly useful for small crews. A neutral patch helps with exposure and neutral balance; color patches reveal differences that neutral patches cannot. He also recommends including an actual person in camera tests because skin responds to lighting differently from printed targets.

I like the emphasis on references that are quick enough to use in the field. A brief recorded chart take gives the editor something concrete to compare after the cameras and lights have been packed away.

**Book:** chapter 3, “Video Test Cards,” “The One Shot,” and “Skin Tone,” `OEBPS/cYE.xhtml`; [extracted text](../../research/book/chapters/ch03.txt:169), lines 169–183, 210–223.

**Application:** photograph the same suitable neutral/color reference with each camera under representative subject lighting at setup and after a meaningful lighting, filter or camera-mode change. Check glare, illumination and chart visibility. Log the reference clip and the sequence or clip range it applies to. Include a person in the preproduction test. Retain an additional reference still with the intended look when useful. A chart is a starting reference; it does not guarantee perfect matching or define the intended aesthetic.

### Know which image the exposure tool measures

Chapter 1 separates recording and viewing branches. Chapter 3 explains that a monitoring LUT can make a picture look clipped even when the source retains detail, and that a luma waveform may miss individual-channel clipping. Chapter 5 repeatedly asks whether the scope is reading log, a viewing conversion or some other processed output. It also describes exposure indicators whose behavior varies by camera and mode.

I like this as a practical diagnostic habit. It prevents a filmmaker from changing capture exposure solely to compensate for the wrong monitor transform. It also improves QC notes: “highlights appear clipped through this viewing transform” gives post a much clearer problem to investigate than “bad exposure.”

**Book:** chapter 1, “Raw Camera Signal Path” and “Viewing Stream,” `OEBPS/c82.xhtml`; [extracted text](../../research/book/chapters/ch01.txt:30), lines 30–36. Chapter 3, “RGB Parade” and “Clipping” (extraction heading reads “CUPPING”), `OEBPS/cYE.xhtml`; [extracted text](../../research/book/chapters/ch03.txt:50), lines 50–61 and 126–138. Chapter 5, “The 18% Solution,” `OEBPS/c1W2.xhtml`; [extracted text](../../research/book/chapters/ch05.txt:136), lines 136–149; contrasting practitioners’ scope preferences at 242–246.

**Application:** in prep, record a test and document what reaches the card, HDMI/SDI output, camera screen and scope. Identify each LUT or conversion and whether it is baked into recorded media. Check the saved source in the intended editor. For image QC, combine an actual image at useful magnification with waveform/parade and relevant exposure warnings; a clean copy report answers a different question.

## Useful additions to the existing logs

The current guide already handles independent roll sequences, physical card IDs, source paths, narrative sequences, sync status and transfer records. Keep those. Add a small camera-settings/change record and link it from the shoot log. This is our workflow synthesis from the book, not a form prescribed by Brown.

| Record | Minimum useful information | Why it helps |
|---|---|---|
| Camera setup | Camera/body ID; recording codec/mode; raster; capture rate and playback/timebase where different; source curve/gamut; WB/tint; ISO/EI; shutter; lens and ND/filter | Explains differences between cameras and changes within a camera’s shoot day. |
| Viewing setup | Output path; transform/LUT name and version; whether recorded; what the scope measures; exposure-tool mode and threshold | Lets a later reviewer reproduce the viewing assumptions. |
| Change | Camera; first affected original clip or timecode; changed fields; reason; related reference take | Avoids implying one settings row covers a whole card when it changed halfway through. |
| Reference | Original roll/path; sequence or applicable clip range; chart type; light/setup; intended look reference | Connects color and exposure evidence to the recordings it describes. |
| QC exception | Original clip and timing reference; observed symptom; viewed source/transform; follow-up status | Separates an observation from its suspected cause. |

For a solo shoot, record stable settings once at setup and record changes as they happen. Avoid retyping metadata that a tested extraction already supplies reliably. Keep these records with the project backups and handoff. OffShoot’s card-level notes can point to a setup record, but these chapters do not establish any current OffShoot or NLE metadata-import capability.

### Worked addition to the pump shoot

This is a proposed example, not observed footage:

- `SETUP_01` applies to camera A from `A007/.../C0042.MP4`, and a separate B-camera setup applies from `B003/.../C0018.MP4`. Each record names that camera’s actual curve, gamut, exposure settings, lens/filter and viewing transform.
- `REF_01` links a chart take from each camera to `PUMP_REPAIR_01`. Preserve its full native path, just as the narrative log preserves the interview and detail-shot paths.
- A B-camera ND change begins at `B003/.../C0021.MP4`. Log the change and a new reference if practical; keep the earlier settings attached to the earlier clips.
- A look note says, “Keep the workshop interior subdued; retain detail on Maya’s hands.” Link the note to the sequence and a source-linked reference still. This communicates intent that neither a checksum nor a neutral chart supplies.

## Small tests with a good return

**Test the actual lens/filter combination.** Brown warns that ND filters can introduce color differences and change infrared contamination. For multiple cameras, compare the filters you will actually use under representative daylight and with relevant fabrics and dark objects. Record the filter identity and strength. This is especially useful when only the close-up camera changes ND during a scene. Book: chapter 1, “IR and Hot Mirror Filters,” `OEBPS/c82.xhtml`, [lines 190–194](../../research/book/chapters/ch01.txt:190). The exact correction must follow the specific current camera/filter combination; the historical passage is not a blanket instruction to buy an IR filter.

**Test low-light results in the editor before relying on an ISO number.** Brown’s discussion connects visible noise to exposure, processing and channel amplification, and includes practitioners who establish usable camera ratings through tests and review. For a solo shoot, make a short representative test at the intended settings, include meaningful dark texture, and view the saved result at a useful size. Book: chapter 1, “Noise” and “ISO in Digital Cameras,” `OEBPS/c82.xhtml`, [lines 170–189](../../research/book/chapters/ch01.txt:170). Modern gain architectures make historical generalizations about ISO insufficient for selecting settings.

**Change the scene when its brightness range is the problem.** Brown separates overall exposure from the balance within the frame. Aperture shifts the whole scene; it cannot compress the difference between a dark face and a bright window. His practical alternatives include lighting/grip control, a different angle, shade or a different time of day. That is useful for solo work because a small location or framing decision can remove a problem before it becomes a postproduction task. Book: chapter 5, “Two Types of Exposure” and “A Different World of Exposure,” `OEBPS/c1W2.xhtml`, [lines 79–83](../../research/book/chapters/ch05.txt:79), 129–131.

**Close the loop after the first sequence.** Brown includes David Mullen’s practice of comparing what he saw on set with dailies and later viewing conditions, then adjusting technique. For a small production, review the first representative A/B sequence in the editor while changes are still possible. Look at matching, focus, shadow texture, highlights and intended tone, then record any revised setup. Book: chapter 5, “The Monitor” and “Know Thyself and Know Thy Camera,” `OEBPS/c1W2.xhtml`, [lines 267–272](../../research/book/chapters/ch05.txt:267). This extends the current import/relink test into a test of the images as a sequence.

## Limits and coverage

This is a full reading of the extracted prose, headings, text tables and captions for the assigned chapters. No source figures were visually inspected for these notes, and image-only labels or numerical details are outside this coverage. The extracted line numbers are stable local anchors, not printed page numbers.

| Chapter | Original XHTML | Extracted coverage | Words (`wc -w`) | Read chunks |
|---|---|---:|---:|---|
| 1, Sensors & Cameras | `OEBPS/c7V.xhtml`, `OEBPS/c82.xhtml` | Lines 1–194, complete | 9,946 | 1–65; 66–130; 131–193; final line 194 |
| 3, Measurement | `OEBPS/cY8.xhtml`, `OEBPS/cYE.xhtml` | Lines 1–241, complete | 10,691 | 1–80; 81–160; 161–240; final line 241 |
| 5, Exposure | `OEBPS/c1VW.xhtml`, `OEBPS/c1W2.xhtml` | Lines 1–308, complete | 15,396 | 1–65; 66–125; 126–190; 191–245; 246–307; final line 308 |

Total: 743 extracted lines (counted with `splitlines`, including unterminated final lines) and 36,033 whitespace-delimited words. Also read the installed skill, its source-notes counterpart in the user’s Book-Skills folder, and the current MULTI-CAMERA-WORKFLOW.md. These notes compare against that workflow; they do not claim a fresh rereading of every YouTube transcript.

Camera menus, chart products, exposure thresholds, raw/ISO behavior and software examples are from 2015. Brown sometimes generalizes raw/log behavior too broadly, and his listed gray values are not universal current targets. His gray-card and white-reflectance discussion also mixes physical reflectance with signal-level examples; those values should not become a camera setup recipe. The source-notes corrections concerning decibels and graph-slope heuristics apply here. The HDR section primarily discusses multiple exposures and historical RED HDRx, not contemporary HDR delivery. None of these chapters supports a current software purchase recommendation without separate verification.
