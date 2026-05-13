# digest-technical-paper — Technical Spec

The README explains what this tool is and how to use it. This spec describes what the code must do.

Scope: the spec covers the deterministic extraction pipeline. No LLM stages are in scope; the tool produces handoff artifacts and stops.

## 0. Conventions

- Python 3.10+
- All paths in this spec are relative to the `--out` directory passed on the CLI
- All JSON files are UTF-8, indented 2 spaces, with trailing newline
- Char offsets are zero-based, end-exclusive (`[start, end)`)
- Page IDs are 1-based integers (`page_id: 1` is the first page)
- Bounding boxes are `[x0, y0, x1, y1]` in PDF points (1/72 inch), origin top-left

## 1. CLI contract

```
python scripts/process_pdf.py INPUT_PDF --out OUT_DIR [flags]
```

### Required arguments

- `INPUT_PDF` — path to a PDF file. Must exist and be readable.
- `--out OUT_DIR` — output directory. Created if absent. Existing contents may be overwritten.

### Flags

| Flag | Default | Effect |
|---|---|---|
| `--max-pages N` | none | Process only the first N pages. Manifest records this. |
| `--dpi N` | 200 | Page raster DPI for `pages/*.png`. |
| `--cache` | off | If `artifacts/run_manifest.json` exists and its `input_pdf_sha256` matches the new input, skip Stages 1–3 and rebuild only the context packet. |
| `--fail-on-low-quality` | off | Exit code 1 if any quality gate fails. Without the flag, gate failures only warn. |

#### Parser toggles

These map directly to Docling's pipeline options. They exist for controlled A/B testing of pipeline behavior, not for end-user use. Defaults are the spec's intended production values; tests vary them. Each accepts `on` or `off`.

| Flag | Default | Effect |
|---|---|---|
| `--formula-enrichment {on,off}` | `on` | Docling's `do_formula_enrichment`. When `on`, math is extracted as LaTeX; when `off`, math comes through as flattened Unicode. |
| `--table-structure {on,off}` | `on` | Docling's `do_table_structure`. When `on`, tables are structured with cell-level layout; when `off`, tables degrade to text blocks. |
| `--ocr {on,off}` | `off` | Docling's `do_ocr`. Off by default since the tool targets native-text PDFs; see §16 for the auto-detect design when this is revisited. |

All three are recorded in the manifest under `cli_flags` so a run's behavior is reproducible from its manifest alone.

Usage pattern for experiments:

```bash
for fe in on off; do
  pixi run python scripts/parse_pdf.py paper.pdf \
    --out runs/fe-$fe --formula-enrichment $fe
done
diff -r runs/fe-on/artifacts/text runs/fe-off/artifacts/text
```

### Exit codes

- `0` — pipeline completed
- `1` — quality gate failed and `--fail-on-low-quality` was set
- `2` — input PDF missing, unreadable, or zero pages
- `3` — uncaught exception in a stage (stderr contains traceback)

## 2. Output directory layout

```
OUT_DIR/
├── artifacts/
│   ├── original.pdf                # verbatim copy of INPUT_PDF
│   ├── run_manifest.json
│   ├── pages/
│   │   └── page_0001.png ...       # one per page, zero-padded to 4 digits
│   ├── parser/
│   │   ├── raw_output.json         # DoclingDocument as JSON
│   │   └── raw_output.md           # Docling markdown, pre-cleanup
│   ├── text/
│   │   ├── plaintext.txt
│   │   ├── sections.json
│   │   └── provenance.json
│   ├── figures/
│   │   ├── figures.json
│   │   └── figure_NNN.png ...      # cropped from page rasters
│   ├── tables/
│   │   ├── tables.json
│   │   └── table_NNN.csv ...
│   ├── algorithms/
│   │   ├── algorithms.json
│   │   └── algorithm_NNN.png ...
│   ├── equations/
│   │   ├── equations.json
│   │   └── equation_NNN.png ...
│   ├── references/
│   │   └── references.json
│   └── quality/
│       └── quality_report.json
└── outputs/
    ├── paper.md                    # the human/AI-facing markdown
    └── context_packet.json
```

