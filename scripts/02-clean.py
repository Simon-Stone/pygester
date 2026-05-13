"""Stage 02: Clean Docling output → paper.md + structured sidecars."""
from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

from common import read_json, write_json

SKILL_VERSION = "0.1.0"


def normalize_text(text: str) -> str:
    """Normalize ligatures and preserve special characters."""
    # Ligature normalization
    text = text.replace("ﬁ", "fi")
    text = text.replace("ﬂ", "fl")
    text = text.replace("ﬀ", "ff")
    text = text.replace("ﬃ", "ffi")
    text = text.replace("ﬄ", "ffl")

    # Rejoin hyphenated line breaks
    def rejoin_hyphen(match):
        word = match.group(1)
        next_word = match.group(2)
        if next_word[0].islower():
            return word + next_word
        return match.group(0)

    text = re.sub(r'(\w+)-\n([a-zA-Z])', rejoin_hyphen, text)

    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def add_frontmatter(markdown: str, manifest: dict) -> str:
    """Prepend YAML frontmatter."""
    flags = manifest.get("flags", {})
    formula = "LaTeX" if flags.get("formula_enrichment") == "on" else "Unicode soup"

    frontmatter = f"""---
title: Docling Extract
source_sha256: {manifest.get("input_pdf_sha256", "")}
parser: {manifest.get("parser", {}).get("name", "docling")} {manifest.get("parser", {}).get("version", "")}
tool_version: {SKILL_VERSION}
run_at: {manifest.get("timestamp_utc", "")}
formula_enrichment: {flags.get("formula_enrichment", "off")}
code_enrichment: {flags.get("code_enrichment", "off")}
ocr: {flags.get("ocr", "off")}
---

"""
    return frontmatter + markdown


def extract_sections(parser_md: Path) -> list[dict]:
    """Extract section info from parser markdown."""
    # Simple heuristic: lines starting with # are sections
    sections = []
    content = parser_md.read_text(encoding="utf-8")
    lines = content.split("\n")

    current_section = None
    char_offset = 0

    for i, line in enumerate(lines):
        if line.startswith("#"):
            if current_section:
                current_section["end_char"] = char_offset
            level = len(line) - len(line.lstrip("#"))
            heading = line.lstrip("#").strip()
            current_section = {
                "id": f"sec-{len(sections)+1:03d}",
                "heading": heading,
                "level": max(1, level),
                "start_char": char_offset,
                "end_char": 0,  # Will be filled by next section
            }
            sections.append(current_section)
        char_offset += len(line) + 1  # +1 for newline

    if sections:
        sections[-1]["end_char"] = char_offset

    return sections


def extract_figures(parser_json: Path, pages_dir: Path) -> list[dict]:
    """Extract figure info from parser JSON."""
    # Placeholder: Docling's structure varies, extract what we can
    data = read_json(parser_json)
    figures = []

    # Look for picture blocks in the document structure
    # This is a simplified extraction - real implementation would traverse DoclingDocument
    if isinstance(data, dict):
        # Docling exports to dict with 'body' or 'sections'
        pass  # Placeholder for actual extraction logic

    return figures


def extract_tables(parser_json: Path) -> list[dict]:
    """Extract table info from parser JSON."""
    data = read_json(parser_json)
    tables = []

    # Placeholder: actual extraction would parse Docling table blocks
    return tables


def extract_equations(parser_json: Path) -> list[dict]:
    """Extract equation info from parser JSON."""
    data = read_json(parser_json)
    equations = []

    # Placeholder: actual extraction would parse Docling formula blocks
    return equations


def extract_references(parser_json: Path) -> list[dict]:
    """Extract reference info from parser JSON."""
    data = read_json(parser_json)
    references = []

    # Placeholder: actual extraction would parse Docling reference blocks
    return references


def write_quality_report(out_dir: Path, manifest: dict, sections: list, figures: list, tables: list, equations: list, references: list) -> None:
    """Write quality report."""
    pages_dir = out_dir / "pages"
    page_count = len(list(pages_dir.glob("page_*.png"))) if pages_dir.exists() else 0

    gates = {
        "canonical_non_empty": True,  # Will be set based on actual content
        "has_references_section": len(references) > 0,
        "raster_page_count_ok": page_count == manifest.get("page_count", 0),
        "paper_md_exists": True,  # Will be set after writing
        "context_packet_valid": True,
    }

    report = {
        "schema_version": "1",
        "status": "ok" if all(gates.values()) else "warn",
        "gates": gates,
        "section_count": len(sections),
        "figure_count": len(figures),
        "table_count": len(tables),
        "equation_count": len(equations),
        "reference_count": len(references),
    }

    write_json(out_dir / "quality-report.json", report)


def clean(out_dir: Path) -> None:
    """Run Stage 02: clean and produce artifacts."""
    debug = out_dir / "debug"
    parser_dir = debug / "parser"

    # Read manifest
    manifest = read_json(debug / "run-manifest.json")

    # Read parser markdown
    parser_md = parser_dir / "raw_output.md"
    markdown = parser_md.read_text(encoding="utf-8")

    # Normalize text
    normalized = normalize_text(markdown)

    # Add frontmatter
    with_frontmatter = add_frontmatter(normalized, manifest)

    # Write intermediate
    markdown_dir = ensure_dir(debug / "markdown")
    (markdown_dir / "01-with-frontmatter.md").write_text(with_frontmatter, encoding="utf-8")

    # Copy to final output
    (out_dir / "paper.md").write_text(with_frontmatter, encoding="utf-8")

    # Extract structured data
    sections = extract_sections(parser_md)
    figures = extract_figures(parser_dir / "raw_output.json", out_dir / "pages")
    tables = extract_tables(parser_dir / "raw_output.json")
    equations = extract_equations(parser_dir / "raw_output.json")
    references = extract_references(parser_dir / "raw_output.json")

    # Write sidecars (nested per spec)
    text_dir = ensure_dir(debug / "text")
    write_json(text_dir / "sections.json", sections)
    write_json(text_dir / "provenance.json", [])  # Placeholder

    figures_dir = ensure_dir(debug / "figures")
    write_json(figures_dir / "figures.json", figures)

    tables_dir = ensure_dir(debug / "tables")
    write_json(tables_dir / "tables.json", tables)

    equations_dir = ensure_dir(debug / "equations")
    write_json(equations_dir / "equations.json", equations)

    references_dir = ensure_dir(debug / "references")
    write_json(references_dir / "references.json", references)

    # Update manifest
    manifest["stages_completed"] = ["01-parse", "02-clean"]
    write_json(debug / "run-manifest.json", manifest)

    # Write quality report
    write_quality_report(out_dir, manifest, sections, figures, tables, equations, references)

    # Write plaintext.txt (canonical text)
    text_dir = ensure_dir(debug / "text")
    (text_dir / "plaintext.txt").write_text(normalized, encoding="utf-8")

    print("Stage 02 complete: paper.md and sidecars produced")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 02: Clean output")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    clean(args.out)


if __name__ == "__main__":
    main()
