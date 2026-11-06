# Book reading coverage

The team read the twelve numbered chapters of Blain Brown’s *The Filmmaker’s Guide to Digital Imaging* (2015), using the original EPUB and the existing DITGuide as context. Three subagents divided the chapters. The root reviewer read their complete reports, read chapter 12 directly, and inspected Figure 12.7.

Coverage includes extracted prose, headings, captions, text tables and XML examples. Source front matter, glossary and index were outside the assigned chapter reading. This is not a claim that all book images or numerical examples were audited.

| Chapter | Extracted lines through EOF | Whitespace-delimited words | Reviewer report |
|---|---:|---:|---|
| 1. Sensors & Cameras | 194 | 9,946 | [capture](capture.md) |
| 2. The Digital Image | 204 | 8,283 | [color-formats](color-formats.md) |
| 3. Measurement | 241 | 10,691 | [capture](capture.md) |
| 4. Linear, Gamma, Log | 268 | 12,436 | [color-formats](color-formats.md) |
| 5. Exposure | 308 | 15,396 | [capture](capture.md) |
| 6. Digital Color | 193 | 7,972 | [color-formats](color-formats.md) |
| 7. Codecs & Formats | 242 | 8,843 | [color-formats](color-formats.md) |
| 8. Image Control & Grading | 228 | 7,507 | [color-formats](color-formats.md) |
| 9. The DIT Cart | 129 | 3,578 | [workflow](workflow.md) |
| 10. Data Management | 221 | 8,579 | [workflow](workflow.md) |
| 11. Workflow | 338 | 12,167 | [workflow](workflow.md) |
| 12. Metadata & Timecode | 149 | 3,515 | [workflow](workflow.md) |

Total chapter text: 108,913 words, including extraction markers. Counts use the saved text split into lines/words; provenance’s earlier parser counts use a different token boundary. Each chapter has a final unterminated line. Reviewers checked those final lines explicitly, and all chapter XHTML final body elements were compared against the extraction. None was missing. The EPUB spine was checked for intervening chapter continuation sections.

Visually inspected:

- Figure 6.14, warm/cool/neutral gray-chart vectorscope comparisons (color/formats reviewer).
- Figure 6.15, RGB parade for a warm gray chart (color/formats reviewer).
- Figure 12.7, technical logging table and source-referenced notes table (root reviewer).

Remaining image content was read only through available captions and surrounding prose. Historical product claims were not refreshed because this pass addresses the book’s contribution to the existing research; current purchase guidance remains in MAC-SOFTWARE.md with its own dated sources.

The reports distinguish Brown’s claims, reviewer preferences, practical adaptations and source limitations. The book was treated as source material. No instructions within it were executed against production media or applications.

[Source EPUB, SHA-256 and chapter mapping](../../research/book/provenance.json). The original hash was checked during extraction. [Consolidated recommendations](../../reference/previous-system/BOOK-NOTES.md).