Files in `artifacts/` are intermediate. Files in `outputs/` are the deliverables.

## 3. Pipeline stages

```
Stage 0  Input        copy PDF, init manifest
Stage 1  Parse        Docling + PyMuPDF, populate artifacts/parser/ and artifacts/pages/
Stage 2  Normalize    Docling output → internal schema, populate artifacts/{text,figures,tables,algorithms,equations,references}/
Stage 2.5 Sanity      fix heading hierarchy, detect abstract, demote false-positive sections
Stage 3  Packet       compose outputs/context_packet.json and outputs/paper.md
```

Stages run sequentially. Each writes its artifacts and the next stage reads them from disk. This makes the pipeline resumable and the artifacts auditable.

## 4. Stage 0 — Input

### Inputs

- `INPUT_PDF` path

### Actions

1. Verify the file exists, is readable, and `fitz.open()` succeeds with `len(doc) > 0`. Otherwise exit code 2.
2. Compute SHA-256 of the input.
3. `shutil.copy2(INPUT_PDF, OUT_DIR/artifacts/original.pdf)`.
4. Write `artifacts/run_manifest.json` (see §10 for schema).

### Manifest at this stage

Populated fields: `input_pdf`, `input_pdf_sha256`, `out_dir`, `tool_version`, `timestamp_utc`, `cli_args`. Other fields populated by later stages.

## 5. Stage 1 — Parse

### Inputs

- `artifacts/original.pdf`
- Manifest from Stage 0

### 5.1 Page rasterization

For each page, call `page.get_pixmap(dpi=DPI)` and write to `artifacts/pages/page_NNNN.png` where `NNNN` is the 1-based page number zero-padded to 4 digits. If `--max-pages N` was set, stop after N pages.

### 5.2 Docling parse

Invoke the parser through the `Parser` Protocol (§9). Configuration is driven by the parser-toggle CLI flags (§1):

```python
pipeline_options.do_formula_enrichment = cli_flags.formula_enrichment  # default on
pipeline_options.do_table_structure    = cli_flags.table_structure      # default on
pipeline_options.do_ocr                = cli_flags.ocr                  # default off
```

The hardcoded defaults match the production-intended values. The flags exist so an experiment script can toggle each option and compare runs without editing source. See §1 for the flag table and §16 for OCR-specific notes.

Write the result two ways:
- `artifacts/parser/raw_output.json` — `DoclingDocument` exported as JSON
- `artifacts/parser/raw_output.md` — Docling's markdown export

### 5.3 Manifest update

