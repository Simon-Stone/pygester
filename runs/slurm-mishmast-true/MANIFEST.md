# Run manifest

This directory contains the output of `digest-technical-paper` processing
`assets/Mishmast Nehi et al. - 2020 - Solving methods for interval linear programming problem a review and an improved method.pdf`.

Tool version: `0.1.0` · Run at: `2026-05-14T22:39:17.372860+00:00` · Flags: `--formula-enrichment true --code-enrichment false --ocr false`

## What's in here

### Deliverables (the things you probably want)

- **`paper.md`** — the paper as cleaned markdown. Section structure preserved.
  Math is LaTeX depending on whether formula enrichment was on.
- **`context-packet.json`** — structured metadata: sections with page ranges,
  figures, tables, equations, references. The thing to paste alongside `paper.md`
  when an LLM needs to know what's on each page.
- **`pages/page_NNNN.png`** — one rasterized image per page (25 total).
  Use these when you want to show an LLM what a figure or equation actually looks like.
- **`visuals/`** — per-block crops: `equations/`, `figures/`, `code/`. Each has
  a JSON manifest plus PNG crops. Visual ground truth for verification.
- **`tables/`** — extracted tables as JSON (if any found).
- **`references/`** — extracted references as JSON (if any found).
- **`quality-report.json`** — quick summary of what's populated and what failed.
  Glance at this if `paper.md` looks weird.

### Debug

Everything under `debug/` is plumbing — intermediate artifacts that exist so a
future debugger can trace what each stage did. You can ignore these unless
something's wrong.

- `debug/original.pdf` — the input, copied here so the run is self-contained.
- `debug/run-manifest.json` — full config: every flag, parser version, hashes,
  per-stage timing.
- `debug/parser/raw_output.{json,md}` — what Docling produced before our post-
  processing. Compare against `paper.md` to see what Stage 02 changed.
- `debug/text/plaintext.txt` — canonical text without markdown formatting.
- `debug/text/sections.json` — section tree (already in context-packet).
- `debug/text/provenance.json` — char-offset → page/bbox map.
- `debug/markdown/` — intermediate snapshots from Stage 02 post-processing.
- `debug/{figures,tables,equations,references}/` — structured artifacts
  that get rolled into `context-packet.json`.

## What was done to your paper

- Docling version: `2.93.0`
- Formula enrichment: `true` — math came through as LaTeX
- Code enrichment: `false` — code blocks raw text
- OCR: `false` — skipped; PDF had usable text layer
- Pages processed: 25
- Sections detected: 20
- Figures detected: 30
- Tables detected: 2
- Equations detected: 37

## Quality gates

- **canonical_non_empty**: ✓
- **has_references_section**: ✓
- **raster_page_count_ok**: ✓
- **paper_md_exists**: ✓
- **context_packet_valid**: ✓

## Reproducing this run

```bash
python src/01-parse.py "assets/Mishmast Nehi et al. - 2020 - Solving methods for interval linear programming problem a review and an improved method.pdf" --out <OUT_DIR> --formula-enrichment true --code-enrichment false --ocr false
python src/02-clean.py --out <OUT_DIR>
python src/03-packet.py --out <OUT_DIR>
```
