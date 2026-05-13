from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import ensure_dir, read_json, write_json


HEADING_RE = re.compile(r"^([A-Z][A-Za-z0-9\s\-:]{3,80}|\d+(\.\d+)*\s+.+)$")


def split_sections(text: str) -> list[dict]:
    sections: list[dict] = []
    current = {"id": "sec-000", "heading": "Document", "content": []}

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            current["content"].append(line)
            continue

        if HEADING_RE.match(stripped) and len(stripped.split()) <= 12:
            if current["content"]:
                sections.append({
                    "id": current["id"],
                    "heading": current["heading"],
                    "text": "\n".join(current["content"]).strip(),
                })
            current = {
                "id": f"sec-{len(sections)+1:03d}",
                "heading": stripped,
                "content": [],
            }
        else:
            current["content"].append(line)

    if current["content"]:
        sections.append({
            "id": current["id"],
            "heading": current["heading"],
            "text": "\n".join(current["content"]).strip(),
        })
    return sections


def consolidate_text(out_dir: Path) -> None:
    artifacts = out_dir / "artifacts"
    text_dir = ensure_dir(artifacts / "text")
    quality_dir = ensure_dir(artifacts / "quality")

    raw_text_path = text_dir / "raw_text.txt"
    raw_text = raw_text_path.read_text(encoding="utf-8") if raw_text_path.exists() else ""

    # Scaffold policy: canonical plaintext starts from raw_text; later replace with fusion engine.
    canonical = raw_text.strip()
    (text_dir / "plaintext.txt").write_text(canonical + "\n", encoding="utf-8")

    sections = split_sections(canonical)
    write_json(text_dir / "sections.json", sections)

    raw_dict = read_json(text_dir / "raw_dict.json") if (text_dir / "raw_dict.json").exists() else []
    provenance = {
        "source": "scaffold-v0",
        "policy": "canonical derived from raw_text; upgrade to multi-extractor fusion in v1",
        "page_count": len(raw_dict),
    }
    write_json(text_dir / "provenance.json", provenance)

    low_confidence_markers = canonical.count("[LOW_CONFIDENCE]")
    quality = {
        "status": "warn" if not canonical else "ok",
        "canonical_char_count": len(canonical),
        "section_count": len(sections),
        "low_confidence_markers": low_confidence_markers,
        "notes": [
            "Scaffold quality model only.",
            "Implement geometric read-order + extractor voting for production.",
        ],
    }
    write_json(quality_dir / "quality_report.json", quality)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    consolidate_text(args.out)


if __name__ == "__main__":
    main()