Populated fields after Stage 1: `parser.name` (`"docling"`), `parser.version` (Docling's installed version), `parser.config` (the effective Docling pipeline options after flag resolution), `page_count_processed`, `dpi`.

## 6. Stage 2 — Normalize

### Inputs

- `artifacts/parser/raw_output.json` (the DoclingDocument)
- `artifacts/pages/page_NNNN.png` (for cropping figures/algorithms/equations)

### Constraint

This is the only stage in the pipeline that imports from `docling` directly or types its parameters as `DoclingDocument`. All downstream stages consume the internal schema only.

### 6.1 Canonical text — `artifacts/text/plaintext.txt`

Iterate the `DoclingDocument.body` block tree in document order. For each block:

- **Skip** blocks with label `page_header` or `page_footer`. These are IEEE running headers, page numbers, conference banners, copyright notices.
- **Skip** the document title block (`section_header` matching the title-detection rule in §7.1).
- **Skip** blocks whose `label` is `picture`, `table`, or formula-only — their content lives in structured artifacts, not in canonical text. Exception: tables that Docling represents as text fall back to inclusion.
- **Include** blocks with label `text`, `paragraph`, `caption`, `list_item`, `section_header` (non-title), `formula` (rendered as `$...$` or `$$...$$` LaTeX from Docling's enrichment), `code` (algorithm pseudocode, rendered as a fenced block).

Apply these transforms to included text:

- Normalize ligatures: `ﬁ→fi`, `ﬂ→fl`, `ﬀ→ff`, `ﬃ→ffi`, `ﬄ→ffl`
- Preserve em-dashes (`—`, U+2014) and en-dashes (`–`, U+2013) verbatim. Do not collapse to ASCII hyphen.
- Preserve math symbols verbatim (e.g. `∗`, `≤`, `≥`, `→`, `π`, `Σ`).
- Rejoin words split by line-end hyphenation: if a line ends with `word-` and the next line starts with a lowercase letter, concatenate. Exception: if the hyphenated form is a known compound (regex check against a small list, or always preserve when the suffix is also dictionary-valid), keep the hyphen.
- Collapse runs of two or more blank lines into a single blank line.

Section headers are emitted as their plain text on a line of their own, with a blank line before and after.

Write the result as UTF-8 to `artifacts/text/plaintext.txt` with a trailing newline.

### 6.2 Sections — `artifacts/text/sections.json`

Schema:

```json
[
  {
    "id": "sec-001",
    "heading": "I. INTRODUCTION",
    "level": 1,
    "start_char": 1246,
    "end_char": 5394,
    "page_start": 1,
    "page_end": 1
  }
]
```

- `id` — `sec-NNN`, zero-padded to 3 digits, in document order starting at `001`.
- `heading` — verbatim text of the heading block.
- `level` — set initially from Docling's `level`. Stage 2.5 may rewrite it.
- `start_char` / `end_char` — char offsets into `plaintext.txt`. `end_char` is the start of the next section, or `len(plaintext)` for the last section.
- `page_start` / `page_end` — derived from the provenance map.

Title is **not** in `sections.json` after Stage 2.5; it lives in `context_packet.paper_profile.title`. Stage 2 may emit it provisionally; Stage 2.5 removes it.

### 6.3 Provenance — `artifacts/text/provenance.json`

Schema:

```json
{
  "blocks": [
    {
      "block_id": "docling-ref-or-internal-id",
      "char_start": 0,
      "char_end": 87,
      "page": 1,
      "bbox": [54.0, 72.0, 290.5, 90.2],
      "kind": "text"
    }
  ]
}
```

One entry per included block in `plaintext.txt`, in document order. `char_start`/`char_end` are offsets into `plaintext.txt`. `kind` mirrors the Docling label (after our skip-list filtering).

This file is what makes "page-level provenance" real. A consumer can map any char offset in `plaintext.txt` back to a page and bbox by binary-searching this list.

### 6.4 Figures — `artifacts/figures/figures.json` and `artifacts/figures/figure_NNN.png`

For each Docling `picture` block:

```json
{
  "id": "fig-001",
  "page": 4,
  "bbox": [108.0, 480.2, 504.0, 700.5],
  "caption": "Fig. 1. Conformal prediction for ...",
  "image_path": "artifacts/figures/figure_001.png"
}
```

Crop the figure region from the corresponding `artifacts/pages/page_NNNN.png` using the bbox (convert PDF points to pixels using DPI). Write as `figure_NNN.png`. If Docling provides a linked caption block, use it; otherwise leave `caption: null`.

### 6.5 Tables — `artifacts/tables/tables.json` and `artifacts/tables/table_NNN.csv`

For each Docling table:

```json
{
  "id": "tab-001",
  "page": 5,
  "bbox": [...],
  "title": "Table I: ...",
  "csv_path": "artifacts/tables/table_001.csv",
  "html_path": null,
  "rows": 8,
  "cols": 4
}
```

Export the table to CSV. If Docling provides HTML representation, also write `table_NNN.html` and set `html_path`. If the document has no tables, write `{"items": []}`.

### 6.6 Algorithms — `artifacts/algorithms/algorithms.json` and `artifacts/algorithms/algorithm_NNN.png`

For each Docling block that matches the algorithm pattern (either label `code` near a heading matching `^Algorithm\s+\d+`, or a `section_header` matching that pattern with a following code block):

```json
{
  "id": "alg-001",
  "page": 6,
  "bbox": [...],
  "title": "Algorithm 1 Conformal Off-Policy Evaluation in MDPs",
  "image_path": "artifacts/algorithms/algorithm_001.png",
  "raw_text": "Require: Datasets D_tr, D_cal; ..."
}
```

Crop the bounding region to PNG. Include the raw pseudocode text in `raw_text` for downstream LLM use. The PNG matters because the 2D layout (indentation, line numbering) is what makes pseudocode readable, and that layout flattens in text.

### 6.7 Equations — `artifacts/equations/equations.json` and `artifacts/equations/equation_NNN.png`

For each Docling `formula` block at display (not inline) scale:

```json
{
  "id": "eq-001",
  "page": 3,
  "bbox": [...],
  "latex": "w(x,y) = \\frac{\\int ...}{\\int ...}",
  "image_path": "artifacts/equations/equation_001.png",
  "number": "(1)"
}
```

`latex` comes from Docling's formula enrichment. `number` is the parenthesized equation label if Docling provides it, else null. The PNG is a crop of the rendered equation.

### 6.8 References — `artifacts/references/references.json`

Each bibliography entry:

```json
{
  "id": "ref-001",
  "raw": "[1] Léon Bottou et al. Counterfactual reasoning and learning systems...",
  "key": "1",
  "authors": ["Léon Bottou", "Jonas Peters", "..."],
  "title": "Counterfactual reasoning and learning systems",
  "venue": "Journal of Machine Learning Research",
  "year": 2013
}
```

Parsing fidelity expectations: `raw` and `key` are required. The structured fields are best-effort; null on parse failure. We don't ship a bibliography parser — if Docling provides structured references, use them; otherwise emit `raw` and `key` only.

## 7. Stage 2.5 — Section hierarchy sanity pass

### Inputs

- `artifacts/text/sections.json` (provisional)
- `artifacts/text/provenance.json`
- The first-page page raster (for title-region heuristics if needed)

### Constraint

Parser-independent. This stage knows nothing about Docling.

### Rules, applied in order

#### 7.1 Title detection

The document title is the first `section_header` block satisfying all of:

- Appears before any block whose heading text matches the numbering patterns in §7.3.
- Heading text length > median heading length in `sections.json`.
- Heading text does not match any of the numbering patterns.
- Heading text is not in the literal set `{"Abstract", "ABSTRACT", "References", "REFERENCES", "Bibliography", "BIBLIOGRAPHY"}`.

Action: remove this section from `sections.json`. Store the heading text as the document title (used later by the context packet).

If no candidate satisfies all conditions, record anomaly `title_not_detected` and proceed.

#### 7.2 False-positive section demotion

For each remaining section, if `heading` matches any of:

```
^Algorithm\s+\d+
^Theorem\s+\d+
^Lemma\s+\d+
^Proposition\s+\d+
^Definition\s+\d+
^Corollary\s+\d+
^Remark\s+\d+
^Example\s+\d+
^Fig(\.|ure)?\s*\d+
^Table\s+[IVX\d]+
```

Remove the section from `sections.json` (the text remains in `plaintext.txt`; only the false section heading goes). Record anomaly `false_positive_demoted` with the heading text.

#### 7.3 Numbering scheme detection

Match remaining section headings against:

- Roman top-level: `^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\.\s+[A-Z]`
- Arabic top-level: `^\d+\.\s+\S`
- Nested arabic: `^\d+\.\d+(\.\d+)*\s+\S`
- Letter sub-level: `^[A-Z]\.\s+\S`

The dominant top-level scheme is whichever of Roman/Arabic has the most matches. Record as `numbering_scheme` in the quality report.

#### 7.4 Level assignment

Given the dominant scheme:

- Top-level match → `level: 1`
- Letter sub-level immediately following a Roman top-level (in document order, no intervening top-level) → `level: 2`
- Nested-arabic immediately following an Arabic top-level → `level: 2`
- Headings matching the literal set `{"REFERENCES", "BIBLIOGRAPHY", "ACKNOWLEDGMENTS", "ACKNOWLEDGEMENTS", "APPENDIX"}` (case-insensitive) → `level: 1` regardless of formatting
- Anything unmatched → leave at parser-reported level, record anomaly `unclassified_heading` with the heading text

#### 7.5 Abstract synthesis

If no section's heading is "Abstract" (case-insensitive) after Stage 2 emits:

Identify the char range between the end of the title (offset 0 if no title detected, otherwise the title's `end_char` which is 0 because the title was removed) and the `start_char` of the first `level: 1` section.

If this range contains at least 200 characters of body text, prepend a synthetic section:

```json
{
  "id": "sec-abstract",
  "heading": "Abstract",
  "level": 1,
  "start_char": 0,
  "end_char": <start of first numbered section>,
  "page_start": 1,
  "page_end": <derived>,
  "synthetic": true
}
```

Otherwise record anomaly `abstract_not_detected`.

#### 7.6 Hierarchy consistency check

The check passes if **all** of:

1. A title was detected.
2. At least one section is `level: 1`.
3. No `level: 2` heading appears before any `level: 1` heading in document order.
4. A section heading matches `^REFERENCES$|^BIBLIOGRAPHY$` (case-insensitive) and is at `level: 1`.
5. An Abstract section exists (synthetic or real) at `level: 1`.
6. No section heading in the final `sections.json` matches the false-positive patterns from §7.2.

Record the pass/fail of each as a boolean in the quality report under `hierarchy_checks`. The overall gate `section_hierarchy_consistent` is the AND of all six.

#### 7.7 Anomaly recording

Every check failure or rule trigger appends to `quality_report.section_sanity_anomalies`. Each anomaly is an object:

```json
{
  "code": "false_positive_demoted",
  "detail": "Algorithm 1 Conformal Off-Policy Evaluation in MDPs",
  "page": 6
}
```

Codes used:

- `title_not_detected`
- `false_positive_demoted`
- `unclassified_heading`
- `abstract_not_detected`
- `references_at_wrong_level`
- `hierarchy_check_failed:<check_number>`

## 8. Stage 3 — Context packet and final markdown

### 8.1 Context packet — `outputs/context_packet.json`

Schema:

```json
{
  "schema_version": "1",
  "paper_profile": {
    "title": "Conformal Off-Policy Evaluation in Markov Decision Processes",
    "authors": ["Daniele Foffano", "Alessio Russo", "Alexandre Proutiere"],
    "page_count": 8,
    "input_pdf_sha256": "...",
    "parser": {"name": "docling", "version": "2.91.0"},
    "tool_version": "..."
  },
  "canonical_text": {
    "path": "artifacts/text/plaintext.txt",
    "char_count": 41961
  },
  "sections": [...],
  "figures": [...],
  "tables": [...],
  "algorithms": [...],
  "equations": [...],
  "references": [...],
  "quality": {
    "status": "ok" | "warn" | "fail",
    "gates": {...},
    "anomalies": [...]
  },
  "evidence_index": {
    "original_pdf": "artifacts/original.pdf",
    "pages_dir": "artifacts/pages/",
    "page_paths": ["artifacts/pages/page_0001.png", ...]
  }
}
```

The arrays are not re-derived; they are loaded from the corresponding artifact JSONs. The packet is the curated handoff: it points into the artifacts, doesn't duplicate them.

Authors detection: if Docling provides authors in document metadata, use them. Otherwise null. We don't ship an author parser.

### 8.2 Final markdown — `outputs/paper.md`

Render the canonical text as Markdown with section headings restored as `#` / `##` / `###` based on `level` (level 1 → `#`, level 2 → `##`, level 3 → `###`). Use a YAML frontmatter block at the top:

```yaml
---
title: <paper title>
authors:
  - <author 1>
  - <author 2>
source_sha256: <input_pdf_sha256>
parser: docling <version>
tool_version: <tool version>
---
```

Figures, tables, and algorithms are referenced inline at their original document position with markdown image syntax or fenced code:

- Figures: `![Fig. 1. Caption text](../artifacts/figures/figure_001.png)`
- Tables: load the CSV, render as markdown table (only if `rows <= 50`; otherwise emit a link)
- Algorithms: fenced code block with the `raw_text` content, plus an image reference
- Equations: inline LaTeX `$...$` or display LaTeX `$$...$$` — leave as text, do not embed images

The path references in the frontmatter and image links are **relative to `outputs/paper.md`**, so the file is portable if the user copies the outputs directory elsewhere.

## 9. Parser Protocol

```python
from typing import Protocol
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ParserOutput:
    raw_doc: object              # implementation-defined
    markdown: str
    page_count: int

class Parser(Protocol):
    name: str                    # e.g. "docling"
    version: str                 # parser package version
    def parse(self, pdf_path: Path) -> ParserOutput: ...
```

Code outside `scripts/parsers/` must not `import docling` (or any other parser package). Stage 2's normalize step is the only consumer of `raw_doc` and may type its parameter as `DoclingDocument` because it is parser-aware.

The default parser is `scripts/parsers/docling_parser.py`. Adding a second parser means: implement the Protocol, register it in `scripts/parsers/__init__.py`, and add a CLI flag to select. Until that happens, no flag is needed.

## 10. Run manifest schema — `artifacts/run_manifest.json`

```json
{
  "schema_version": "1",
  "tool_version": "0.1.0",
  "timestamp_utc": "2026-05-11T10:30:00Z",
  "input_pdf": "path/as/passed/to/cli.pdf",
  "input_pdf_sha256": "...",
  "out_dir": "/abs/path/to/out",
  "cli_args": {
    "max_pages": null,
    "dpi": 200,
    "cache": false,
    "fail_on_low_quality": false,
    "formula_enrichment": "on",
    "table_structure": "on",
    "ocr": "off"
  },
  "parser": {
    "name": "docling",
    "version": "2.91.0",
    "config": {
      "do_formula_enrichment": true,
      "do_table_structure": true,
      "do_ocr": false
    }
  },
  "page_count_processed": 8,
  "dpi": 200,
  "stages_completed": ["input", "parse", "normalize", "sanity", "packet"],
  "duration_seconds": {
    "parse": 14.2,
    "normalize": 0.3,
    "sanity": 0.05,
    "packet": 0.1
  }
}
```

Schema version is bumped on any breaking change to the manifest layout.

## 11. Quality report schema — `artifacts/quality/quality_report.json`

```json
{
  "schema_version": "1",
  "status": "ok" | "warn" | "fail",
  "canonical_char_count": 41961,
  "section_count": 22,
  "gates": {
    "canonical_non_empty": true,
    "has_abstract": true,
    "has_references": true,
    "raster_page_count_ok": true,
    "section_hierarchy_consistent": false
  },
  "hierarchy_checks": {
    "title_detected": true,
    "has_level_1_section": true,
    "no_premature_level_2": true,
    "references_at_level_1": true,
    "abstract_section_exists": true,
    "no_false_positive_headings": false
  },
  "section_sanity_anomalies": [
    {"code": "false_positive_demoted", "detail": "Algorithm 1 ...", "page": 6}
  ],
  "numbering_scheme": "roman",
  "failures": ["section_hierarchy_consistent"],
  "warnings": []
}
```

### Gate semantics

- `canonical_non_empty` — `len(plaintext.txt) > 0`
- `has_abstract` — an Abstract section exists in final `sections.json`
- `has_references` — a section heading matches `^REFERENCES$|^BIBLIOGRAPHY$` (case-insensitive) at level 1
- `has_pages` — `len(pages/) == page_count_processed`
- `section_hierarchy_consistent` — AND of all six `hierarchy_checks` per §7.6

### Status derivation

- `fail` if any gate is `false` and `--fail-on-low-quality` was set
- `warn` if any gate is `false` or any anomaly is present
- `ok` otherwise

## 12. Caching behavior

When `--cache` is set:

1. Read `artifacts/run_manifest.json` if it exists.
2. Compute SHA-256 of the new input.
3. If the new SHA matches the manifest's `input_pdf_sha256` **and** the manifest's `stages_completed` includes `parse`, skip Stages 1–2 and recompute only Stage 2.5 onward.
4. Otherwise, run the full pipeline and overwrite.

Caching only saves the expensive step (Docling parse + rasterization). Normalization, sanity, and packet construction always re-run because they're cheap and we want consistency with current code.

## 13. Error handling

- **Stage failure mid-pipeline**: write whatever artifacts the stage produced before failing. Manifest's `stages_completed` reflects only fully-completed stages. Re-run without `--cache` to retry from scratch.
- **Docling crashes on a page**: catch, record `parse_error` in manifest with the page number and exception type, continue. The page contributes no text or layout.
- **Bbox crop outside page raster**: clip to page bounds. Record anomaly `bbox_clipped`.
- **JSON write failure**: bubble up as exit code 3. Do not produce partial files; write to `.tmp` and rename.

## 14. What this spec does not cover

- The README's "how to use the outputs in an AI workflow" — that's user guidance, not behavior.
- LLM integration — not in scope for this tool.
- A second parser backend — Protocol exists for it, but no concrete second parser is specified.
- Bibliography parsing beyond `raw` + `key` — best-effort, no contract.
- Cross-paper deduplication, citation graph construction, or any multi-paper feature — out of scope.

## 15. Test fixtures

A reference run on the Foffano 2023 paper (`assets/Foffano_et_al_-_2023_-_Conformal_Off-Policy_Evaluation_in_Markov_Decision_Processes.pdf`) is the primary fixture. Expected output snapshots live in `tests/fixtures/foffano/`. Stage 2.5 tests should assert:

- Title detected: "Conformal Off-Policy Evaluation in Markov Decision Processes"
- 7 level-1 numbered sections (I–VII) plus REFERENCES at level 1
- Letter sub-sections (A., B., C., ...) at level 2 under their Roman parents
- `Algorithm 1` not in `sections.json`
- Synthetic Abstract section present
- `section_hierarchy_consistent: true`

## 16. Future work

Items considered and deferred. Not commitments — the list is here so future-us doesn't re-litigate them from scratch.

### OCR for scanned PDFs

The `--ocr` CLI flag exists (§1) and defaults to `off`. The tool assumes native-text PDFs, which holds for modern academic papers from arXiv/IEEE/ACM/NeurIPS/etc. Users with a scanned PDF can flip `--ocr on` and pay the cost knowingly.

The future-work piece is **auto-detection** so users don't have to know:

- Before Stage 1's Docling parse, do a cheap PyMuPDF text-layer check: sum `page.get_text("text")` lengths and divide by page count.
- If `chars_per_page < 100`, the PDF has no usable text layer; override `--ocr off` to `on` and proceed. Record the override in the manifest.
- Quality report adds an `ocr_enabled` field and an `ocr_auto_detected: true` field for visibility.

Why not now: we have no test corpus of scanned papers and no reason to ship auto-detect logic that might misfire on edge cases. The flag is sufficient for the experimental cases this tool will encounter. Add auto-detect when there's a concrete paper that needs it.

### Second parser backend

The `Parser` Protocol (§9) exists for this. No concrete second parser is specified. MinerU was considered and dropped (license + maintenance cost). If Docling regresses or a better parser arrives, add it as `scripts/parsers/<name>_parser.py` and a CLI flag.

### Per-block confidence propagation

Docling exposes some per-block confidence but inconsistently. If it becomes reliable, propagate into `quality_report` and into `provenance.json` as a per-block `confidence` field. Until then, no contract.

### Bibliography parsing

Currently `raw` + `key` only, with structured fields populated only when Docling provides them. A real BibTeX/RIS-quality parser is out of scope for this tool; if needed, the `references.json` `raw` field is the input to a downstream parser.

### Author detection

Same story as bibliography: Docling's metadata if present, otherwise null. No heuristic parsing of author lines on the first page.
