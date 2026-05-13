from __future__ import annotations

import argparse
from pathlib import Path

from common import ensure_dir, read_json, write_json


def build_context_packet(out_dir: Path) -> None:
    artifacts = out_dir / "artifacts"
    outputs_dir = ensure_dir(out_dir / "outputs")

    manifest = read_json(artifacts / "run_manifest.json") if (artifacts / "run_manifest.json").exists() else {}
    quality = read_json(artifacts / "quality" / "quality_report.json") if (artifacts / "quality" / "quality_report.json").exists() else {}
    sections = read_json(artifacts / "text" / "sections.json") if (artifacts / "text" / "sections.json").exists() else []
    figures = read_json(artifacts / "figures" / "figures.json") if (artifacts / "figures" / "figures.json").exists() else []
    tables = read_json(artifacts / "tables" / "tables.json") if (artifacts / "tables" / "tables.json").exists() else []

    profile = quality.get("paper_profile", {})

    packet = {
        "paper_profile": {
            "title": profile.get("title"),
            "authors": profile.get("authors"),
            "input_pdf_sha256": manifest.get("input_pdf_sha256"),
            "page_count": manifest.get("page_count_processed"),
            "parser": manifest.get("parser", {}),
            "tool_version": manifest.get("skill_version"),
        },
        "canonical_text": {
            "path": "artifacts/text/plaintext.txt",
        },
        "sections": [
            {
                "id": s.get("id"),
                "heading": s.get("heading"),
                "level": s.get("level"),
                "start_char": s.get("start_char"),
                "end_char": s.get("end_char"),
            }
            for s in sections
        ],
        "figures": figures,
        "tables": tables,
        "uncertainties": {
            "quality_status": quality.get("status"),
            "failures": quality.get("failures", []),
            "notes": quality.get("notes", []),
        },
        "evidence_index": {
            "original_pdf": "artifacts/original.pdf",
            "pages_dir": "artifacts/pages/",
            "parser_raw_json": "artifacts/parser/raw_output.json",
        },
    }

    write_json(outputs_dir / "context_packet.json", packet)


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 3: build context packet")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    build_context_packet(args.out)


if __name__ == "__main__":
    main()
