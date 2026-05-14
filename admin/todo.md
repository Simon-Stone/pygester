# TODO

Concrete next steps, ordered by what unblocks what. Based on the gap between current outputs and what the spec says they should be.

## Critical — math handling is broken

### 1. Enable Docling formula enrichment

**Symptom:** `plaintext.txt` contains `V π H ( x ) = E π [ ∑ H t =1 r t | x 1 = x ]` instead of `$V_H^\pi(x) = \mathbb{E}_\pi[\sum_{t=1}^H r_t | x_1 = x]$`. Zero `$` characters in the entire file.

**Cause:** `do_formula_enrichment` is not being set on Docling's `pipeline_options`. The current manifest shows `"config": {"do_ocr": false}` — that's the whole config.

**Fix:** in `src/parsers/docling_parser.py`, set:

```python
pipeline_options.do_formula_enrichment = True
```

**Verify:** re-run on Foffano, then:

```bash
grep -c '\$' run-foffano/artifacts/text/plaintext.txt
grep -c '\$' run-foffano/artifacts/parser/raw_output.md
```

Both should return > 0. Eyeball a few equations in `plaintext.txt` to confirm the LaTeX looks roughly right.

**Why it matters:** without this, math is degraded to unreadable Unicode soup. An LLM can't translate it, a human can't read it, and the equation PNGs become the only viable source of math content.

### 2. Wire up `artifacts/equations/`

**Symptom:** `context_packet.json` has no `equations` field. The directory `artifacts/equations/` doesn't appear in the run tree.

**Spec ref:** §6.7 of `spec.md`.

**Action:**
- In `normalize.py`, iterate Docling `formula` blocks at display scale
- Crop each from the corresponding page PNG using the bbox
- Write `equation_NNN.png` and append entry to `equations.json` with `id`, `page`, `bbox`, `latex`, `image_path`, `number`
- Include the array in `context_packet.json`

**Why it matters:** even with formula enrichment on, some equations come out with broken LaTeX (mismatched braces, missing subscripts on complex displays). The PNG is the unambiguous fallback. For math-to-code workflows this is the most important artifact in the tool.

### 3. Wire up `artifacts/algorithms/`

Same shape as equations, for pseudocode blocks. Spec §6.6.

The sanity pass is already correctly demoting `Algorithm 1` from sections (good). But the algorithm block content needs to be preserved as a first-class artifact, not just stripped. Crop the page region, save the PNG, capture the `raw_text`.

## Critical — `paper.md` is still scaffold

### 4. Generate real `paper.md`

**Symptom:** `outputs/paper.md` currently says "# Summary (Scaffold)" and dumps the first 3000 chars of plaintext in a code fence. This is leftover from the killed summary generator.

**Spec ref:** §8.2.

**Action:**
- Delete `src/generate_summary.py` and `src/generate_translation.py`
- Add `src/render_markdown.py` (or fold into `build_context_packet.py`)
- Render `outputs/paper.md` from `plaintext.txt` + `sections.json`:
  - YAML frontmatter with title, authors, source SHA, parser version, tool version
  - Section headings as `#`/`##`/`###` based on `level`
  - Body text preserved
  - LaTeX math inline (`$...$` or `$$...$$`) — comes free once #1 lands
  - Figure references: `![caption](../artifacts/figures/figure_NNN.png)`
  - Algorithm references: fenced code block with `raw_text` + image link
  - Tables: rendered inline as markdown if ≤50 rows, else linked

**Verify:** open `paper.md` in a markdown renderer with LaTeX support. Should look like a clean version of the paper.

### 5. Remove `translation.md`

The scope-narrowing decisions killed translation as a built-in mode. `outputs/translation.md` shouldn't exist. Either delete the generator or short-circuit it.

## Cleanup — already-agreed deletions

These are leftover from previous iterations and should go:

- `src/parsers/mineru_parser.py` (MinerU dropped)
- `src/extract_artifacts.py` (superseded by `parse_pdf.py`)
- `src/consolidate_text.py` (superseded by `normalize.py`)
- `src/enrich_structures.py` (superseded by `normalize.py` + sanity pass)
- `src/generate_summary.py` (no LLM in scope)
- `src/generate_translation.py` (no LLM in scope)
- `SKILL.md` (this is a tool, not a Claude skill)
- All `__pycache__` directories (gitignore them)

## Quality — artifacts that aren't being populated

### 6. Figures

`context_packet.json` reports `"figures": []`. The Foffano paper has 4 figures. Either Docling isn't extracting them or `normalize.py` isn't reading them out. Worth checking `raw_output.json` for picture blocks and tracing through.

### 7. Tables

`tables.json` is `{"items": []}` — for this paper that's actually correct (no `<table>`-shaped tables, only figures and algorithms). But the empty list should be distinguished from "not yet implemented." Add a `status: "no_tables_found"` or similar so a consumer knows the difference.

### 8. References

`references.json` isn't populated. Foffano has 33 references. Even a `raw` + `key` extraction (no structured parsing) would be useful.

## Documentation

### 9. Sync README and spec to actual behavior

Once the above lands, both files need a pass:
- README's "what you get" list should match real outputs
- Spec's §6 schemas should match what's actually written

This is a small edit, but worth doing **after** the code is fixed so the docs describe what is, not what should be.

## Out of scope for this pass

Things that came up but aren't on this list:

- **OCR** — already in `spec.md` §16 as future work
- **`outputs/paper.txt`** — discussed as a nice-to-have; skip until paper.md is real
- **`outputs/README.md` in the bundle** — same
- **`--pages M-N` flag** — same
- **Token count estimate** — same
- **Citation graph / cross-paper features** — explicitly out of scope

## Ordering

If working solo, do them in this order:

1. Enable formula enrichment (#1) — five minutes, unblocks everything math
2. Real `paper.md` (#4) — biggest user-facing improvement
3. Equations artifact (#2) — math safety net
4. Algorithms artifact (#3) — needed for the math-to-code use case
5. Cleanup leftover files (Cleanup section) — quick wins, reduces confusion
6. Figures, tables, references (#6, #7, #8) — round out the bundle
7. Docs sync (#9) — last, after the code is stable

Steps 1 and 4 are the only ones that change user-visible behavior in a meaningful way. The rest is plumbing.
