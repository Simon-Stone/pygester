from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import ensure_dir, read_json, write_json

LIGATURES = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
}


def _strip_markdown(md: str) -> str:
    text = re.sub(r"```.*?```", "", md, flags=re.DOTALL)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text


def _normalize_text(text: str) -> str:
    for k, v in LIGATURES.items():
        text = text.replace(k, v)
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def _sections_from_markdown(md: str, plain: str) -> list[dict]:
    lines = md.splitlines()
    sections: list[dict] = []
    pos = 0

    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not m:
            continue
        level = len(m.group(1))
        heading = m.group(2).strip()
        start = plain.find(heading, pos)
        if start < 0:
            start = pos
        sections.append(
            {
                "id": f"sec-{len(sections)+1:03d}",
                "heading": heading,
                "level": level,
                "start_char": start,
                "end_char": None,
            }
        )
        pos = start

    for i in range(len(sections)):
        if i + 1 < len(sections):
            sections[i]["end_char"] = sections[i + 1]["start_char"]
        else:
            sections[i]["end_char"] = len(plain)

    if not sections:
        sections = [
            {
                "id": "sec-000",
                "heading": "Document",
                "level": 1,
                "start_char": 0,
                "end_char": len(plain),
            }
        ]
    return sections


def normalize(out_dir: Path) -> None:
    artifacts = out_dir / "artifacts"
    parser_dir = artifacts / "parser"

    text_dir = ensure_dir(artifacts / "text")
    figures_dir = ensure_dir(artifacts / "figures")
    tables_dir = ensure_dir(artifacts / "tables")
    refs_dir = ensure_dir(artifacts / "references")
    quality_dir = ensure_dir(artifacts / "quality")

    md_path = parser_dir / "raw_output.md"
    raw_md = md_path.read_text(encoding="utf-8") if md_path.exists() else ""

    plain = _normalize_text(_strip_markdown(raw_md)) if raw_md else ""
    (text_dir / "plaintext.txt").write_text(plain, encoding="utf-8")

    sections = _sections_from_markdown(raw_md, plain)
    write_json(text_dir / "sections.json", sections)

    provenance = {
        "status": "partial",
        "notes": [
            "Char-range provenance scaffolded.",
            "Wire parser-native span/page mapping in next phase.",
        ],
        "spans": [
            {
                "start_char": 0,
                "end_char": len(plain),
                "page": None,
                "bbox": None,
                "source_block_id": None,
            }
        ],
    }
    write_json(text_dir / "provenance.json", provenance)

    write_json(figures_dir / "figures.json", [])
    write_json(tables_dir / "tables.json", [])
    write_json(refs_dir / "references.json", [])

    manifest = read_json(artifacts / "run_manifest.json") if (artifacts / "run_manifest.json").exists() else {}
    expected_pages = manifest.get("page_count_processed", 0)
    actual_pages = len(list((artifacts / "pages").glob("page_*.png")))

    gates = {
        "canonical_non_empty": len(plain.strip()) > 0,
        "raster_page_count_ok": expected_pages == actual_pages,
        "has_abstract": False,
        "has_references": False,
        "section_hierarchy_consistent": False,
    }
    failures = [k for k, ok in gates.items() if not ok and k not in {"has_abstract", "has_references", "section_hierarchy_consistent"}]

    quality = {
        "status": "ok" if not failures else "warn",
        "canonical_char_count": len(plain),
        "section_count": len(sections),
        "gates": gates,
        "failures": failures,
        "section_sanity_anomalies": [],
        "paper_profile": {"title": None, "authors": None},
        "notes": [
            "Docling-backed parse; normalize stage currently conservative.",
            "Stage 2.5 assigns hierarchy, abstract, references gates.",
        ],
    }
    write_json(quality_dir / "quality_report.json", quality)


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 2: normalize parser output")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    normalize(args.out)


if __name__ == "__main__":
    main()
