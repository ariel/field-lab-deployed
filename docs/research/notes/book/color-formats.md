# Book notes: color, look records and file formats

Blain Brown, *The Filmmaker’s Guide to Digital Imaging*, 2015. Read against the existing `ONE-PAGER.md` and `MULTI-CAMERA-WORKFLOW.md`. These notes cover chapters 2, 4, 6, 7 and 8. The practical procedures below are our adaptations for a solo filmmaker; Brown did not document OffShoot.

## What I like most

### A look report is another useful production log

Brown explicitly recommends simple spreadsheets recording LUT use to prevent a transform being applied twice. This is an unusually cheap, practical answer to a problem that can look like bad cinematography when someone opens the files later. It complements the guide’s existing copy reports and narrative log.

For the pump example, keep `A007` as the OffShoot source label and `PUMP_REPAIR_01` as the narrative association. Add a look record referring to the original clip or a clearly bounded group of clips. Record the exact input curve and gamut, the transform file/version, its position, and whether it affected only monitoring or was rendered into a derivative. Include the derivative path. Store the actual look file in `04_LOOKS`, with a reference still and short intent note.

A useful row says that `A/A007/.../C0042.MP4` used `PUMP_WARM_v02.cube` on the monitoring branch, that the camera original remains in its recorded encoding, and that a named review export has that transform rendered into its pixels. The curve/gamut values must come from the actual camera mode; they cannot be inferred from `.MP4`. This is a fictional example, and it establishes no current OffShoot metadata interchange capability.

**Book evidence:** chapter 8, “We Already Baked This Turkey,” `OEBPS/c33G.xhtml`, [extracted text lines 221–222](../../research/book/chapters/ch08.txt:221). Related: “Calibration LUTs,” lines 219–220, and “Viewing LUTs,” lines 196–203. **Our synthesis:** the proposed log fields, links and folder placement.

### Save an approved frame before your memory of the scene changes

“Exporting and Reusing Grades” describes how people adapt to a strong look during a long grade and then push it further on later scenes. Brown recommends saved frame references, including reusable grade information where the software supports it. I like this because it applies even when the same person shoots and edits: a month later, you are effectively handing material to a different version of yourself.

Save a source-linked reference frame for each recurring lighting setup. Record the source timecode and rate, intended appearance, and look version. For example: “Workshop remains warm; retain the cool daylight at the open door.” On the next day, compare the new material with the stored reference. Keep a distinction between an approved creative reference and a temporary viewing conversion. A JPEG alone is insufficient to reproduce the treatment; retain the relevant look/grade and interpretation information too.

**Book evidence:** chapter 8, “Exporting and Reusing Grades,” `c33G.xhtml`, [lines 150–153](../../research/book/chapters/ch08.txt:150); chapter 2, “Digital Negative,” `cHD.xhtml`, [lines 26–35](../../research/book/chapters/ch02.txt:26). **Our synthesis:** the source-keyed record and pump-shoot example.

### Match cameras using a recorded test of the actual scene

The book separates the blue–orange temperature axis from green–magenta tint. It also explains that camera matrices affect color reproduction in ways that a neutral-balance adjustment does not establish. Its discussion of proprietary curves makes clear why two camera settings bearing the same broad label need not produce matching pictures.

For A and B cameras, record a neutral target and color chart under the same representative lighting, then include a person and important wardrobe or props. Record the camera mode, white balance and tint, filters, and viewing transform. Import those files through the intended editorial route and compare them after the correct per-camera interpretation. A shared “5600 K” setting does not by itself demonstrate a match. If the lighting changes materially, record another reference and log the change. This is a useful addition to the guide’s camera register without turning every clip into a manual technical form.

**Book evidence:** chapter 6, “Color Temperature: The Balances,” `c2CD.xhtml`, [lines 65–71](../../research/book/chapters/ch06.txt:65), and “The Matrix,” lines 156–191; chapter 4, “The Rec.709 Transfer Function,” `c1A3.xhtml`, lines 65–72. **Our synthesis:** the test sequence and selective logging procedure. The one-paragraph “Metamerism” section at the end of chapter 6 supplies background only; it is too brief to establish a detailed modern camera-matching method.

### Diagnose the viewing transform before condemning the recording

Brown’s LUT-order example explains how a viewing transform can clip highlights or crush shadows even though useful source information remains. Moving an appropriate correction before that constraining transform can change the result. This helps explain why a failed-looking preview does not establish that a file is damaged.

For the guide, record whether a QC observation was made on the original interpretation, a monitoring feed, or a rendered proxy. If a highlight appears clipped, inspect the source through the known pipeline before logging “camera clipping.” Also check whether a display conversion has been applied twice. This does not recover detail absent from the recording.

**Book evidence:** chapter 8, “Proper Use of LUTs in Color Correction,” `c33G.xhtml`, [lines 194–198](../../research/book/chapters/ch08.txt:194). **Qualification:** this describes a specific normalization/display-transform context. It does not justify a universal rule that every LUT goes last. Calibration, input, creative and output transforms have distinct roles and assumptions.

### Specify what each derivative is for

Chapter 7’s opening is excellent: different crew members can describe the same clip by frame rate, wrapper, codec, precision or recording type. Each description leaves something out. Chapter 8 also distinguishes the different files a production may make for a director, editorial and VFX.

The existing guide already requires a proxy reconform test. Extend its test record with the derivative’s purpose and exact settings: container, codec/profile, dimensions, playback rate, audio layout, color interpretation, rendered look and identity fields. A review movie may need a readable appearance and burn-ins. An editing proxy must follow the chosen linking and timing convention. A VFX delivery may require a different treatment agreed with its recipient. One export preset should not silently become the answer to all three requests.

On a solo Mac workflow, first test the actual edit with representative original files, including the number of simultaneous angles you expect. If playback is inadequate, test a proxy route. Brown’s intra/inter-frame explanation supplies the reason an edit can be harder to decode than file size alone suggests; his old codec inventories cannot predict current Mac performance. Test difficult material such as moving foliage, fine texture, noise and gradients through the actual export and final viewing route before accepting a compression setting.

**Book evidence:** chapter 7, “Video File Formats” and “The Characteristics of a Video Image,” `c2T0.xhtml`, [lines 7–32](../../research/book/chapters/ch07.txt:7), “Visually Lossless,” lines 74–75, “Intra-Frame vs. Inter-Frame,” lines 95–100, and “Compression Artifacts,” lines 240 onward; chapter 8, “What Happens at the Cart Doesn’t Stay at the Cart,” `c33G.xhtml`, lines 31–45. **Our synthesis:** the export-record fields and test procedure.

## Small additions that would strengthen the guide

| Record | Useful addition | When to enter it |
|---|---|---|
| Camera register or setup log | Recording mode, exact curve/gamut, white balance/tint, relevant filters, monitoring output treatment | Initial setup and each material change |
| Look log | Source paths or bounded scope, look/version, input/output assumptions, transform order, baked-in status, derivative path | Look changes and derivative creation |
| Reference-frame index | Source clip, timecode/rate, setup, intent, approval/provisional status | Each recurring look/setup |
| Proxy test record | Codec/profile, dimensions, rate, audio layout, color settings, identity/relink result | Preproduction and changed export settings |
| QC issue | Source or derivative inspected, transform active, scope point if relevant | When recording a suspected picture problem |

Most values belong once per setup or export preset, with clip exceptions linked back to that record. This keeps the field workload manageable. Continue putting story observations and pickup requests in the shoot log; look intent can use the same sequence ID without turning the OffShoot roll name into a description of the scene.

Chapter 4’s examples show that waveform targets depend on the selected curve and monitoring transform. Preserve the curve and measurement point when recording exposure-test results. Avoid copying one historical middle-gray percentage into every camera checklist. [Chapter 4, “18% Gray in Log” and “Variation in Log Curves,” `c1A3.xhtml`, lines 223–254](../../research/book/chapters/ch04.txt:223).

## Historical and accuracy limits

The useful parts here are the reasoning and workflow distinctions. The 2015 codec lists, camera menus, RAW behavior, LUT hardware and Resolve interface examples require present-day documentation before configuring equipment. RAW, log, uncompressed, high resolution and high bit depth describe different properties. The text itself includes camera-specific RAW exceptions, so its broader claims about reversible white balance must be qualified by exact camera/mode.

The source has numerical and terminology problems identified in `source-notes.md`: code counts and bit-depth examples, decimal/binary storage units, a mislabeled intra-frame sentence, and damaged chromaticity tables. I have not copied those into operational specifications. Its simple LUT-size quality categories also should not become universal acceptance thresholds. Repeated projection flashes do not add captured temporal samples. “Visually lossless” is a viewing judgment; it does not establish byte identity.

The closing paragraph of chapter 8 places technical control in service of storytelling. That supports saving a short statement of visual intent alongside technical metadata: later readers need to know whether a dark, warm or unusual image was deliberate. It does not waive file verification or justify disguising an acquisition problem.

## Reading and visual coverage

Read all extracted text of these five chapters in sequential chunks, then checked the original EPUB endings and read each final paragraph directly. Initial chunk boundaries used `wc -l`, which counts newline characters and excluded the final unterminated line. The extraction itself retained those tails. Direct source checks covered chapter 2’s final dB paragraph, chapter 4’s Figure 4.49 caption, chapter 6’s metamerism paragraph, chapter 7’s concluding compression-artifact paragraph, and chapter 8’s Poynton paragraph. The EPUB spine has no omitted continuation sections between these chapter pairs and the following chapter.

| Chapter | Original XHTML | Extracted lines initially read |
|---|---|---|
| 2, The Digital Image | `cH7.xhtml`, `cHD.xhtml` | 1–204 (last line also checked in source) |
| 4, Linear, Gamma, Log | `c19X.xhtml`, `c1A3.xhtml` | 1–268 (last line also checked in source) |
| 6, Digital Color | `c2C7.xhtml`, `c2CD.xhtml` | 1–193 (last line also checked in source) |
| 7, Codecs & Formats | `c2SU.xhtml`, `c2T0.xhtml` | 1–242 (last line also checked in source) |
| 8, Image Control & Grading | `c33A.xhtml`, `c33G.xhtml` | 1–228 (last line also checked in source) |

Chapter 2’s first read had a 65-token truncation inside the chroma-subsampling passage; lines 45–48 were reread untruncated. Final source-tail checking used a separate bounded XML read after an overly large diagnostic output. Full prose coverage includes source captions and text tables, but it does not imply a numerical audit or inspection of every image.

Visually inspected only chapter 6 Figures 6.14 and 6.15, original EPUB resources `OEBPS/image_rsrc76C.jpg` and `OEBPS/image_rsrc76D.jpg`: the first compares warm, cool and neutral gray-chart vectorscope traces; the second shows unequal RGB parade levels for a warm gray chart. These support the chapter’s explanation of neutral-balance measurement. All other figures were encountered as captions/image markers, not visually reviewed.
